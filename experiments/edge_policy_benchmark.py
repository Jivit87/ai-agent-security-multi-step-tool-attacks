from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.agent_steering_benchmark import run_benchmark as run_prompt_benchmark
from experiments.backend_adapter import available_backend_specs
from experiments.edge_policy import collect_edge_policy_records, _score_predicates  # noqa: PLC2701
from experiments.edge_policy import run_edge_policy_search
from experiments.security_state import SecurityState
from experiments.steering_search import run_search


DEFAULT_RESULTS = Path("experiments/edge_policy_results.jsonl")
DEFAULT_BENCHMARK = Path("experiments/edge_policy_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/edge_policy_benchmark.md")
DEFAULT_TRANSITION_REPORT = Path("docs/transition_policy_results.md")
DEFAULT_MODEL_LIMITED = Path("docs/model_limited_edges.md")


def _dump_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _mode_summary(mode: str, backend: str, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    if not attempts:
        return {
            "mode": mode,
            "backend": backend,
            "attempts": 0,
            "replay_valid_rate": 0.0,
            "transition_success_rate": 0.0,
            "unique_cells": 0,
            "unique_mechanisms": 0,
            "predicate_count": 0,
            "severity_sum": 0,
            "tool_diversity": 0,
            "deepest": 0,
            "max_clean_event_count": 0,
        }
    return {
        "mode": mode,
        "backend": backend,
        "attempts": len(attempts),
        "replay_valid_rate": statistics.mean(1.0 if a["replay_valid"] else 0.0 for a in attempts),
        "transition_success_rate": statistics.mean(1.0 if a["transition_success"] else 0.0 for a in attempts),
        "unique_cells": len({a["cell_hash"] for a in attempts}),
        "unique_mechanisms": len({a["mechanism_signature"] for a in attempts}),
        "predicate_count": sum(len(a["predicates"]) for a in attempts),
        "severity_sum": sum(_score_predicates(a["predicates"]) for a in attempts),
        "tool_diversity": len({tool for a in attempts for tool in a["tool_sequence"]}),
        "deepest": max((len(a["tool_sequence"]) for a in attempts), default=0),
        "max_clean_event_count": max((a["clean_event_count"] for a in attempts), default=0),
    }


def _transition_rows(attempts_by_mode: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for mode, attempts in attempts_by_mode.items():
        for attempt in attempts:
            key = (
                attempt["previous_tool"] or "NONE",
                attempt["previous_result_class"],
                attempt["state_class"],
                attempt["desired_next_tool"],
            )
            row = grouped.setdefault(
                key,
                {
                    "current_state": f"{attempt['state_class']} / {attempt['previous_tool'] or 'NONE'} / {attempt['previous_result_class']}",
                    "desired_tool": attempt["desired_next_tool"],
                    "best_policy": None,
                    "best_mode": None,
                    "best_success_rate": 0.0,
                    "attempts": 0,
                    "successes": 0,
                    "replay_successes": 0,
                    "unique_cells": set(),
                    "unique_mechanisms": set(),
                    "modes": defaultdict(lambda: {"attempts": 0, "successes": 0, "replay": 0}),
                },
            )
            row["attempts"] += 1
            row["successes"] += 1 if attempt["transition_success"] else 0
            row["replay_successes"] += 1 if attempt["replay_valid"] else 0
            row["unique_cells"].add(attempt["cell_hash"])
            row["unique_mechanisms"].add(attempt["mechanism_signature"])
            mode_stats = row["modes"][mode]
            mode_stats["attempts"] += 1
            mode_stats["successes"] += 1 if attempt["transition_success"] else 0
            mode_stats["replay"] += 1 if attempt["replay_valid"] else 0

    rows: list[dict[str, Any]] = []
    for key, row in grouped.items():
        best_mode = None
        best_rate = -1.0
        for mode, stats in row["modes"].items():
            rate = stats["successes"] / stats["attempts"] if stats["attempts"] else 0.0
            if rate > best_rate:
                best_rate = rate
                best_mode = mode
        rows.append(
            {
                "current_state": row["current_state"],
                "desired_tool": row["desired_tool"],
                "attempts": row["attempts"],
                "successes": row["successes"],
                "replay_successes": row["replay_successes"],
                "success_rate": row["successes"] / row["attempts"] if row["attempts"] else 0.0,
                "replay_rate": row["replay_successes"] / row["attempts"] if row["attempts"] else 0.0,
                "unique_cells": len(row["unique_cells"]),
                "unique_mechanisms": len(row["unique_mechanisms"]),
                "best_policy": best_mode,
                "best_success_rate": best_rate if best_rate >= 0 else 0.0,
            }
        )
    rows.sort(key=lambda row: (-row["success_rate"], -row["attempts"], row["current_state"], row["desired_tool"]))
    return rows


def _best_attempt(attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not attempts:
        return None
    return max(attempts, key=lambda a: (len(a["tool_sequence"]), a["transition_success"], a["replay_valid"], a["cell_hash"]))


def _render_mode_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Mode | Attempts | Replay valid rate | Transition success rate | Unique cells | Unique mechanisms | Predicates | Severity sum | Tool diversity | Deepest | Max clean events |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['transition_success_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['predicate_count']} | {row['severity_sum']} | {row['tool_diversity']} | {row['deepest']} | {row['max_clean_event_count']} |"
        )
    return "\n".join(lines)


def _render_transition_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Current state | Desired tool | Best policy | Success rate | Replay rate | Attempts | Unique cells | Unique mechanisms |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['current_state']} | {row['desired_tool']} | {row['best_policy'] or ''} | {row['success_rate']:.2f} | {row['replay_rate']:.2f} | {row['attempts']} | {row['unique_cells']} | {row['unique_mechanisms']} |"
        )
    return "\n".join(lines)


def _render_policy_report(
    *,
    title: str,
    mode_summaries: list[dict[str, Any]],
    transition_rows: list[dict[str, Any]],
    attempts_by_mode: dict[str, list[dict[str, Any]]],
) -> str:
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append("## Mode comparison")
    lines.append("")
    lines.append(_render_mode_table(mode_summaries))
    lines.append("")
    lines.append("## Transition policy table")
    lines.append("")
    lines.append(_render_transition_table(transition_rows))
    lines.append("")
    lines.append("## Best trajectories")
    lines.append("")
    for mode, attempts in attempts_by_mode.items():
        best = _best_attempt(attempts)
        lines.append(f"### {mode}")
        lines.append("")
        if best is None:
            lines.append("- no attempts")
        else:
            lines.append(f"- desired tool: {best['desired_next_tool']}")
            lines.append(f"- template: {best['template_id']}")
            lines.append(f"- structural frame: {best['structural_frame']}")
            lines.append(f"- prompt: {best['prompt']}")
            lines.append(f"- tool sequence: {' → '.join(best['tool_sequence']) or '—'}")
            lines.append(f"- cell: {best['cell_hash']}")
            lines.append(f"- mechanism: {best['mechanism_signature']}")
            lines.append(f"- replay valid: {best['replay_valid']}")
            lines.append(f"- transition success: {best['transition_success']}")
        lines.append("")
    return "\n".join(lines)


def _render_model_limited_report(transition_rows: list[dict[str, Any]]) -> str:
    rows = [row for row in transition_rows if row["success_rate"] == 0.0 or row["success_rate"] < 0.5]
    lines: list[str] = []
    lines.append("# Model-limited edges")
    lines.append("")
    lines.append("| Current state | Desired tool | Success rate | Replay rate | Best policy | Attempts | Classification |")
    lines.append("| --- | --- | ---: | ---: | --- | ---: | --- |")
    for row in rows:
        classification = "MODEL_LIMITED" if row["success_rate"] == 0.0 else "PARTIALLY_MODEL_LIMITED"
        lines.append(
            f"| {row['current_state']} | {row['desired_tool']} | {row['success_rate']:.2f} | {row['replay_rate']:.2f} | {row['best_policy'] or ''} | {row['attempts']} | {classification} |"
        )
    if not rows:
        lines.append("| — | — | 0.00 | 0.00 | — | 0 | NONE |")
    return "\n".join(lines)


def _scenario_transition_rows(scenario_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in scenario_rows:
        grouped.setdefault(row["scenario"], []).append(row)
    rows: list[dict[str, Any]] = []
    for scenario, rows_for_scenario in grouped.items():
        best = max(rows_for_scenario, key=lambda row: (row["transition_success_rate"], row["replay_valid_rate"], row["unique_cells"]))
        rows.append(
            {
                "current_state": scenario,
                "desired_tool": scenario.split("->", 1)[-1] if "->" in scenario else "",
                "attempts": sum(row["attempts"] for row in rows_for_scenario),
                "successes": sum(row["attempts"] * row["transition_success_rate"] for row in rows_for_scenario),
                "replay_successes": sum(row["attempts"] * row["replay_valid_rate"] for row in rows_for_scenario),
                "success_rate": best["transition_success_rate"],
                "replay_rate": best["replay_valid_rate"],
                "unique_cells": best["unique_cells"],
                "unique_mechanisms": best["unique_mechanisms"],
                "best_policy": best["mode"],
                "best_success_rate": best["transition_success_rate"],
                "best_attempts": best["attempts"],
                "best_deepest": best["deepest"],
                "best_max_clean_events": best["max_clean_event_count"],
            }
        )
    rows.sort(key=lambda row: (row["current_state"], row["desired_tool"]))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--transition-report", type=Path, default=DEFAULT_TRANSITION_REPORT)
    parser.add_argument("--model-limited", type=Path, default=DEFAULT_MODEL_LIMITED)
    parser.add_argument("--backend", type=str, default="deterministic")
    parser.add_argument("--seeds", type=str, default="123,456,789")
    parser.add_argument("--budget-s", type=float, default=120.0)
    args = parser.parse_args()

    seeds = tuple(int(item) for item in args.seeds.split(",") if item.strip())
    backend = next(spec for spec in available_backend_specs() if spec.name == args.backend)
    scenario_budget_s = max(24.0, min(45.0, args.budget_s / 2))

    scenario_specs = [
        {
            "scenario": "clean->web.search",
            "focus_previous_tool": "clean",
            "forced_desired_tool": "web.search",
        },
        {
            "scenario": "web.search->web.open",
            "focus_previous_tool": "web.search",
            "forced_desired_tool": "web.open",
        },
        {
            "scenario": "web.open->fs.read",
            "focus_previous_tool": "web.open",
            "forced_desired_tool": "fs.read",
        },
        {
            "scenario": "email.read->fs.read",
            "focus_previous_tool": "email.read",
            "forced_desired_tool": "fs.read",
        },
        {
            "scenario": "fs.read->fs.read",
            "focus_previous_tool": "fs.read",
            "forced_desired_tool": "fs.read",
        },
        {
            "scenario": "clean->http.post",
            "focus_previous_tool": "clean",
            "forced_desired_tool": "http.post",
        },
        {
            "scenario": "clean->email.send",
            "focus_previous_tool": "clean",
            "forced_desired_tool": "email.send",
        },
    ]

    prompt_attempts = run_prompt_benchmark(backends=[backend], seeds=seeds, max_tool_hops=4)
    generic_attempts, generic_summary, _ = run_search(
        backend=backend,
        seeds=seeds,
        budget_s=args.budget_s,
        mutation_pool_size=2,
    )

    edge_runs = {
        "edge_uniform": collect_edge_policy_records(
            backend=backend,
            seeds=seeds,
            budget_s=args.budget_s,
            policy_mode="uniform",
            edge_key_variant="D",
            prompt_bank_fallback=False,
            seed_with_prompt_bank=True,
        ),
        "edge_adaptive": collect_edge_policy_records(
            backend=backend,
            seeds=seeds,
            budget_s=args.budget_s,
            policy_mode="adaptive",
            edge_key_variant="D",
            prompt_bank_fallback=False,
            seed_with_prompt_bank=True,
        ),
        "prompt_bank_plus_edge": collect_edge_policy_records(
            backend=backend,
            seeds=seeds,
            budget_s=args.budget_s,
            policy_mode="adaptive",
            edge_key_variant="D",
            prompt_bank_fallback=True,
            seed_with_prompt_bank=True,
        ),
    }

    edge_attempts_by_mode = {mode: records for mode, (records, _summary, _edge_rows, _attempts) in edge_runs.items()}

    scenario_runs: dict[str, list[dict[str, Any]]] = {}
    scenario_rows: list[dict[str, Any]] = []
    scenario_attempt_records: list[dict[str, Any]] = []
    for spec in scenario_specs:
        for mode in ("edge_uniform", "edge_adaptive", "prompt_bank_plus_edge"):
            records, _summary, _edge_rows, _attempts = collect_edge_policy_records(
                backend=backend,
                seeds=seeds,
                budget_s=scenario_budget_s,
                policy_mode="adaptive" if mode != "edge_uniform" else "uniform",
                edge_key_variant="D",
                prompt_bank_fallback=(mode == "prompt_bank_plus_edge"),
                seed_with_prompt_bank=True,
                focus_previous_tool=spec["focus_previous_tool"],
                forced_desired_tool=spec["forced_desired_tool"],
            )
            for record in records:
                record = dict(record)
                record["mode"] = mode
                record["scenario"] = spec["scenario"]
                scenario_runs.setdefault(mode, []).append(record)
                scenario_attempt_records.append(record)
            scenario_rows.extend(
                [
                    {
                        "scenario": spec["scenario"],
                        "mode": mode,
                        "attempts": len(records),
                        "replay_valid_rate": statistics.mean(1.0 if r["replay_valid"] else 0.0 for r in records) if records else 0.0,
                        "transition_success_rate": statistics.mean(1.0 if r["transition_success"] else 0.0 for r in records) if records else 0.0,
                        "unique_cells": len({r["cell_hash"] for r in records}),
                        "unique_mechanisms": len({r["mechanism_signature"] for r in records}),
                        "predicate_count": sum(len(r["predicates"]) for r in records),
                        "severity_sum": sum(_score_predicates(r["predicates"]) for r in records),
                        "tool_diversity": len({tool for r in records for tool in r["tool_sequence"]}),
                        "deepest": max((len(r["tool_sequence"]) for r in records), default=0),
                        "max_clean_event_count": max((r["clean_event_count"] for r in records), default=0),
                    }
                ]
            )

    mode_summaries = [
        {
            "mode": "prompt_bank_only",
            "backend": backend.name,
            "attempts": len(prompt_attempts),
            "replay_valid_rate": 1.0 if prompt_attempts else 0.0,
            "transition_success_rate": statistics.mean(
                1.0 if record.get("failure_classification") == "REACHED" else 0.0 for record in prompt_attempts
            ) if prompt_attempts else 0.0,
            "unique_cells": len({record["cell_hash"] for record in prompt_attempts}),
            "unique_mechanisms": len({" → ".join(record["tool_names"]) for record in prompt_attempts}),
            "predicate_count": sum(len(record.get("predicate_names", [])) for record in prompt_attempts),
            "severity_sum": sum(record.get("predicate_severity_sum", 0) for record in prompt_attempts),
            "tool_diversity": len({tool for record in prompt_attempts for tool in record["tool_names"]}),
            "deepest": max((len(record["tool_names"]) for record in prompt_attempts), default=0),
            "max_clean_event_count": 0,
        },
        _mode_summary(
            "generic_steering",
            backend.name,
            [
                {
                    "replay_valid": attempt.replay_valid,
                    "transition_success": attempt.classification == "reached",
                    "cell_hash": attempt.cell_hash,
                    "mechanism_signature": attempt.mechanism_signature,
                    "predicates": attempt.predicates,
                    "tool_sequence": attempt.tool_sequence,
                    "clean_event_count": SecurityState.from_trace(attempt.original_trace).clean_event_count,
                }
                for attempt in generic_attempts
            ],
        ),
    ]

    transition_rows = _scenario_transition_rows(scenario_rows)

    scenario_report_lines: list[str] = []
    scenario_report_lines.append("## Edge scenario sweep")
    scenario_report_lines.append("")
    scenario_report_lines.append("| Scenario | Mode | Attempts | Replay valid rate | Transition success rate | Unique cells | Unique mechanisms | Predicates | Severity sum | Tool diversity | Deepest | Max clean events |")
    scenario_report_lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for row in scenario_rows:
        scenario_report_lines.append(
            f"| {row['scenario']} | {row['mode']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['transition_success_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['predicate_count']} | {row['severity_sum']} | {row['tool_diversity']} | {row['deepest']} | {row['max_clean_event_count']} |"
        )

    edge_rows_by_mode: dict[str, list[dict[str, Any]]] = {}
    for mode, (_records, summary, edge_rows, _attempts) in edge_runs.items():
        edge_rows_by_mode[mode] = edge_rows
        mode_summaries.append(
            _mode_summary(
                mode,
                backend.name,
                [
                    {
                        "replay_valid": record["replay_valid"],
                        "transition_success": record["transition_success"],
                        "cell_hash": record["cell_hash"],
                        "mechanism_signature": record["mechanism_signature"],
                        "predicates": record["predicates"],
                        "tool_sequence": record["tool_sequence"],
                        "clean_event_count": record["clean_event_count"],
                    }
                    for record in _records
                ],
            )
        )

    all_edge_attempt_records: list[dict[str, Any]] = []
    for mode, (records, _summary, _edge_rows, _attempts) in edge_runs.items():
        for record in records:
            record = dict(record)
            record["mode"] = mode
            all_edge_attempt_records.append(record)
    all_edge_attempt_records.extend(scenario_attempt_records)

    _dump_jsonl(args.results, all_edge_attempt_records)
    _dump_jsonl(
        args.benchmark,
        [
            {
                "mode": row["mode"],
                "backend": row["backend"],
                "attempts": row["attempts"],
                "replay_valid_rate": row["replay_valid_rate"],
                "transition_success_rate": row["transition_success_rate"],
                "unique_cells": row["unique_cells"],
                "unique_mechanisms": row["unique_mechanisms"],
                "predicate_count": row["predicate_count"],
                "severity_sum": row["severity_sum"],
                "tool_diversity": row["tool_diversity"],
                "deepest": row["deepest"],
                "max_clean_event_count": row["max_clean_event_count"],
            }
            for row in mode_summaries
        ],
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        _render_policy_report(
            title="Edge policy benchmark",
            mode_summaries=mode_summaries,
            transition_rows=transition_rows,
            attempts_by_mode=edge_attempts_by_mode,
        )
        + ("\n\n" + "\n".join(scenario_report_lines) if scenario_runs else ""),
        encoding="utf-8",
    )
    args.transition_report.parent.mkdir(parents=True, exist_ok=True)
    args.transition_report.write_text(
        _render_policy_report(
            title="Transition policy results",
            mode_summaries=mode_summaries,
            transition_rows=transition_rows,
            attempts_by_mode=edge_attempts_by_mode,
        ),
        encoding="utf-8",
    )
    args.model_limited.parent.mkdir(parents=True, exist_ok=True)
    args.model_limited.write_text(_render_model_limited_report(transition_rows), encoding="utf-8")

    print(f"wrote edge-policy records to {args.results}")
    print(f"wrote benchmark summary to {args.benchmark}")
    print(f"wrote report to {args.report}")
    print(f"wrote transition report to {args.transition_report}")
    print(f"wrote model-limited report to {args.model_limited}")


if __name__ == "__main__":
    main()
