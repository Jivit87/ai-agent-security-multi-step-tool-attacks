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

from experiments.backend_validation_common import (
    DEFAULT_SEEDS,
    FIXTURES_DIR,
    SMOKE_SCENARIOS,
    SINK_SCENARIOS,
    execute_scenario,
    summarize_backend_availability,
    write_jsonl,
)


DEFAULT_OUT = Path("experiments/phase13_backend_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/phase13_results.md")
DEFAULT_BACKEND_COMPARISON = Path("docs/backend_comparison.md")
DEFAULT_RUNTIME_PARITY = Path("docs/runtime_parity.md")
DEFAULT_COMPETITION_REQS = Path("docs/competition_runtime_requirements.md")
DEFAULT_MODEL_LIMITED = Path("docs/model_limited_edges.md")


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "attempts": 0,
            "tool_call_success_rate": 0.0,
            "multi_turn_success_rate": 0.0,
            "http_post_rate": 0.0,
            "email_send_rate": 0.0,
            "avg_tool_calls": 0.0,
            "unique_cells": 0,
            "unique_mechanisms": 0,
            "predicate_count": 0,
            "verified_breach_rate": 0.0,
            "verified_score": 0.0,
            "mean_latency_s": 0.0,
            "median_latency_s": 0.0,
        }

    attempts = len(rows)
    latencies = [float(row.get("elapsed_s") or 0.0) for row in rows]
    return {
        "attempts": attempts,
        "tool_call_success_rate": sum(bool(row.get("tool_call_success")) for row in rows) / attempts,
        "multi_turn_success_rate": sum(bool(row.get("multi_turn_success")) for row in rows) / attempts,
        "http_post_rate": sum("http.post" in row.get("tool_names", []) for row in rows) / attempts,
        "email_send_rate": sum("email.send" in row.get("tool_names", []) for row in rows) / attempts,
        "avg_tool_calls": sum(int(row.get("tool_call_count") or 0) for row in rows) / attempts,
        "unique_cells": len({row.get("cell_hash") for row in rows if row.get("cell_hash")}),
        "unique_mechanisms": len({tuple(row.get("tool_names", [])) for row in rows}),
        "predicate_count": sum(len(row.get("predicates", [])) for row in rows),
        "verified_breach_rate": sum(bool(row.get("verified_breach")) for row in rows) / attempts,
        "verified_score": 0.0,
        "mean_latency_s": statistics.mean(latencies),
        "median_latency_s": statistics.median(latencies),
    }


