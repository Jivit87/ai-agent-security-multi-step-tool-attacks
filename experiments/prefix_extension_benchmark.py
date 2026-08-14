from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.agent_steering_benchmark import run_benchmark as run_prompt_benchmark
from experiments.backend_adapter import available_backend_specs
from experiments.edge_policy import collect_edge_policy_records
from experiments.prefix_extension_search import render_prefix_extension_report, run_prefix_extension_search
from experiments.web_open_to_fs_read import _build_web_open_prefix, _render_report as render_reverse_reachability_report, _run_variant


DEFAULT_RESULTS = Path("experiments/prefix_extension_results.jsonl")
DEFAULT_BENCHMARK = Path("experiments/prefix_extension_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/prefix_extension_results.md")
DEFAULT_REVERSE = Path("docs/reverse_reachability_results.md")


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
            "best_clean_event_count": 0,
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
        "severity_sum": sum(sum(p["severity"] for p in a["predicates"]) for a in attempts),
        "tool_diversity": len({tool for a in attempts for tool in a["tool_sequence"]}),
        "deepest": max((len(a["tool_sequence"]) for a in attempts), default=0),
        "best_clean_event_count": max((a["clean_event_count"] for a in attempts), default=0),
    }


def _render_mode_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Mode | Attempts | Replay valid rate | Transition success rate | Unique cells | Unique mechanisms | Predicates | Severity sum | Tool diversity | Deepest | Best clean events |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['transition_success_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['predicate_count']} | {row['severity_sum']} | {row['tool_diversity']} | {row['deepest']} | {row['best_clean_event_count']} |"
        )
    return "\n".join(lines)


