from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.backend_adapter import available_backend_specs
from experiments.agent_steering_benchmark import run_benchmark as run_prompt_benchmark
from experiments.steering_search import run_search


DEFAULT_OUT = Path("experiments/steering_search_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/steering_search_benchmark.md")


def _dump_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _baseline_records(mode: str, backend_name: str, attempts: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "mode": mode,
        "backend": backend_name,
        "attempts": len(attempts),
        "replay_valid_rate": statistics.mean(1.0 if a["replay_valid"] else 0.0 for a in attempts) if attempts else 0.0,
        "unique_cells": len({a["cell_hash"] for a in attempts}),
        "unique_mechanisms": len({a["mechanism_signature"] for a in attempts}),
        "predicate_count": sum(len(a["predicates"]) for a in attempts),
        "severity_sum": sum(sum(p["severity"] for p in a["predicates"]) for a in attempts),
        "tool_diversity": len({tool for a in attempts for tool in a["tool_sequence"]}),
        "deepest": max((len(a["tool_sequence"]) for a in attempts), default=0),
    }


def _render_report(rows: list[dict[str, Any]]) -> str:
    lines = ["# Steering search benchmark", "", "| Mode | Attempts | Replay valid rate | Unique cells | Unique mechanisms | Predicates | Severity sum | Tool diversity | Deepest |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['predicate_count']} | {row['severity_sum']} | {row['tool_diversity']} | {row['deepest']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backend", type=str, default="deterministic")
    parser.add_argument("--seeds", type=str, default="123,456")
    args = parser.parse_args()

    seeds = tuple(int(item) for item in args.seeds.split(",") if item.strip())
    backend = next(spec for spec in available_backend_specs() if spec.name == args.backend)

    prompt_attempts = run_prompt_benchmark(backends=[backend], seeds=seeds, max_tool_hops=4)
    graph_attempts, graph_summary, _ = run_search(
        backend=backend,
        seeds=seeds,
        budget_s=120.0,
        mutation_pool_size=1,
    )
    steering_attempts, steering_summary, _ = run_search(
        backend=backend,
        seeds=seeds,
        budget_s=120.0,
        mutation_pool_size=2,
    )
    mutation_attempts, mutation_summary, _ = run_search(
        backend=backend,
        seeds=seeds,
        budget_s=120.0,
        mutation_pool_size=3,
    )

    def from_prompt_bank() -> dict[str, Any]:
        return {
            "mode": "prompt_bank_only",
            "backend": args.backend,
            "attempts": len(prompt_attempts),
            "replay_valid_rate": 1.0,
            "unique_cells": len({r["cell_hash"] for r in prompt_attempts}),
            "unique_mechanisms": len({tuple(r["tool_sequence"]) for r in prompt_attempts}),
            "predicate_count": sum(len(r["predicate_names"]) for r in prompt_attempts),
            "severity_sum": sum(r["predicate_severity_sum"] for r in prompt_attempts),
            "tool_diversity": len({tool for r in prompt_attempts for tool in r["tool_names"]}),
            "deepest": max((len(r["tool_names"]) for r in prompt_attempts), default=0),
        }

    records = [
        from_prompt_bank(),
        {
            "mode": "graph_only",
            "backend": args.backend,
            "attempts": len(graph_attempts),
            "replay_valid_rate": graph_summary["replay_valid_rate"],
            "unique_cells": graph_summary["unique_cells"],
            "unique_mechanisms": graph_summary["unique_mechanisms"],
            "predicate_count": graph_summary["predicate_count"],
            "severity_sum": graph_summary["predicate_severity_sum"],
            "tool_diversity": graph_summary["tool_diversity"],
            "deepest": graph_summary["best_depth"],
        },
        {
            "mode": "steering_aware_search",
            "backend": args.backend,
            "attempts": len(steering_attempts),
            "replay_valid_rate": steering_summary["replay_valid_rate"],
            "unique_cells": steering_summary["unique_cells"],
            "unique_mechanisms": steering_summary["unique_mechanisms"],
            "predicate_count": steering_summary["predicate_count"],
            "severity_sum": steering_summary["predicate_severity_sum"],
            "tool_diversity": steering_summary["tool_diversity"],
            "deepest": steering_summary["best_depth"],
        },
        {
            "mode": "steering_plus_mutation",
            "backend": args.backend,
            "attempts": len(mutation_attempts),
            "replay_valid_rate": mutation_summary["replay_valid_rate"],
            "unique_cells": mutation_summary["unique_cells"],
            "unique_mechanisms": mutation_summary["unique_mechanisms"],
            "predicate_count": mutation_summary["predicate_count"],
            "severity_sum": mutation_summary["predicate_severity_sum"],
            "tool_diversity": mutation_summary["tool_diversity"],
            "deepest": mutation_summary["best_depth"],
        },
    ]
    _dump_jsonl(args.out, records)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(records), encoding="utf-8")
    print(f"wrote benchmark to {args.out}")
    print(f"wrote report to {args.report}")


if __name__ == "__main__":
    main()
