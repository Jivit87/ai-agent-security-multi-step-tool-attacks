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
    FIXTURES_DIR,
    SINK_SCENARIOS,
    execute_scenario,
    summarize_backend_availability,
    write_jsonl,
)


DEFAULT_OUT = Path("experiments/phase15_model_sink_matrix.jsonl")
DEFAULT_REPORT = Path("docs/phase15_model_comparison.md")


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "attempts": 0,
            "selected_rate": 0.0,
            "executed_rate": 0.0,
            "guardrail_rate": 0.0,
            "predicate_rate": 0.0,
            "replay_rate": 0.0,
            "score": 0.0,
        }
    attempts = len(rows)
    return {
        "attempts": attempts,
        "selected_rate": sum(bool(row.get("tool_success")) for row in rows) / attempts,
        "executed_rate": sum(bool(row.get("tool_success")) for row in rows) / attempts,
        "guardrail_rate": sum(bool(row.get("guardrail_blocks")) for row in rows) / attempts,
        "predicate_rate": sum(bool(row.get("predicates")) for row in rows) / attempts,
        "replay_rate": sum(bool(row.get("replay_valid")) for row in rows) / attempts,
        "score": sum(float(row.get("score") or 0.0) for row in rows),
    }


def _render_report(rows: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> str:
    availability = {row["backend"]: row for row in summarize_backend_availability()}
    lines: list[str] = []
    lines.append("# Phase 15 model comparison")
    lines.append("")
    lines.append("| Backend | Model | Attempts | Selected | Executed | Guardrail | Predicate | Replay | Score |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for backend, summary in summaries.items():
        model = next((row["model"] for row in rows if row["backend"] == backend), backend)
        if not availability.get(backend, {}).get("available", False):
            lines.append(f"| {backend} | {model} | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |")
            continue
        lines.append(
            f"| {backend} | {model} | {summary['attempts']} | {summary['selected_rate']:.2f} | "
            f"{summary['executed_rate']:.2f} | {summary['guardrail_rate']:.2f} | {summary['predicate_rate']:.2f} | "
            f"{summary['replay_rate']:.2f} | {summary['score']:.2f} |"
        )
    lines.append("")
    lines.append("| Backend | Model | Sink | Selected | Executed | Guardrail | Predicate | Replay | Score | Error |")
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
        for scenario in SINK_SCENARIOS:
            row = execute_scenario(backend, scenario, seed=args.seed, fixtures_dir=FIXTURES_DIR)
            row["backend"] = backend
            row["model"] = model
            row["scenario"] = scenario.scenario_id
            row["tool_success"] = bool(row.get("tool_call_success"))
            rows.append(row)

    write_jsonl(args.out, rows)
    by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_backend[row["backend"]].append(row)
    summaries = {backend: _summarize(backend_rows) for backend, backend_rows in by_backend.items()}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(rows, summaries), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(args.out), "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()

