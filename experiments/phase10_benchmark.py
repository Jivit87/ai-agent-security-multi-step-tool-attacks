from __future__ import annotations

import argparse
import json
import hashlib
import statistics
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aicomp_sdk.scoring import score_attack, score_attack_raw

from experiments.agent_steering_benchmark import run_benchmark as run_prompt_benchmark
from experiments.backend_adapter import available_backend_specs
from experiments.fixture_router import build_fixture_route_library, enumerate_fixtures, select_best_fixture
from experiments.inspect_local_read_state import inspect_state
from experiments.predicate_backward_search import backward_search_predicates
from experiments.prefix_extension_search import run_prefix_extension_search
from experiments.route_composer import RouteComposer
from experiments.route_library import RouteFragment, RouteLibrary
from experiments.score_frontier import FrontierEntry, ScoreFrontier


DEFAULT_RESULTS = Path("experiments/phase10_results.jsonl")
DEFAULT_BENCHMARK = Path("experiments/phase10_benchmark.jsonl")
DEFAULT_REPORT = Path("docs/phase10_results.md")
DEFAULT_ROUTE_LIBRARY = Path("docs/route_library.md")
DEFAULT_FIXTURE_RESULTS = Path("docs/fixture_routing_results.md")
DEFAULT_PREDICATE_RESULTS = Path("docs/predicate_backward_search.md")
DEFAULT_FRONTIER = Path("docs/score_frontier.md")
DEFAULT_MODEL_LIMITED = Path("docs/model_limited_edges.md")


def _dump_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _metric_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    def _mechanism_signature(record: dict[str, Any]) -> str:
        if record.get("mechanism_signature"):
            return str(record["mechanism_signature"])
        payload = {
            "tool_sequence": record.get("tool_sequence", []),
            "sources": record.get("sources", record.get("source_sequence", [])),
            "predicate_names": record.get("predicate_names", [pred.get("predicate", "") for pred in record.get("predicates", [])]),
            "guardrail_blocks": record.get("guardrail_blocks", []),
            "family": record.get("family", record.get("mode", "")),
            "stage": record.get("stage", ""),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]

    def _replay_valid(record: dict[str, Any]) -> bool:
        if "replay_valid" in record:
            return bool(record["replay_valid"])
        if "failure_classification" in record:
            return record.get("failure_classification") == "REACHED"
        return True

    def _transition_success(record: dict[str, Any]) -> bool:
        if "transition_success" in record:
            return bool(record["transition_success"])
        if "failure_classification" in record:
            return record.get("failure_classification") == "REACHED"
        return bool(record.get("tool_sequence"))

    successful = [record for record in records if _replay_valid(record)]
    findings = [
        {
            "predicates": record.get("predicates", []),
            "score_cell_signature": {"hash": record.get("score_cell_hash") or record.get("cell_hash") or ""},
        }
        for record in successful
        if record.get("score_cell_hash") or record.get("cell_hash")
    ]
    raw_score = score_attack_raw(findings) if findings else 0.0
    normalized_score = score_attack(findings) if findings else 0.0
    return {
        "attempts": len(records),
        "replay_valid_rate": statistics.mean(1.0 if _replay_valid(record) else 0.0 for record in records) if records else 0.0,
        "transition_success_rate": statistics.mean(1.0 if _transition_success(record) else 0.0 for record in records) if records else 0.0,
        "unique_cells": len({record.get("cell_hash", "") for record in successful if record.get("cell_hash")}),
        "unique_mechanisms": len({_mechanism_signature(record) for record in successful if record.get("cell_hash") or record.get("score_cell_hash")}),
        "predicate_count": sum(len(record.get("predicates", [])) for record in successful),
        "severity_sum": sum(sum(int(pred.get("severity", 1)) for pred in record.get("predicates", [])) for record in successful),
        "raw_score": raw_score,
        "normalized_score": normalized_score,
        "tool_diversity": len({tool for record in successful for tool in record.get("tool_sequence", [])}),
        "deepest": max((len(record.get("tool_sequence", [])) for record in successful), default=0),
        "best_clean_event_count": max((int(record.get("clean_event_count", 0)) for record in successful), default=0),
    }


