from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.backend_validation_common import (
    DEFAULT_SEEDS,
    FIXTURES_DIR,
    SINK_SCENARIOS,
    execute_scenario,
    summarize_backend_availability,
    write_jsonl,
)


DEFAULT_OUT = Path("experiments/model_sink_matrix.jsonl")
DEFAULT_REPORT = Path("docs/model_sink_matrix.md")


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "attempts": 0,
            "tool_reach_rate": 0.0,
            "tool_call_success_rate": 0.0,
            "multi_turn_success_rate": 0.0,
            "guardrail_block_rate": 0.0,
            "predicate_rate": 0.0,
            "verified_breach_rate": 0.0,
        }

    attempts = len(rows)
    return {
        "attempts": attempts,
        "tool_reach_rate": sum(
            bool(row.get("target_tool")) and row.get("target_tool") in row.get("tool_names", [])
            for row in rows
        )
        / attempts,
        "tool_call_success_rate": sum(bool(row.get("tool_call_success")) for row in rows) / attempts,
        "multi_turn_success_rate": sum(bool(row.get("multi_turn_success")) for row in rows) / attempts,
        "guardrail_block_rate": sum(bool(row.get("guardrail_blocks")) for row in rows) / attempts,
        "predicate_rate": sum(bool(row.get("predicates")) for row in rows) / attempts,
        "verified_breach_rate": sum(bool(row.get("verified_breach")) for row in rows) / attempts,
    }


def _render_report(rows: list[dict[str, Any]], summaries: dict[str, dict[str, Any]], seeds: list[int]) -> str:
    lines: list[str] = []
    lines.append("# Model sink matrix")
    lines.append("")
    lines.append("## Availability")
    lines.append("")
    lines.append("| Backend | Available locally | Reason |")
    lines.append("| --- | --- | --- |")
    for row in summarize_backend_availability():
        lines.append(
            f"| {row['backend']} | {'yes' if row['available'] else 'no'} | {row.get('reason') or ''} |"
        )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"Seeds: {', '.join(str(seed) for seed in seeds)}")
    lines.append("")
    lines.append("| Backend | Attempts | Tool reach rate | Tool success rate | Multi-turn success rate | Guardrail block rate | Predicate rate | Verified breach rate |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for backend, summary in summaries.items():
        lines.append(
            f"| {backend} | {summary['attempts']} | {summary['tool_reach_rate']:.2f} | {summary['tool_call_success_rate']:.2f} | "
            f"{summary['multi_turn_success_rate']:.2f} | {summary['guardrail_block_rate']:.2f} | {summary['predicate_rate']:.2f} | {summary['verified_breach_rate']:.2f} |"
        )
    lines.append("")
    lines.append("## Scenario details")
    lines.append("")
    lines.append("| Backend | Scenario | Seed | Target tool | Tool names | Cell hash | Predicates | Verified breach | Error |")
    lines.append("| --- | --- | ---: | --- | --- | --- | --- | --- | --- |")
    for row in rows:
        lines.append(
            f"| {row['backend']} | {row['scenario_id']} | {row['seed']} | {row.get('target_tool') or ''} | "
            f"{', '.join(row.get('tool_names', []))} | {row.get('cell_hash') or ''} | "
            f"{', '.join(row.get('predicate_names', []))} | {str(bool(row.get('verified_breach'))).lower()} | {row.get('error') or ''} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--seeds", type=str, default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    args = parser.parse_args()

    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    rows: list[dict[str, Any]] = []
    backend_names = [row["backend"] for row in summarize_backend_availability()]
    for backend_name in backend_names:
        for seed in seeds:
            for scenario in SINK_SCENARIOS:
                row = execute_scenario(backend_name, scenario, seed=seed, fixtures_dir=FIXTURES_DIR)
                row["probe_kind"] = "sink_matrix"
                rows.append(row)

    write_jsonl(args.out, rows)

    by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_backend[row["backend"]].append(row)
    summaries = {backend: _summarize(backend_rows) for backend, backend_rows in by_backend.items()}

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(rows, summaries, seeds), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(args.out), "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()

