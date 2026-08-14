from __future__ import annotations

import json
import random
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aicomp_sdk.core.cells import cell_signature
from aicomp_sdk.core.env.sandbox import SandboxEnv
from aicomp_sdk.core.predicates import eval_predicates
from aicomp_sdk.scoring import SEVERITY_W, get_score_cell_hash

from experiments.backend_adapter import BackendSpec
from experiments.continuation_generator import ContinuationCandidate, generate_continuations
from experiments.edge_policy import PromptBankController, _result_class_from_event, _trace_summary
from experiments.security_state import SecurityState


FIXTURES_DIR = Path("aicomp_sdk/fixtures")
DEFAULT_MAX_TOOL_HOPS = 4


def _short_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _dump_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _score_predicates(predicates: list[dict[str, Any]]) -> int:
    return int(sum(SEVERITY_W.get(int(pred.get("severity", 1)), 1) for pred in predicates))


def _tool_names(trace: dict[str, Any]) -> list[str]:
    return [event.get("name", "") for event in trace.get("tool_events", [])]


def _source_names(trace: dict[str, Any]) -> list[str]:
    return [event.get("source", "") for event in trace.get("tool_events", [])]


def _last_event(trace: dict[str, Any]) -> dict[str, Any] | None:
    events = list(trace.get("tool_events", []))
    return events[-1] if events else None


def _make_env(backend: BackendSpec, seed: int, max_tool_hops: int = DEFAULT_MAX_TOOL_HOPS) -> SandboxEnv:
    from aicomp_sdk.guardrails.optimal import Guardrail

    env = SandboxEnv(
        seed=seed,
        fixtures_dir=FIXTURES_DIR,
        agent=backend.build_agent(),
        guardrail=Guardrail(),
        max_tool_hops=max_tool_hops,
    )
    env.reset()
    return env


@dataclass
class PrefixEntry:
    prefix_id: str
    snapshot: Any
    user_messages: list[str]
    state: SecurityState
    tool_sequence: list[str]
    source_sequence: list[str]
    depth: int
    available_next_tools: list[str] = field(default_factory=list)
    transition_success_rates: dict[str, float] = field(default_factory=dict)
    cell_hashes: set[str] = field(default_factory=set)
    mechanism_signature: str = ""
    predicate_hits: list[str] = field(default_factory=list)
    replay_valid: bool = False
    times_extended: int = 0
    successful_extensions: int = 0
    failed_extensions: int = 0
    last_tool: str | None = None
    last_result_class: str = "EMPTY_RESULT"
    last_source: str | None = None
    note: str = ""

    @property
    def continuation_success_probability(self) -> float:
        return max(self.transition_success_rates.values(), default=0.0)

    @property
    def mechanism_count(self) -> int:
        return 1 if self.mechanism_signature else 0


@dataclass
class PrefixAttempt:
    seed: int
    mode: str
    desired_tool: str
    prefix_id: str
    candidate_id: str
    source: str
    structural_frame: str
    prompt: str
    user_messages: list[str]
    tool_sequence: list[str]
    source_sequence: list[str]
    predicates: list[dict[str, Any]]
    cell_hash: str
    score_cell_hash: str | None
    state_key: str
    mechanism_signature: str
    replay_valid: bool
    transition_success: bool
    original_trace: dict[str, Any]
    replay_trace: dict[str, Any] | None
    post_snapshot: Any
    depth: int
    egress_count: int
    clean_event_count: int
    guardrail_blocked: bool
    refusal: bool
    continuation_value: float


