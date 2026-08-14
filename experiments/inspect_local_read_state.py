from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aicomp_sdk.core.cells import cell_signature
from aicomp_sdk.core.predicates import eval_predicates

from experiments.backend_adapter import available_backend_specs
from experiments.route_library import state_snapshot, taint_label
from experiments.web_open_to_fs_read import _build_web_open_prefix


DEFAULT_OUT = Path("experiments/local_read_state.json")


def _dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def inspect_state(*, backend: str = "deterministic", seed: int = 123, out: Path = DEFAULT_OUT) -> dict[str, Any]:
    spec = next(spec for spec in available_backend_specs() if spec.name == backend)
    prefix = _build_web_open_prefix(spec, seed)
    trace = prefix["trace_2"]
    state = prefix["summary"]["state"]
    predicates = eval_predicates(trace)
    sig = cell_signature(trace.get("tool_events", []), egress_data=trace.get("egress", []), user_messages=trace.get("user_messages", []))
    payload = {
        "backend": backend,
        "seed": seed,
        "page_id": prefix["target_page"],
        "stage_a": prefix["stage_a"],
        "followup": prefix["followup"],
        "tool_sequence": prefix["summary"]["tool_sequence"],
        "source_sequence": prefix["summary"]["source_sequence"],
        "result_class": prefix["summary"]["last_result_class"],
        "state": state_snapshot(state),
        "taint_label": taint_label(state),
        "clean_event_count": state.clean_event_count,
        "predicates": [
            {
                "predicate": pred["predicate"],
                "severity": pred["severity"],
                "evidence": pred.get("evidence", {}),
            }
            for pred in predicates
        ],
        "cell_signature": sig,
        "replay_valid": prefix["prefix"].replay_valid,
    }
    _dump_json(out, payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", type=str, default="deterministic")
    parser.add_argument("--seed", type=int, default=123)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = inspect_state(backend=args.backend, seed=args.seed, out=args.out)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
