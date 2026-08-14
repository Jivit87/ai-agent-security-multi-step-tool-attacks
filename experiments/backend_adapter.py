from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from aicomp_sdk.agents import AgentSelection, build_agent, require_agent_selection_configuration


@dataclass(frozen=True)
class BackendSpec:
    name: str
    selection: AgentSelection
    available: bool
    reason: str | None = None

    def build_agent(self):
        return build_agent(self.selection)


def discover_backend_specs() -> list[BackendSpec]:
    """Return the backend matrix with availability checked against the local workspace."""
    specs: list[BackendSpec] = []
    for selection in (
        AgentSelection.DETERMINISTIC,
        AgentSelection.OPENAI,
        AgentSelection.GPT_OSS,
        AgentSelection.GEMMA,
        AgentSelection.GEMMA_4,
    ):
        try:
            require_agent_selection_configuration(selection)
        except Exception as err:  # noqa: BLE001 - availability probe only
            specs.append(
                BackendSpec(
                    name=selection.value,
                    selection=selection,
                    available=False,
                    reason=f"{type(err).__name__}: {err}",
                )
            )
        else:
            specs.append(
                BackendSpec(
                    name=selection.value,
                    selection=selection,
                    available=True,
                )
            )
    return specs


def available_backend_specs() -> list[BackendSpec]:
    return [spec for spec in discover_backend_specs() if spec.available]


def get_backend_spec(name: str) -> BackendSpec:
    for spec in discover_backend_specs():
        if spec.name == name:
            return spec
    raise ValueError(f"Unknown backend: {name}")

