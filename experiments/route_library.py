from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from experiments.security_state import SecurityState


@dataclass
class RouteFragment:
    route_id: str
    entry_condition: str
    user_messages: list[str]
    tool_sequence: list[str]
    result_classes: list[str]
    state_sequence: list[str]
    clean_event_count: int
    taint_state: str
    predicates: list[str]
    cell_hash: str
    mechanism_signature: str
    replay_valid: bool
    replay_count: int
    success_rate: float
    required_state: dict[str, Any] = field(default_factory=dict)
    resulting_state: dict[str, Any] = field(default_factory=dict)
    source_sequence: list[str] = field(default_factory=list)
    notes: str = ""
    snapshot: Any | None = field(default=None, repr=False, compare=False)

    def short_row(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "entry_condition": self.entry_condition,
            "tool_sequence": " → ".join(self.tool_sequence),
            "result_classes": " → ".join(self.result_classes),
            "clean_event_count": self.clean_event_count,
            "taint_state": self.taint_state,
            "predicates": ",".join(self.predicates),
            "cell_hash": self.cell_hash,
            "mechanism_signature": self.mechanism_signature,
            "replay_valid": self.replay_valid,
            "replay_count": self.replay_count,
            "success_rate": self.success_rate,
            "notes": self.notes,
        }

    def to_jsonable(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("snapshot", None)
        return data


class RouteLibrary:
    def __init__(self, fragments: list[RouteFragment] | None = None) -> None:
        self._fragments: list[RouteFragment] = []
        if fragments:
            for fragment in fragments:
                self.add(fragment)

    def add(self, fragment: RouteFragment) -> None:
        self._fragments = [existing for existing in self._fragments if existing.route_id != fragment.route_id]
        self._fragments.append(fragment)
        self._fragments.sort(key=lambda item: (item.success_rate, item.clean_event_count, item.route_id), reverse=True)

    def fragments(self) -> list[RouteFragment]:
        return list(self._fragments)

    def rows(self) -> list[dict[str, Any]]:
        return [fragment.short_row() for fragment in self._fragments]

    def best(self, *, prefix: str | None = None) -> RouteFragment | None:
        candidates = self._fragments
        if prefix is not None:
            candidates = [fragment for fragment in candidates if fragment.route_id.startswith(prefix)]
        return candidates[0] if candidates else None


def taint_label(state: SecurityState) -> str:
    if state.taint_active and state.web_recent and state.email_recent:
        return "TAINTED_MIXED"
    if state.taint_active and state.web_recent:
        return "TAINTED_WEB"
    if state.taint_active and state.email_recent:
        return "TAINTED_EMAIL"
    if state.taint_active:
        return "TAINTED"
    return "CLEAN"


def state_snapshot(state: SecurityState) -> dict[str, Any]:
    return {
        "recent_sources": list(state.recent_sources),
        "recent_tools": list(state.recent_tools),
        "last_tool": state.last_tool,
        "last_tool_ok": state.last_tool_ok,
        "episode_depth": state.episode_depth,
        "web_recent": state.web_recent,
        "email_recent": state.email_recent,
        "taint_active": state.taint_active,
        "clean_event_count": state.clean_event_count,
        "secret_read": state.secret_read,
        "egress_count": state.egress_count,
        "predicate_names": list(state.predicate_names),
        "guardrail_blocked": state.guardrail_blocked,
        "refusal": state.refusal,
    }


def route_fragment_from_summary(
    *,
    route_id: str,
    entry_condition: str,
    user_messages: list[str],
    tool_sequence: list[str],
    result_classes: list[str],
    state_sequence: list[str],
    state: SecurityState,
    predicates: list[dict[str, Any]],
    cell_hash: str,
    mechanism_signature: str,
    replay_valid: bool,
    replay_count: int,
    success_rate: float,
    source_sequence: list[str] | None = None,
    notes: str = "",
    snapshot: Any | None = None,
) -> RouteFragment:
    return RouteFragment(
        route_id=route_id,
        entry_condition=entry_condition,
        user_messages=list(user_messages),
        tool_sequence=list(tool_sequence),
        result_classes=list(result_classes),
        state_sequence=list(state_sequence),
        clean_event_count=state.clean_event_count,
        taint_state=taint_label(state),
        predicates=[pred.get("predicate", "") for pred in predicates if pred.get("predicate")],
        cell_hash=cell_hash,
        mechanism_signature=mechanism_signature,
        replay_valid=replay_valid,
        replay_count=replay_count,
        success_rate=success_rate,
        required_state=state_snapshot(state),
        resulting_state=state_snapshot(state),
        source_sequence=list(source_sequence or []),
        notes=notes,
        snapshot=snapshot,
    )


def compose_fragments(prefix: RouteFragment, suffix: RouteFragment, *, route_id: str | None = None) -> RouteFragment | None:
    """Compose two replay-valid fragments when their state preconditions are compatible."""
    if not prefix.replay_valid or not suffix.replay_valid:
        return None

    if suffix.entry_condition not in {prefix.taint_state, "ANY", prefix.route_id, prefix.result_classes[-1] if prefix.result_classes else ""}:
        if suffix.entry_condition and suffix.entry_condition != prefix.route_id:
            return None

    combined_messages = list(prefix.user_messages) + list(suffix.user_messages)
    combined_tools = list(prefix.tool_sequence) + list(suffix.tool_sequence)
    combined_results = list(prefix.result_classes) + list(suffix.result_classes)
    combined_states = list(prefix.state_sequence) + list(suffix.state_sequence)
    combined_sources = list(prefix.source_sequence) + list(suffix.source_sequence)
    combined_predicates = list(dict.fromkeys(prefix.predicates + suffix.predicates))

    return RouteFragment(
        route_id=route_id or f"{prefix.route_id}::{suffix.route_id}",
        entry_condition=prefix.entry_condition,
        user_messages=combined_messages,
        tool_sequence=combined_tools,
        result_classes=combined_results,
        state_sequence=combined_states,
        clean_event_count=max(prefix.clean_event_count, suffix.clean_event_count),
        taint_state=suffix.taint_state,
        predicates=combined_predicates,
        cell_hash=suffix.cell_hash,
        mechanism_signature="::".join([prefix.mechanism_signature, suffix.mechanism_signature]).strip(":"),
        replay_valid=prefix.replay_valid and suffix.replay_valid,
        replay_count=min(prefix.replay_count, suffix.replay_count),
        success_rate=min(prefix.success_rate, suffix.success_rate),
        required_state=prefix.required_state,
        resulting_state=suffix.resulting_state,
        source_sequence=combined_sources,
        notes="composed",
    )