def _render_backend_comparison(availability_rows: list[dict[str, Any]], summaries: dict[str, dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("# Backend comparison")
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
    lines.append("## Comparison")
    lines.append("")
    lines.append("| Backend | Attempts | Tool success | Multi-turn success | http.post | email.send | Unique cells | Unique mechanisms | Predicates | Verified breach | Verified score | Mean latency (s) |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for backend, summary in summaries.items():
        lines.append(
            f"| {backend} | {summary['attempts']} | {summary['tool_call_success_rate']:.2f} | {summary['multi_turn_success_rate']:.2f} | "
            f"{summary['http_post_rate']:.2f} | {summary['email_send_rate']:.2f} | {summary['unique_cells']} | {summary['unique_mechanisms']} | "
            f"{summary['predicate_count']} | {summary['verified_breach_rate']:.2f} | {summary['verified_score']:.2f} | {summary['mean_latency_s']:.3f} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- The current workspace can only execute the deterministic backend. GPT-OSS and Gemma family backends are source-present but not locally runnable because their runtime dependencies are missing."
    )
    lines.append(
        "- The competition runtime uses the Kaggle gateway and model servers, which are distinct from the local HF/OpenAI code paths."
    )
    return "\n".join(lines)


def _render_runtime_parity() -> str:
    return "\n".join(
        [
            "# Runtime parity",
            "",
            "## What matches between local and competition code",
            "",
            "- Submission contract: `AttackAlgorithm.run(env, config) -> list[AttackCandidate]`.",
            "- Replay validation: evaluator replays returned candidates in a fresh environment.",
            "- Attack replay hop limit: evaluator replay uses `max_tool_hops = 4`.",
            "",
            "## What differs",
            "",
            "- Local SDK backends are Python implementations (`deterministic`, `openai`, `gpt_oss`, `gemma`, `gemma_4`).",
            "- Competition runtime routes through `kaggle_evaluation/jed_attack_134815/*` and launches Kaggle model servers.",
            "- GPT-OSS/Gemma competition backends are GGUF/llama.cpp servers, not the local HF `transformers` implementations.",
            "- `KAGGLE_IS_COMPETITION_RERUN=1` switches the gateway/inference servers into serving mode.",
            "",
            "## Local parity status",
            "",
            "- Deterministic backend: fully runnable locally.",
            "- GPT-OSS backend: not runnable locally in this workspace (`transformers` missing).",
            "- Gemma backend: not runnable locally in this workspace (`transformers` missing).",
            "- Gemma 4 backend: not runnable locally in this workspace (`transformers` missing, and the Kaggle runtime is a GGUF/llama.cpp path).",
        ]
    )


def _render_competition_requirements() -> str:
    return "\n".join(
        [
            "# Competition runtime requirements",
            "",
            "## Submission contract",
            "",
            "- Provide `attack.py` with `AttackAlgorithm` inheriting `AttackAlgorithmBase`.",
            "- `run(env, config)` must return `list[AttackCandidate]` with replayable `user_messages` only.",
            "",
            "## Runtime knobs from source",
            "",
            "- Local evaluation CLI defaults attack/defense budget to `1800s`.",
            "- Kaggle gateway uses `DEFAULT_BUDGET_S = 8750.0` for the hosted run.",
            "- Replays are validated with `max_tool_hops = 4`.",
            "- Search-side `AttackRunConfig.max_tool_hops` defaults to `8`.",
            "",
            "## Model/backend configuration",
            "",
            "- `AICOMP_MODEL_NAMES` defaults to `gpt_oss,gemma` in the Kaggle gateway.",
            "- `GPT_OSS_GGUF_REPO` / `GPT_OSS_GGUF_FILE` / `GPT_OSS_MODEL_PATH` configure the GPT-OSS GGUF server.",
            "- `GEMMA_GGUF_REPO` / `GEMMA_GGUF_FILE` / `GEMMA_MODEL_PATH` configure the Gemma GGUF server.",
            "- `KAGGLE_IS_COMPETITION_RERUN=1` enables Kaggle serving mode.",
            "",
            "## Local dependency gap",
            "",
            "- This workspace does not currently have `transformers`, `openai`, or the Kaggle GGUF runtime packages required to run the model backends locally.",
            "- Therefore backend validation here is limited to source inspection and the deterministic agent.",
        ]
    )


def _render_model_limited(rows: list[dict[str, Any]]) -> str:
    by_backend: dict[str, dict[str, Any]] = {}
    for row in rows:
        backend = row["backend"]
        by_backend.setdefault(backend, {})
        by_backend[backend][row["scenario_id"]] = row

    lines: list[str] = []
    lines.append("# Model-limited edges")
    lines.append("")
    lines.append("| Backend | Edge | Status | Evidence |")
    lines.append("| --- | --- | --- | --- |")
    deterministic = by_backend.get("deterministic", {})
    if deterministic:
        email_row = deterministic.get("email_send")
        http_row = deterministic.get("http_post")
        lines.append(
            f"| deterministic | clean -> email.send | MODEL_LIMITED | {email_row.get('error') if email_row else 'not run'} |"
        )
        lines.append(
            f"| deterministic | clean -> http.post | REACHABLE_BUT_UNSCORED | {http_row.get('cell_hash') if http_row else 'not run'} |"
        )
    for backend in ("openai", "gpt_oss", "gemma", "gemma_4"):
        lines.append(
            f"| {backend} | backend availability | UNAVAILABLE_LOCALLY | {next((r.get('reason') for r in summarize_backend_availability() if r['backend'] == backend), '')} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Backend-specific labels are used instead of a single global `MODEL_LIMITED` label.")
    lines.append("- A backend that is unavailable locally is not assumed to be impossible in the competition runtime.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backend-comparison", type=Path, default=DEFAULT_BACKEND_COMPARISON)
    parser.add_argument("--runtime-parity", type=Path, default=DEFAULT_RUNTIME_PARITY)
    parser.add_argument("--competition-requirements", type=Path, default=DEFAULT_COMPETITION_REQS)
    parser.add_argument("--model-limited", type=Path, default=DEFAULT_MODEL_LIMITED)
    parser.add_argument("--seeds", type=str, default=",".join(str(seed) for seed in DEFAULT_SEEDS))
    args = parser.parse_args()

    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    availability_rows = summarize_backend_availability()
    backend_names = [row["backend"] for row in availability_rows]

    rows: list[dict[str, Any]] = []
    for backend_name in backend_names:
        for seed in seeds:
            for scenario in list(SMOKE_SCENARIOS) + list(SINK_SCENARIOS):
                row = execute_scenario(backend_name, scenario, seed=seed, fixtures_dir=FIXTURES_DIR)
                row["probe_kind"] = "phase13_backend_benchmark"
                rows.append(row)

    write_jsonl(args.out, rows)

    by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_backend[row["backend"]].append(row)
    summaries = {backend: _summarize(backend_rows) for backend, backend_rows in by_backend.items()}

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        "\n".join(
            [
                "# Phase 13 results",
                "",
                "## Summary",
                "",
                "| Backend | Attempts | Tool success | Multi-turn success | http.post | email.send | Unique cells | Unique mechanisms | Predicates | Verified breach | Verified score | Mean latency (s) | Median latency (s) |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
            + [
                f"| {backend} | {summary['attempts']} | {summary['tool_call_success_rate']:.2f} | {summary['multi_turn_success_rate']:.2f} | "
                f"{summary['http_post_rate']:.2f} | {summary['email_send_rate']:.2f} | {summary['unique_cells']} | {summary['unique_mechanisms']} | "
                f"{summary['predicate_count']} | {summary['verified_breach_rate']:.2f} | {summary['verified_score']:.2f} | {summary['mean_latency_s']:.3f} | {summary['median_latency_s']:.3f} |"
                for backend, summary in summaries.items()
            ]
            + [
                "",
                "## Interpretation",
                "",
                "- This workspace can only validate the deterministic backend locally.",
                "- GPT-OSS and Gemma-family backends are source-present but not runnable here because the required runtime packages are absent.",
                "- The next phase should be executed in the official Kaggle runtime if the goal is to validate those backends against the real competition model servers.",
            ]
        ),
        encoding="utf-8",
    )

    args.backend_comparison.parent.mkdir(parents=True, exist_ok=True)
    args.backend_comparison.write_text(_render_backend_comparison(availability_rows, summaries), encoding="utf-8")
    args.runtime_parity.parent.mkdir(parents=True, exist_ok=True)
    args.runtime_parity.write_text(_render_runtime_parity(), encoding="utf-8")
    args.competition_requirements.parent.mkdir(parents=True, exist_ok=True)
    args.competition_requirements.write_text(_render_competition_requirements(), encoding="utf-8")
    args.model_limited.parent.mkdir(parents=True, exist_ok=True)
    args.model_limited.write_text(_render_model_limited(rows), encoding="utf-8")
    print(json.dumps({"rows": len(rows), "out": str(args.out), "report": str(args.report)}, indent=2))


if __name__ == "__main__":
    main()
