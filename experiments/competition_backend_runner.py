from __future__ import annotations

import argparse
import json
import os
import sys
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


DEFAULT_OUT = Path("experiments/competition_backend_runner.jsonl")


def _scenario_map() -> dict[str, Any]:
    scenarios = {scenario.scenario_id: scenario for scenario in SINK_SCENARIOS}
    return scenarios


def _run_one(backend: str, model: str, scenario_id: str, seed: int) -> dict[str, Any]:
    scenario = _scenario_map().get(scenario_id)
    if scenario is None:
        raise SystemExit(f"Unknown scenario: {scenario_id}")
    row = execute_scenario(backend, scenario, seed=seed, fixtures_dir=FIXTURES_DIR)
    row["model"] = model
    row["backend"] = backend
    row["scenario"] = scenario.scenario_id
    row["tool_success"] = bool(row.get("tool_call_success"))
    row["guardrail_blocks"] = row.get("guardrail_blocks", [])
    row["predicate_hits"] = row.get("predicate_names", [])
    row["score"] = row.get("verified_score", 0.0)
    row["latency"] = row.get("elapsed_s", 0.0)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--scenario", default="http_post")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    model = args.model or args.backend
    row = _run_one(args.backend, model, args.scenario, args.seed)
    write_jsonl(args.out, [row])
    print(json.dumps(row, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