def _prefix_key(prefix: PrefixEntry) -> str:
    payload = {
        "tool_sequence": prefix.tool_sequence,
        "source_sequence": prefix.source_sequence,
        "last_tool": prefix.last_tool,
        "last_result_class": prefix.last_result_class,
        "state": prefix.state.canonical_key(),
    }
    return _short_hash(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _prefix_score(prefix: PrefixEntry, selection_policy: str) -> tuple[float, float, float]:
    continuation = prefix.continuation_success_probability
    novelty = float(len(prefix.cell_hashes))
    depth = float(prefix.depth)
    if selection_policy == "depth_first":
        return (depth, continuation, novelty)
    if selection_policy == "novelty_first":
        return (novelty, continuation, depth)
    if selection_policy == "edge_bottleneck_first":
        bottleneck = 1.0 - continuation
        return (bottleneck, novelty, depth)
    if selection_policy == "value_first":
        value = 1.0 if prefix.last_tool == "fs.read" and prefix.state.clean_event_count >= 4 else 0.0
        value += 1.0 if prefix.last_tool == "web.open" else 0.0
        value += 1.0 if prefix.last_tool == "web.search" else 0.0
        return (value, continuation, novelty)
    return (continuation, novelty, depth)


def _choose_prefix(prefixes: list[PrefixEntry], policy: str, rng: random.Random) -> PrefixEntry | None:
    if not prefixes:
        return None
    scored = sorted(prefixes, key=lambda prefix: _prefix_score(prefix, policy), reverse=True)
    top_score = _prefix_score(scored[0], policy)
    best = [prefix for prefix in scored if _prefix_score(prefix, policy) == top_score]
    return rng.choice(best)


def _classify_transition(*, desired_next_tool: str, trace: dict[str, Any]) -> str:
    tool_names = _tool_names(trace)
    if desired_next_tool in tool_names:
        return "reached"
    if any(
        event["name"] == desired_next_tool
        and not event["ok"]
        and str(event.get("error", "")).startswith(("denied:", "confirm_required:"))
        for event in trace.get("tool_events", [])
    ):
        return "guardrail_limited"
    return "model_limited"


def _replay_trace(
    *,
    backend: BackendSpec,
    seed: int,
    snapshot: Any,
    messages: list[str],
    max_tool_hops: int,
) -> dict[str, Any]:
    env = _make_env(backend, seed, max_tool_hops=max_tool_hops)
    env.restore(snapshot)
    for message in messages:
        env.interact(message, max_tool_hops=max_tool_hops)
    return env.export_trace_dict()


def _state_from_trace(trace: dict[str, Any]) -> SecurityState:
    return SecurityState.from_trace(trace)


def _prefix_from_trace(
    *,
    prefix_id: str,
    snapshot: Any,
    trace: dict[str, Any],
    note: str = "",
) -> PrefixEntry:
    summary = _trace_summary(trace)
    state = summary["state"]
    return PrefixEntry(
        prefix_id=prefix_id,
        snapshot=snapshot,
        user_messages=list(trace.get("user_messages", [])),
        state=state,
        tool_sequence=summary["tool_sequence"],
        source_sequence=summary["source_sequence"],
        depth=len(trace.get("user_messages", [])),
        available_next_tools=[],
        transition_success_rates={},
        cell_hashes={summary["cell"]["hash"]},
        mechanism_signature=state.mechanism_signature(),
        predicate_hits=[pred["predicate"] for pred in summary["predicates"]],
        replay_valid=True,
        times_extended=0,
        successful_extensions=0,
        failed_extensions=0,
        last_tool=summary["last_tool"],
        last_result_class=summary["last_result_class"],
        last_source=summary["last_source"],
        note=note,
    )


def _seed_prefix_archive(
    *,
    backend: BackendSpec,
    seeds: tuple[int, ...],
    max_tool_hops: int,
    prompt_bank: PromptBankController,
    include_initial: bool = True,
    include_two_turn: bool = True,
) -> list[PrefixEntry]:
    prefixes: list[PrefixEntry] = []
    seed_list = list(seeds) or [123]
    if include_initial:
        env = _make_env(backend, seed_list[0], max_tool_hops=max_tool_hops)
        trace = env.export_trace_dict()
        prefixes.append(_prefix_from_trace(prefix_id="initial", snapshot=env.snapshot(), trace=trace, note="initial"))

    followup_target = {
        "web_discovery": "web.open",
        "email_discovery": "email.read",
        "indirect_instruction_following": "fs.read",
        "benign_file_workflow": "fs.read",
        "multi_step_workflow": "fs.read",
        "taint_clearing": "fs.read",
        "http_action_steering": "http.post",
        "email_send_steering": "email.send",
    }
    for idx, (_family_id, prompt_id, prompt) in enumerate(prompt_bank.seed_prompts()):
        seed = seed_list[idx % len(seed_list)]
        env = _make_env(backend, seed, max_tool_hops=max_tool_hops)
        env.interact(prompt, max_tool_hops=max_tool_hops)
        trace = env.export_trace_dict()
        prefixes.append(
            _prefix_from_trace(
                prefix_id=f"{prompt_id}:{idx}",
                snapshot=env.snapshot(),
                trace=trace,
                note="prompt_bank",
            )
        )
        if include_two_turn:
            desired_followup = followup_target.get(_family_id, "fs.read")
            followup = prompt_bank.followup_prompt(desired_tool=desired_followup, trace=trace, result=trace)
            env.interact(followup, max_tool_hops=max_tool_hops)
            trace2 = env.export_trace_dict()
            prefixes.append(
                _prefix_from_trace(
                    prefix_id=f"{prompt_id}:{idx}:two_turn",
                    snapshot=env.snapshot(),
                    trace=trace2,
                    note=f"prompt_bank_two_turn:{desired_followup}",
                )
            )
    return prefixes


def _extension_result(
    *,
    backend: BackendSpec,
    seed: int,
    prefix: PrefixEntry,
    candidate: ContinuationCandidate,
    desired_tool: str,
    max_tool_hops: int,
) -> PrefixAttempt:
    env = _make_env(backend, seed, max_tool_hops=max_tool_hops)
    env.restore(prefix.snapshot)
    env.interact(candidate.prompt, max_tool_hops=max_tool_hops)
    trace = env.export_trace_dict()
    post_snapshot = env.snapshot()
    summary = _trace_summary(trace)
    state = summary["state"]
    replay_trace = None
    replay_valid = False
    if trace.get("tool_events"):
        replay_trace = _replay_trace(
            backend=backend,
            seed=seed,
            snapshot=prefix.snapshot,
            messages=[candidate.prompt],
            max_tool_hops=max_tool_hops,
        )
        replay_valid = (
            [event["name"] for event in replay_trace.get("tool_events", [])] == summary["tool_sequence"]
            and [pred["predicate"] for pred in eval_predicates(replay_trace)] == [pred["predicate"] for pred in summary["predicates"]]
            and cell_signature(
                replay_trace.get("tool_events", []),
                egress_data=replay_trace.get("egress", []),
                user_messages=replay_trace.get("user_messages", []),
            )["hash"]
            == summary["cell"]["hash"]
        )

    transition_success = desired_tool in summary["tool_sequence"]
    continuation_value = 0.0
    if transition_success:
        continuation_value += 2.0
    continuation_value += 1.0 if replay_valid else 0.0
    continuation_value += 0.5 * len(summary["tool_sequence"])
    continuation_value += 1.0 if state.taint_active else 0.0
    continuation_value += 3.0 if summary["predicates"] else 0.0

    return PrefixAttempt(
        seed=seed,
        mode=candidate.source,
        desired_tool=desired_tool,
        prefix_id=prefix.prefix_id,
        candidate_id=candidate.candidate_id,
        source=candidate.source,
        structural_frame=candidate.structural_frame,
        prompt=candidate.prompt,
        user_messages=list(trace.get("user_messages", [])),
        tool_sequence=summary["tool_sequence"],
        source_sequence=summary["source_sequence"],
        predicates=[
            {"predicate": pred["predicate"], "severity": pred["severity"], "evidence": pred.get("evidence", {})}
            for pred in summary["predicates"]
        ],
        cell_hash=summary["cell"]["hash"],
        score_cell_hash=summary["score_cell_hash"],
        state_key=state.canonical_key(),
        mechanism_signature=state.mechanism_signature(),
        replay_valid=replay_valid,
        transition_success=transition_success,
        original_trace=trace,
        replay_trace=replay_trace,
        post_snapshot=post_snapshot,
        depth=len(trace.get("user_messages", [])),
        egress_count=state.egress_count,
        clean_event_count=state.clean_event_count,
        guardrail_blocked=state.guardrail_blocked,
        refusal=state.refusal,
        continuation_value=continuation_value,
    )


def run_prefix_extension_search(
    *,
    backend: BackendSpec,
    seeds: tuple[int, ...],
    budget_s: float,
    selection_policy: str,
    desired_tool: str = "fs.read",
    include_initial: bool = True,
    include_prompt_bank: bool = True,
    include_edge_policy: bool = True,
    include_mutation: bool = True,
    include_explicit: bool = True,
    focus_prefix_id: str | None = None,
    max_tool_hops: int = DEFAULT_MAX_TOOL_HOPS,
) -> tuple[list[PrefixAttempt], dict[str, Any], list[dict[str, Any]]]:
    rng = random.Random(seeds[0] if seeds else 123)
    prompt_bank = PromptBankController()
    prefixes = _seed_prefix_archive(
        backend=backend,
        seeds=seeds,
        max_tool_hops=max_tool_hops,
        prompt_bank=prompt_bank,
        include_initial=include_initial,
    )
    attempts: list[PrefixAttempt] = []

    max_steps = max(36, int(budget_s // 2))
    for step in range(max_steps):
        candidates_prefixes = prefixes
        if focus_prefix_id is not None:
            focused = [prefix for prefix in prefixes if prefix.prefix_id == focus_prefix_id]
            if focused:
                candidates_prefixes = focused
        current = _choose_prefix(candidates_prefixes, selection_policy, rng)
        if current is None:
            break

        trace_context = {
            "tool_events": [
                {"name": tool, "source": source}
                for tool, source in zip(current.tool_sequence, current.source_sequence, strict=False)
            ]
        }
        previous_tool = current.last_tool
        result_class = current.last_result_class
        candidates = generate_continuations(
            prefix_messages=current.user_messages,
            state=current.state,
            desired_tool=desired_tool,
            trace=trace_context,
            previous_tool=previous_tool,
            result_class=result_class,
            include_explicit=include_explicit,
            include_prompt_bank=include_prompt_bank,
            include_edge_templates=include_edge_policy,
            include_mutations=include_mutation,
        )
        if not candidates:
            continue

        candidate = candidates[step % len(candidates)]
        seed = seeds[step % len(seeds)] if seeds else 123
        attempt = _extension_result(
            backend=backend,
            seed=seed,
            prefix=current,
            candidate=candidate,
            desired_tool=desired_tool,
            max_tool_hops=max_tool_hops,
        )
        attempts.append(attempt)
        current.times_extended += 1
        if attempt.transition_success:
            current.successful_extensions += 1
        else:
            current.failed_extensions += 1
        current.cell_hashes.add(attempt.cell_hash)
        current.transition_success_rates[desired_tool] = current.successful_extensions / current.times_extended if current.times_extended else 0.0

        if attempt.transition_success or attempt.replay_valid:
            next_prefix = PrefixEntry(
                prefix_id=f"{current.prefix_id}:{attempt.candidate_id}:{step}",
                snapshot=attempt.post_snapshot,
                user_messages=attempt.user_messages,
                state=_state_from_trace(attempt.original_trace),
                tool_sequence=attempt.tool_sequence,
                source_sequence=attempt.source_sequence,
                depth=attempt.depth,
                available_next_tools=[],
                transition_success_rates={desired_tool: 1.0 if attempt.transition_success else 0.0},
                cell_hashes={attempt.cell_hash},
                mechanism_signature=attempt.mechanism_signature,
                predicate_hits=[pred["predicate"] for pred in attempt.predicates],
                replay_valid=attempt.replay_valid,
                times_extended=0,
                successful_extensions=0,
                failed_extensions=0,
                last_tool=attempt.tool_sequence[-1] if attempt.tool_sequence else None,
                last_result_class=_result_class_from_event(_last_event(attempt.original_trace)),
                last_source=attempt.source_sequence[-1] if attempt.source_sequence else None,
                note="extended" if attempt.transition_success else "replayed",
            )
            prefixes.append(next_prefix)

    summary = {
        "backend": backend.name,
        "selection_policy": selection_policy,
        "desired_tool": desired_tool,
        "attempts": len(attempts),
        "replay_valid_rate": statistics.mean(1.0 if attempt.replay_valid else 0.0 for attempt in attempts) if attempts else 0.0,
        "transition_success_rate": statistics.mean(1.0 if attempt.transition_success else 0.0 for attempt in attempts) if attempts else 0.0,
        "unique_cells": len({attempt.cell_hash for attempt in attempts}),
        "unique_mechanisms": len({attempt.mechanism_signature for attempt in attempts}),
        "predicate_count": sum(len(attempt.predicates) for attempt in attempts),
        "predicate_severity_sum": sum(_score_predicates(attempt.predicates) for attempt in attempts),
        "tool_diversity": len({tool for attempt in attempts for tool in attempt.tool_sequence}),
        "best_depth": max((len(attempt.tool_sequence) for attempt in attempts), default=0),
        "best_clean_event_count": max((attempt.clean_event_count for attempt in attempts), default=0),
        "prefix_count": len(prefixes),
        "prefixes_replayed": sum(1 for prefix in prefixes if prefix.replay_valid),
    }

    prefix_rows: list[dict[str, Any]] = []
    for prefix in prefixes:
        prefix_rows.append(
            {
                "prefix_id": prefix.prefix_id,
                "depth": prefix.depth,
                "tool_sequence": prefix.tool_sequence,
                "source_sequence": prefix.source_sequence,
                "last_tool": prefix.last_tool,
                "last_result_class": prefix.last_result_class,
                "continuation_success_probability": prefix.continuation_success_probability,
                "unique_cells": len(prefix.cell_hashes),
                "times_extended": prefix.times_extended,
                "successful_extensions": prefix.successful_extensions,
                "failed_extensions": prefix.failed_extensions,
                "replay_valid": prefix.replay_valid,
                "mechanism_signature": prefix.mechanism_signature,
                "predicate_hits": prefix.predicate_hits,
                "note": prefix.note,
            }
        )
    return attempts, summary, prefix_rows


def render_prefix_extension_report(summary: dict[str, Any], prefix_rows: list[dict[str, Any]], attempts: list[PrefixAttempt]) -> str:
    lines: list[str] = []
    lines.append("# Prefix extension results")
    lines.append("")
    lines.append(f"- backend: {summary['backend']}")
    lines.append(f"- selection policy: {summary['selection_policy']}")
    lines.append(f"- desired tool: {summary['desired_tool']}")
    lines.append(f"- attempts: {summary['attempts']}")
    lines.append(f"- replay valid rate: {summary['replay_valid_rate']:.2f}")
    lines.append(f"- transition success rate: {summary['transition_success_rate']:.2f}")
    lines.append(f"- unique cells: {summary['unique_cells']}")
    lines.append(f"- unique mechanisms: {summary['unique_mechanisms']}")
    lines.append(f"- predicate count: {summary['predicate_count']}")
    lines.append(f"- predicate severity sum: {summary['predicate_severity_sum']}")
    lines.append(f"- tool diversity: {summary['tool_diversity']}")
    lines.append(f"- best depth: {summary['best_depth']}")
    lines.append(f"- best clean-event count: {summary['best_clean_event_count']}")
    lines.append(f"- prefix count: {summary['prefix_count']}")
    lines.append("")
    lines.append("## Best trajectory")
    lines.append("")
    best = max(attempts, key=lambda attempt: (len(attempt.tool_sequence), attempt.transition_success, attempt.replay_valid, attempt.continuation_value), default=None)
    if best is not None:
        lines.append(f"- prefix: {best.prefix_id}")
        lines.append(f"- candidate: {best.candidate_id}")
        lines.append(f"- source: {best.source}")
        lines.append(f"- structural frame: {best.structural_frame}")
        lines.append(f"- prompt: {best.prompt}")
        lines.append(f"- tool sequence: {' → '.join(best.tool_sequence) or '—'}")
        lines.append(f"- replay valid: {best.replay_valid}")
        lines.append(f"- transition success: {best.transition_success}")
        lines.append(f"- cell: {best.cell_hash}")
        lines.append(f"- mechanism: {best.mechanism_signature}")
    lines.append("")
    lines.append("## Prefix archive")
    lines.append("")
    lines.append("| Prefix | Depth | Last tool | Last result | Continuation success | Unique cells | Extended | Successes | Failures | Replay | Note |")
    lines.append("| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |")
    for row in prefix_rows:
        lines.append(
            f"| {row['prefix_id']} | {row['depth']} | {row['last_tool'] or '—'} | {row['last_result_class']} | {row['continuation_success_probability']:.2f} | {row['unique_cells']} | {row['times_extended']} | {row['successful_extensions']} | {row['failed_extensions']} | {row['replay_valid']} | {row['note']} |"
        )
    return "\n".join(lines)
