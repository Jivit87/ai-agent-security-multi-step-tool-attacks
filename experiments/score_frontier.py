from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FrontierEntry:
    entry_id: str
    score: float
    cell_hash: str
    replay_valid: bool
    unique_cells: int
    unique_mechanisms: int
    predicates: int
    severity_sum: int
    route_id: str
    mechanism_signature: str
    metadata: dict[str, Any] = field(default_factory=dict)


def dominates(left: FrontierEntry, right: FrontierEntry) -> bool:
    return (
        left.score >= right.score
        and left.unique_cells >= right.unique_cells
        and left.unique_mechanisms >= right.unique_mechanisms
        and int(left.replay_valid) >= int(right.replay_valid)
        and (
            left.score > right.score
            or left.unique_cells > right.unique_cells
            or left.unique_mechanisms > right.unique_mechanisms
            or int(left.replay_valid) > int(right.replay_valid)
        )
    )


class ScoreFrontier:
    def __init__(self) -> None:
        self._entries: list[FrontierEntry] = []

    def add(self, entry: FrontierEntry) -> bool:
        if any(dominates(existing, entry) for existing in self._entries):
            return False
        self._entries = [existing for existing in self._entries if not dominates(entry, existing)]
        self._entries.append(entry)
        self._entries.sort(key=lambda item: (item.score, item.unique_cells, item.unique_mechanisms, int(item.replay_valid)), reverse=True)
        return True

    def entries(self) -> list[FrontierEntry]:
        return list(self._entries)

    def to_rows(self) -> list[dict[str, Any]]:
        return [
            {
                "entry_id": entry.entry_id,
                "score": entry.score,
                "cell_hash": entry.cell_hash,
                "replay_valid": entry.replay_valid,
                "unique_cells": entry.unique_cells,
                "unique_mechanisms": entry.unique_mechanisms,
                "predicates": entry.predicates,
                "severity_sum": entry.severity_sum,
                "route_id": entry.route_id,
                "mechanism_signature": entry.mechanism_signature,
                "metadata": entry.metadata,
            }
            for entry in self._entries
        ]