def _render_policy_table(rows: list[dict[str, Any]]) -> str:
    lines = [
        "| Selection policy | Attempts | Replay valid rate | Transition success rate | Unique cells | Unique mechanisms | Deepest |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['selection_policy']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['transition_success_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['best_depth']} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--reverse-report", type=Path, default=DEFAULT_REVERSE)
    parser.add_argument("--backend", type=str, default="deterministic")
    parser.add_argument("--seeds", type=str, default="123,456")
    parser.add_argument("--budget-s", type=float, default=120.0)
    args = parser.parse_args()

    seeds = tuple(int(item) for item in args.seeds.split(",") if item.strip())
    backend = next(spec for spec in available_backend_specs() if spec.name == args.backend)

    prompt_attempts = run_prompt_benchmark(backends=[backend], seeds=seeds, max_tool_hops=4)
    edge_records, edge_summary, _edge_rows, _edge_attempts = collect_edge_policy_records(
        backend=backend,
        seeds=seeds,
        budget_s=args.budget_s,
        policy_mode="adaptive",
        edge_key_variant="D",
        prompt_bank_fallback=True,
        seed_with_prompt_bank=True,
    )

    prefix_modes = {
        "prefix_extension": dict(
            selection_policy="depth_first",
            include_prompt_bank=False,
            include_edge_policy=False,
            include_mutation=False,
            include_explicit=True,
        ),
        "prefix_extension_plus_edge": dict(
            selection_policy="edge_bottleneck_first",
            include_prompt_bank=False,
            include_edge_policy=True,
            include_mutation=False,
            include_explicit=True,
        ),
        "prefix_extension_plus_all": dict(
            selection_policy="hybrid",
            include_prompt_bank=True,
            include_edge_policy=True,
            include_mutation=True,
            include_explicit=True,
        ),
    }

    prefix_runs: dict[str, tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]], list[Any]]] = {}
    for mode, kwargs in prefix_modes.items():
        attempts, summary, prefix_rows = run_prefix_extension_search(
            backend=backend,
            seeds=seeds,
            budget_s=args.budget_s,
            desired_tool="fs.read",
            **kwargs,
        )
        prefix_runs[mode] = (
            [
                {
                    "mode": mode,
                    "seed": attempt.seed,
                    "prefix_id": attempt.prefix_id,
                    "candidate_id": attempt.candidate_id,
                    "source": attempt.source,
                    "structural_frame": attempt.structural_frame,
                    "prompt": attempt.prompt,
                    "tool_sequence": attempt.tool_sequence,
                    "source_sequence": attempt.source_sequence,
                    "predicates": attempt.predicates,
                    "cell_hash": attempt.cell_hash,
                    "score_cell_hash": attempt.score_cell_hash,
                    "state_key": attempt.state_key,
                    "mechanism_signature": attempt.mechanism_signature,
                    "replay_valid": attempt.replay_valid,
                    "transition_success": attempt.transition_success,
                    "depth": attempt.depth,
                    "clean_event_count": attempt.clean_event_count,
                    "egress_count": attempt.egress_count,
                    "guardrail_blocked": attempt.guardrail_blocked,
                    "refusal": attempt.refusal,
                    "continuation_value": attempt.continuation_value,
                }
                for attempt in attempts
            ],
            summary,
            prefix_rows,
            attempts,
        )

    prefix_policy_rows: list[dict[str, Any]] = []
    for selection_policy in ("depth_first", "novelty_first", "edge_bottleneck_first", "value_first", "hybrid"):
        attempts, summary, prefix_rows = run_prefix_extension_search(
            backend=backend,
            seeds=seeds,
            budget_s=min(60.0, args.budget_s / 2),
            selection_policy=selection_policy,
            desired_tool="fs.read",
            include_prompt_bank=True,
            include_edge_policy=True,
            include_mutation=True,
            include_explicit=True,
        )
        prefix_policy_rows.append(
            {
                "selection_policy": selection_policy,
                "attempts": len(attempts),
                "replay_valid_rate": summary["replay_valid_rate"],
                "transition_success_rate": summary["transition_success_rate"],
                "unique_cells": summary["unique_cells"],
                "unique_mechanisms": summary["unique_mechanisms"],
                "best_depth": summary["best_depth"],
                "best_clean_event_count": summary["best_clean_event_count"],
                "prefix_rows": prefix_rows,
            }
        )

    web_open_prefix = _build_web_open_prefix(backend, seeds[0] if seeds else 123)
    reverse_variants = {
        "natural": _run_variant(
            backend=backend,
            seed=seeds[0] if seeds else 123,
            prefix=web_open_prefix["prefix"],
            desired_tool="fs.read",
            include_prompt_bank=False,
            include_edge_policy=True,
            include_mutation=False,
            include_explicit=False,
        ),
        "explicit": _run_variant(
            backend=backend,
            seed=seeds[0] if seeds else 123,
            prefix=web_open_prefix["prefix"],
            desired_tool="fs.read",
            include_prompt_bank=False,
            include_edge_policy=False,
            include_mutation=False,
            include_explicit=True,
        ),
        "mixed": _run_variant(
            backend=backend,
            seed=seeds[0] if seeds else 123,
            prefix=web_open_prefix["prefix"],
            desired_tool="fs.read",
            include_prompt_bank=True,
            include_edge_policy=True,
            include_mutation=True,
            include_explicit=True,
        ),
    }

    records: list[dict[str, Any]] = []
    for record in prompt_attempts:
        records.append({"mode": "prompt_bank_only", **record})
    for record in edge_records:
        records.append({"mode": "phase8_edge_policy", **record})
    for mode, (attempt_records, _summary, _prefix_rows, _attempts) in prefix_runs.items():
        records.extend(attempt_records)
    for variant, rows in reverse_variants.items():
        for row in rows:
            records.append({"mode": f"web_open_to_fs_read::{variant}", **row})

    _dump_jsonl(args.results, records)

    mode_rows = [
        _mode_summary(
            "prompt_bank_only",
            backend.name,
            [
                {
                    "replay_valid": True,
                    "transition_success": record.get("failure_classification") == "REACHED",
                    "cell_hash": record["cell_hash"],
                    "mechanism_signature": " → ".join(record["tool_names"]),
                    "predicates": [{"severity": 1} for _ in record.get("predicate_names", [])],
                    "tool_sequence": record["tool_names"],
                    "clean_event_count": 0,
                }
                for record in prompt_attempts
            ],
        ),
        {
            "mode": "phase8_edge_policy",
            "backend": backend.name,
            "attempts": len(edge_records),
            "replay_valid_rate": edge_summary["replay_valid_rate"],
            "transition_success_rate": edge_summary["transition_success_rate"],
            "unique_cells": edge_summary["unique_cells"],
            "unique_mechanisms": edge_summary["unique_mechanisms"],
            "predicate_count": edge_summary["predicate_count"],
            "severity_sum": edge_summary["predicate_severity_sum"],
            "tool_diversity": edge_summary["tool_diversity"],
            "deepest": edge_summary["best_depth"],
            "best_clean_event_count": edge_summary["best_clean_event_count"],
        },
    ]
    for mode, (_attempts, summary, _prefix_rows, _raw_attempts) in prefix_runs.items():
        mode_rows.append(
            {
                "mode": mode,
                "backend": backend.name,
                "attempts": summary["attempts"],
                "replay_valid_rate": summary["replay_valid_rate"],
                "transition_success_rate": summary["transition_success_rate"],
                "unique_cells": summary["unique_cells"],
                "unique_mechanisms": summary["unique_mechanisms"],
                "predicate_count": summary["predicate_count"],
                "severity_sum": summary["predicate_severity_sum"],
                "tool_diversity": summary["tool_diversity"],
                "deepest": summary["best_depth"],
                "best_clean_event_count": summary["best_clean_event_count"],
            }
        )

    benchmark_rows = mode_rows + prefix_policy_rows
    _dump_jsonl(args.benchmark, benchmark_rows)

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        render_prefix_extension_report(
            prefix_runs["prefix_extension_plus_all"][1],
            prefix_runs["prefix_extension_plus_all"][2],
            prefix_runs["prefix_extension_plus_all"][3],
        )
        + "\n\n## Selection policy ablation\n\n"
        + _render_policy_table(prefix_policy_rows),
        encoding="utf-8",
    )
    args.reverse_report.parent.mkdir(parents=True, exist_ok=True)
    args.reverse_report.write_text(
        render_reverse_reachability_report(
            web_open_prefix,
            reverse_variants,
        ),
        encoding="utf-8",
    )

    print(f"wrote results to {args.results}")
    print(f"wrote benchmark to {args.benchmark}")
    print(f"wrote report to {args.report}")
    print(f"wrote reverse report to {args.reverse_report}")


if __name__ == "__main__":
    main()
