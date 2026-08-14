from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from experiments.backend_adapter import BackendSpec
from experiments.continuation_generator import ContinuationCandidate, generate_continuations
from experiments.edge_policy import _result_class_from_event
from experiments.prefix_extension_search import PrefixAttempt, PrefixEntry, _extension_result
from experiments.route_library import RouteFragment, RouteLibrary
from experiments.security_state import SecurityState


@dataclass(frozen=True)
class ComposedRouteRecord:
    base_route_id: str
    candidate_id: str
    desired_tool: str
    prompt: str
    transition_success: bool
    replay_valid: bool
    cell_hash: str
    mechanism_signature: str
    predicates: list[dict[str, Any]]
    route: RouteFragment
    attempt: PrefixAttempt


def _state_from_snapshot(snapshot: dict[str, Any]) -> SecurityState:
    return SecurityState(
        recent_sources=tuple(snapshot.get("recent_sources", [])),
        recent_tools=tuple(snapshot.get("recent_tools", [])),
        last_tool=snapshot.get("last_tool"),
        last_tool_ok=snapshot.get("last_tool_ok"),
        episode_depth=int(snapshot.get("episode_depth", 0)),
        web_recent=bool(snapshot.get("web_recent", False)),
        email_recent=bool(snapshot.get("email_recent", False)),
        taint_active=bool(snapshot.get("taint_active", False)),
        clean_event_count=int(snapshot.get("clean_event_count", 0)),
        secret_read=bool(snapshot.get("secret_read", False)),
        egress_count=int(snapshot.get("egress_count", 0)),
        predicate_names=tuple(snapshot.get("predicate_names", [])),
        guardrail_blocked=bool(snapshot.get("guardrail_blocked", False)),
        refusal=bool(snapshot.get("refusal", False)),
    )


def _prefix_entry(fragment: RouteFragment) -> PrefixEntry:
    state = _state_from_snapshot(fragment.resulting_state or fragment.required_state)
    return PrefixEntry(
        prefix_id=fragment.route_id,
        snapshot=fragment.snapshot,
        user_messages=list(fragment.user_messages),
        state=state,
        tool_sequence=list(fragment.tool_sequence),
        source_sequence=list(fragment.source_sequence),
        depth=len(fragment.user_messages),
        available_next_tools=[],
        transition_success_rates={},
        cell_hashes={fragment.cell_hash},
        mechanism_signature=fragment.mechanism_signature,
        predicate_hits=list(fragment.predicates),
        replay_valid=fragment.replay_valid,
        times_extended=fragment.replay_count,
        successful_extensions=int(fragment.success_rate > 0.0),
        failed_extensions=0 if fragment.success_rate > 0.0 else fragment.replay_count,
        last_tool=fragment.tool_sequence[-1] if fragment.tool_sequence else None,
        last_result_class=fragment.result_classes[-1] if fragment.result_classes else "EMPTY_RESULT",
        last_source=fragment.source_sequence[-1] if fragment.source_sequence else None,
        note=fragment.notes,
    )


def _fragment_from_attempt(attempt: PrefixAttempt, route_id: str) -> RouteFragment:
    state = SecurityState.from_trace(attempt.original_trace)
    return RouteFragment(
        route_id=route_id,
        entry_condition=attempt.prefix_id,
        user_messages=list(attempt.user_messages),
        tool_sequence=list(attempt.tool_sequence),
        result_classes=[_result_class_from_event(event) for event in attempt.original_trace.get("tool_events", [])],
        state_sequence=[state.canonical_key()],
        clean_event_count=attempt.clean_event_count,
        taint_state="CLEAN" if not state.taint_active else "TAINTED",
        predicates=[pred.get("predicate", "") for pred in attempt.predicates if pred.get("predicate")],
        cell_hash=attempt.cell_hash,
        mechanism_signature=attempt.mechanism_signature,
        replay_valid=attempt.replay_valid,
        replay_count=1,
        success_rate=1.0 if attempt.transition_success else 0.0,
        required_state={},
        resulting_state={},
        source_sequence=list(attempt.source_sequence),
        notes=f"desired={attempt.desired_tool}",
        snapshot=attempt.post_snapshot,
    )


class RouteComposer:
    def __init__(self, route_library: RouteLibrary | None = None) -> None:
        self.route_library = route_library or RouteLibrary()

    def extend(
        self,
        *,
        backend: BackendSpec,
        seed: int,
        fragment: RouteFragment,
        desired_tool: str,
        include_prompt_bank: bool = True,
        include_edge_policy: bool = True,
        include_mutation: bool = True,
        include_explicit: bool = True,
        max_tool_hops: int = 4,
    ) -> list[ComposedRouteRecord]:
        prefix = _prefix_entry(fragment)
        trace_context = {
            "tool_events": [
                {"name": name, "source": source}
                for name, source in zip(prefix.tool_sequence, prefix.source_sequence, strict=False)
            ]
        }
        candidates = generate_continuations(
            prefix_messages=prefix.user_messages,
            state=prefix.state,
            desired_tool=desired_tool,
            trace=trace_context,
            previous_tool=prefix.last_tool,
            result_class=prefix.last_result_class,
            include_prompt_bank=include_prompt_bank,
            include_edge_templates=include_edge_policy,
            include_mutations=include_mutation,
            include_explicit=include_explicit,
        )

        records: list[ComposedRouteRecord] = []
        for index, candidate in enumerate(candidates):
            attempt = _extension_result(
                backend=backend,
                seed=seed,
                prefix=prefix,
                candidate=candidate,
                desired_tool=desired_tool,
                max_tool_hops=max_tool_hops,
            )
            route = _fragment_from_attempt(attempt, f"{fragment.route_id}::{candidate.candidate_id}:{index}")
            records.append(
                ComposedRouteRecord(
                    base_route_id=fragment.route_id,
                    candidate_id=candidate.candidate_id,
                    desired_tool=desired_tool,
                    prompt=candidate.prompt,
                    transition_success=attempt.transition_success,
                    replay_valid=attempt.replay_valid,
                    cell_hash=attempt.cell_hash,
                    mechanism_signature=attempt.mechanism_signature,
                    predicates=list(attempt.predicates),
                    route=route,
                    attempt=attempt,
                )
            )
        return records

    def best_extension(
        self,
        *,
        backend: BackendSpec,
        seed: int,
        fragment: RouteFragment,
        desired_tool: str,
        include_prompt_bank: bool = True,
        include_edge_policy: bool = True,
        include_mutation: bool = True,
        include_explicit: bool = True,
        max_tool_hops: int = 4,
    ) -> ComposedRouteRecord | None:
        records = self.extend(
            backend=backend,
            seed=seed,
            fragment=fragment,
            desired_tool=desired_tool,
            include_prompt_bank=include_prompt_bank,
            include_edge_policy=include_edge_policy,
            include_mutation=include_mutation,
            include_explicit=include_explicit,
            max_tool_hops=max_tool_hops,
        )
        if not records:
            return None
        return max(records, key=lambda record: (record.transition_success, record.replay_valid, len(record.route.tool_sequence), record.route.success_rate))
