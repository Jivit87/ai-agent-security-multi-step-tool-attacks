from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.backend_validation_common import (
    FIXTURES_DIR,
    SMOKE_SCENARIOS,
    SINK_SCENARIOS,
    execute_scenario,
    summarize_backend_availability,
    write_jsonl,
)


DEFAULT_OUT = Path("experiments/phase15_competition_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/phase15_results.md")


def _render_report(rows: list[dict[str, Any]]) -> str:
    availability = {row["backend"]: row for row in summarize_backend_availability()}
    lines: list[str] = []
    lines.append("# Phase 15 results")
    lines.append("")
    lines.append("| Backend | Model | Scenario | Selected | Executed | Guardrail | Predicate | Replay | Score | Error |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |")
    for row in rows:
        if not availability.get(row["backend"], {}).get("available", False):
            lines.append(
                f"| {row['backend']} | {row['model']} | {row['scenario']} | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | {row.get('error') or ''} |"
            )
            continue
        lines.append(
            f"| {row['backend']} | {row['model']} | {row['scenario']} | "
            f"{str(bool(row.get('tool_success'))).lower()} | {str(bool(row.get('tool_success'))).lower()} | "
            f"{', '.join(row.get('guardrail_blocks', []))} | {', '.join(row.get('predicate_names', []))} | "
            f"{str(bool(row.get('replay_valid'))).lower()} | {float(row.get('score') or 0.0):.2f} | {row.get('error') or ''} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    backends = [args.backend] if args.backend else [row["backend"] for row in summarize_backend_availability()]
    rows: list[dict[str, Any]] = []
    for backend in backends:
        model = args.model or backend
        for scenario in list(SMOKE_SCENARIOS) + list(SINK_SCENARIOS):
            row = execute_scenario(backend, scenario, seed=args.seed, fixtures_dir=FIXTURES_DIR)
            row["backend"] = backend
            row["model"] = model
            row["scenario"] = scenario.scenario_id
            row["tool_success"] = bool(row.get("tool_call_success"))
            rows.append(row)

    write_jsonl(args.out, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(args.out), "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()