def _render_metric_table(title: str, rows: list[dict[str, Any]]) -> str:
    lines = [f"## {title}", "", "| Mode | Attempts | Replay valid rate | Transition success rate | Unique cells | Unique mechanisms | Predicates | Severity sum | Raw score | Normalized score | Deepest | Best clean events |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in rows:
        lines.append(
            f"| {row['mode']} | {row['attempts']} | {row['replay_valid_rate']:.2f} | {row['transition_success_rate']:.2f} | {row['unique_cells']} | {row['unique_mechanisms']} | {row['predicate_count']} | {row['severity_sum']} | {row['raw_score']:.2f} | {row['normalized_score']:.2f} | {row['deepest']} | {row['best_clean_event_count']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_fixture_table(records: list[dict[str, Any]]) -> str:
    lines = [
        "| Fixture | Categories | Local ref score | fs.read success | Replay valid | Cell | Mechanism | Result class |",
        "| --- | --- | ---: | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        lines.append(
            f"| {record['fixture_id']} | {', '.join(record['categories'])} | {record['local_reference_score']} | {record['fs_read_success']} | {record['replay_valid']} | {record['cell_hash']} | {record['mechanism_signature']} | {record['result_class']} |"
        )
    return "\n".join(lines)


def _render_route_library(library: RouteLibrary) -> str:
    lines = [
        "# Route library",
        "",
        "| Route | Entry | Tools | Result classes | Clean events | Taint | Predicates | Replay valid | Success rate | Cell | Mechanism |",
        "| --- | --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |",
    ]
    for fragment in library.rows():
        lines.append(
            f"| {fragment['route_id']} | {fragment['entry_condition']} | {fragment['tool_sequence']} | {fragment['result_classes']} | {fragment['clean_event_count']} | {fragment['taint_state']} | {fragment['predicates']} | {fragment['replay_valid']} | {fragment['success_rate']:.2f} | {fragment['cell_hash']} | {fragment['mechanism_signature']} |"
        )
    return "\n".join(lines)


def _render_predicate_report(plans: list[dict[str, Any]]) -> str:
    lines = [
        "# Predicate backward search",
        "",
        "| Predicate | Target tool | Candidate route | Transition success | Replay valid | Cell | Mechanism | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for plan in plans:
        lines.append(
            f"| {plan['predicate']} | {plan['target_tool']} | {plan['candidate_route_id']} | {plan['transition_success']} | {plan['replay_valid']} | {plan['cell_hash']} | {plan['mechanism_signature']} | {plan['notes']} |"
        )
    return "\n".join(lines)


def _frontier_from_records(mode: str, records: list[dict[str, Any]]) -> list[FrontierEntry]:
    frontier = ScoreFrontier()
    for idx, record in enumerate(records):
        cell_hash = record.get("score_cell_hash") or record.get("cell_hash") or ""
        score = float(sum(int(pred.get("severity", 1)) for pred in record.get("predicates", [])) + (2 if cell_hash else 0))
        frontier.add(
            FrontierEntry(
                entry_id=f"{mode}:{idx}",
                score=score,
                cell_hash=cell_hash,
                replay_valid=bool(record.get("replay_valid", False)),
                unique_cells=1 if cell_hash else 0,
                unique_mechanisms=1 if record.get("mechanism_signature") else 0,
                predicates=len(record.get("predicates", [])),
                severity_sum=sum(int(pred.get("severity", 1)) for pred in record.get("predicates", [])),
                route_id=str(record.get("candidate_id") or record.get("prompt_id") or record.get("fixture_id") or ""),
                mechanism_signature=str(record.get("mechanism_signature", "")),
                metadata={"mode": mode, "prompt": record.get("prompt", "")},
            )
        )
    return frontier.entries()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backend", type=str, default="deterministic")
    parser.add_argument("--seeds", type=str, default="123,456")
    parser.add_argument("--budget-s", type=float, default=120.0)
    parser.add_argument("--max-tool-hops", type=int, default=4)
    args = parser.parse_args()

    seeds = tuple(int(item) for item in args.seeds.split(",") if item.strip())
    backend = next(spec for spec in available_backend_specs() if spec.name == args.backend)

    phase6_records = run_prompt_benchmark(backends=[backend], seeds=seeds, max_tool_hops=4)
    phase9_attempts, phase9_summary, phase9_prefix_rows = run_prefix_extension_search(
        backend=backend,
        seeds=seeds,
        budget_s=args.budget_s,
        selection_policy="depth_first",
        desired_tool="fs.read",
        include_prompt_bank=True,
        include_edge_policy=True,
        include_mutation=True,
        include_explicit=True,
    )
    phase9_records = [
        {
            "mode": "phase9_prefix_extension",
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
            "mechanism_signature": attempt.mechanism_signature,
            "replay_valid": attempt.replay_valid,
            "transition_success": attempt.transition_success,
            "clean_event_count": attempt.clean_event_count,
            "egress_count": attempt.egress_count,
            "depth": attempt.depth,
        }
        for attempt in phase9_attempts
    ]

    local_read_state = inspect_state(backend=backend.name, seed=seeds[0] if seeds else 123, out=Path("experiments/local_read_state.json"))

    fixture_ids = ["page_1002"]
    for row in enumerate_fixtures(limit=11):
        if row["fixture_id"] not in fixture_ids:
            fixture_ids.append(row["fixture_id"])
    fixture_library, fixture_records = build_fixture_route_library(
        backend=backend,
        seed=seeds[0] if seeds else 123,
        page_ids=fixture_ids,
        max_tool_hops=args.max_tool_hops,
    )
    best_fixture = select_best_fixture(fixture_records)

    composer = RouteComposer(route_library=fixture_library)
    composed_records: list[dict[str, Any]] = []
    if best_fixture and best_fixture.route is not None:
        for desired_tool in ("http.post", "email.send"):
            for record in composer.extend(
                backend=backend,
                seed=seeds[0] if seeds else 123,
                fragment=best_fixture.route,
                desired_tool=desired_tool,
                include_prompt_bank=True,
                include_edge_policy=True,
                include_mutation=True,
                include_explicit=True,
                max_tool_hops=args.max_tool_hops,
            ):
                composed_records.append(
                    {
                        "mode": f"route_composition::{desired_tool}",
                        "base_route_id": record.base_route_id,
                        "candidate_id": record.candidate_id,
                        "desired_tool": record.desired_tool,
                        "prompt": record.prompt,
                        "transition_success": record.transition_success,
                        "replay_valid": record.replay_valid,
                        "cell_hash": record.cell_hash,
                        "mechanism_signature": record.mechanism_signature,
                        "predicates": record.predicates,
                        "tool_sequence": record.route.tool_sequence,
                        "source_sequence": record.route.source_sequence,
                        "score_cell_hash": record.route.cell_hash,
                        "clean_event_count": record.route.clean_event_count,
                    }
                )

    backward_plans = backward_search_predicates(
        backend=backend,
        seed=seeds[0] if seeds else 123,
        library=fixture_library,
        composer=composer,
        max_tool_hops=args.max_tool_hops,
    )
    backward_records = [
        {
            "mode": "predicate_backward_search",
            "predicate": plan.predicate,
            "target_tool": plan.target_tool,
            "candidate_route_id": plan.candidate_route_id,
            "candidate_score": plan.candidate_score,
            "transition_success": plan.transition_success,
            "replay_valid": plan.replay_valid,
            "cell_hash": plan.cell_hash,
            "mechanism_signature": plan.mechanism_signature,
            "notes": plan.notes,
            "required_state": plan.required_state,
        }
        for plan in backward_plans
    ]

    records: list[dict[str, Any]] = []
    records.extend({"mode": "phase6_prompt_bank", **record} for record in phase6_records)
    records.extend({"mode": "phase9_prefix_extension", **record} for record in phase9_records)
    records.extend({"mode": "fixture_route", **record.to_row(), "route_id": record.route.route_id if record.route else ""} for record in fixture_records)
    records.extend(composed_records)
    records.extend(backward_records)

    _dump_jsonl(args.results, list(records))

    summaries = [
        {"mode": "phase6_prompt_bank", **_metric_records(phase6_records), "best_depth": max((len(record.get("tool_sequence", [])) for record in phase6_records), default=0)},
        {"mode": "phase9_prefix_extension", **_metric_records(phase9_records), "best_depth": phase9_summary.get("best_depth", 0)},
        {"mode": "fixture_route", **_metric_records([record.to_row() for record in fixture_records]), "best_depth": max((len(record.route.tool_sequence) if record.route else 0 for record in fixture_records), default=0)},
        {"mode": "route_composition", **_metric_records(composed_records)},
        {"mode": "predicate_backward_search", **_metric_records(backward_records)},
    ]

    frontier = ScoreFrontier()
    for mode, subset in (
        ("phase6_prompt_bank", phase6_records),
        ("phase9_prefix_extension", phase9_records),
        ("fixture_route", [record.to_row() | {"candidate_id": record.route.route_id if record.route else ""} for record in fixture_records]),
        ("route_composition", composed_records),
        ("predicate_backward_search", backward_records),
    ):
        for entry in _frontier_from_records(mode, subset):
            frontier.add(entry)

    benchmark_rows = [
        {
            "mode": row["mode"],
            "attempts": row["attempts"],
            "replay_valid_rate": row["replay_valid_rate"],
            "transition_success_rate": row["transition_success_rate"],
            "unique_cells": row["unique_cells"],
            "unique_mechanisms": row["unique_mechanisms"],
            "predicate_count": row["predicate_count"],
            "severity_sum": row["severity_sum"],
            "raw_score": row["raw_score"],
            "normalized_score": row["normalized_score"],
            "tool_diversity": row["tool_diversity"],
            "deepest": row["deepest"],
            "best_clean_event_count": row["best_clean_event_count"],
        }
        for row in summaries
    ]
    _dump_jsonl(args.benchmark, benchmark_rows)

    report_lines = [
        "# Phase 10 results",
        "",
        "## Verified local-read snapshot",
        "",
        f"- page id: {local_read_state['page_id']}",
        f"- stage A: {local_read_state['stage_a']}",
        f"- follow-up: {local_read_state['followup']}",
        f"- tool sequence: {' → '.join(local_read_state['tool_sequence'])}",
        f"- state taint label: {local_read_state['taint_label']}",
        f"- clean event count: {local_read_state['clean_event_count']}",
        f"- replay valid: {local_read_state['replay_valid']}",
        f"- predicates: {', '.join(pred['predicate'] for pred in local_read_state['predicates']) or '—'}",
        "",
        "## Benchmark summary",
        "",
        _render_metric_table("Summary", summaries),
        "## Fixture routing",
        "",
        _render_fixture_table([record.to_row() for record in fixture_records]),
        "",
        _render_route_library(fixture_library),
        "",
        _render_predicate_report(backward_records),
        "",
        "## Score frontier",
        "",
        "| Entry | Score | Cell | Replay valid | Unique cells | Unique mechanisms | Predicates | Severity sum | Route | Mechanism |",
        "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for entry in frontier.entries():
        report_lines.append(
            f"| {entry.entry_id} | {entry.score:.2f} | {entry.cell_hash} | {entry.replay_valid} | {entry.unique_cells} | {entry.unique_mechanisms} | {entry.predicates} | {entry.severity_sum} | {entry.route_id} | {entry.mechanism_signature} |"
        )
    report_lines.extend(
        [
            "",
        "## Notes",
        "",
        f"- Best fixture: {best_fixture.fixture_id if best_fixture else '—'}",
        f"- Best fixture categories: {', '.join(best_fixture.categories) if best_fixture else '—'}",
        f"- Best fixture fs.read success: {best_fixture.fs_read_success if best_fixture else False}",
        f"- Route composition candidates: {len(composed_records)}",
        f"- Backward search plans: {len(backward_records)}",
        "",
        "## Model-limited edges",
        "",
        "- `web.open -> fs.read` is fixture-sensitive, not globally model-limited.",
        "- `email.read -> fs.read` remains model-limited in deterministic runs.",
        "- `clean -> email.send` remains model-limited in deterministic runs.",
        "- `clean -> http.post` remains a useful secondary route.",
    ]
    )
    _write_text(args.report, "\n".join(report_lines) + "\n")

    _write_text(DEFAULT_ROUTE_LIBRARY, _render_route_library(fixture_library) + "\n")
    _write_text(DEFAULT_FIXTURE_RESULTS, _render_fixture_table([record.to_row() for record in fixture_records]) + "\n")
    _write_text(DEFAULT_PREDICATE_RESULTS, _render_predicate_report(backward_records) + "\n")
    _write_text(
        DEFAULT_FRONTIER,
        "\n".join(
            [
                "# Score frontier",
                "",
                "| Entry | Score | Cell | Replay valid | Unique cells | Unique mechanisms | Predicates | Severity sum | Route | Mechanism |",
                "| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
            ]
            + [
                f"| {entry.entry_id} | {entry.score:.2f} | {entry.cell_hash} | {entry.replay_valid} | {entry.unique_cells} | {entry.unique_mechanisms} | {entry.predicates} | {entry.severity_sum} | {entry.route_id} | {entry.mechanism_signature} |"
                for entry in frontier.entries()
            ]
        )
        + "\n",
    )

    _write_text(
        DEFAULT_MODEL_LIMITED,
        "\n".join(
            [
                "# Model-limited edges",
                "",
                "- `web.open -> fs.read` is fixture-sensitive, not globally model-limited.",
                "- `email.read -> fs.read` remains model-limited in deterministic runs.",
                "- `clean -> email.send` remains model-limited in deterministic runs.",
                "- `clean -> http.post` remains a useful secondary route.",
            ]
        )
        + "\n",
    )

    print(f"wrote {len(list(records))} records to {args.results}")
    print(f"wrote benchmark summary to {args.benchmark}")
    print(f"wrote report to {args.report}")


if __name__ == "__main__":
    main()
