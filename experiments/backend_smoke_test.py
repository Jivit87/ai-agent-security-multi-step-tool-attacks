from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.backend_validation_common import (
    DEFAULT_SEEDS,
    FIXTURES_DIR,
    SMOKE_SCENARIOS,
    execute_scenario,
    summarize_backend_availability,
    write_jsonl,
)


DEFAULT_OUT = Path("experiments/backend_smoke_test.jsonl")
DEFAULT_REPORT = Path("docs/backend_inventory.md")


def _render_report(rows: list[dict[str, Any]], availability_rows: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# Backend inventory")
    lines.append("")
    lines.append("## Local availability")
    lines.append("")
    lines.append("| Backend | Available locally | Reason |")
    lines.append("| --- | --- | --- |")
    for row in availability_rows:
        lines.append(
            f"| {row['backend']} | {'yes' if row['available'] else 'no'} | {row.get('reason') or ''} |"
        )
    lines.append("")
    lines.append("## Smoke-test summary")
    lines.append("")
    lines.append("| Backend | Scenario | Seed | Tool calls | Target tool | Tool call success | Multi-turn success | Predicate count | Cell hash | Error |")
    lines.append("| --- | --- | ---: | ---: | --- | --- | --- | ---: | --- | --- |")
    for row in rows:
        lines.append(
            f"| {row['backend']} | {row['scenario_id']} | {row['seed']} | {row.get('tool_call_count', 0)} | "
            f"{row.get('target_tool') or ''} | {str(bool(row.get('tool_call_success'))).lower()} | "
            f"{str(bool(row.get('multi_turn_success'))).lower()} | {len(row.get('predicates', []))} | "
            f"{row.get('cell_hash') or ''} | {row.get('error') or ''} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- This workspace currently runs the deterministic backend only; the other backends are present in source but unavailable locally."
    )
    lines.append(
        "- GPT-OSS and Gemma backends depend on `transformers` in the local SDK path, while the Kaggle wrapper uses GGUF servers for the competition runtime."
    )
    lines.append(
        "- OpenAI backend requires `OPENAI_API_KEY` and the `openai` package."
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
    availability_rows = summarize_backend_availability()
    backend_names = [row["backend"] for row in availability_rows]

    for backend_name in backend_names:
        for seed in seeds:
            for scenario in SMOKE_SCENARIOS:
                row = execute_scenario(backend_name, scenario, seed=seed, fixtures_dir=FIXTURES_DIR)
                row["probe_kind"] = "smoke"
                rows.append(row)

    write_jsonl(args.out, rows)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(_render_report(rows, availability_rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(args.out), "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()

