# State reset map

This records what resets and what persists in the local sandbox.

## Verified behavior

| Operation | Trace / tool state | Guardrail state | Agent state | Filesystem | Outcome |
|---|---|---|---|---|---|
| `snapshot()` | captured | captured | captured | captured | restoration replayable |
| `restore(snapshot)` | restored exactly | restored exactly | restored exactly | restored exactly | taint persists through restore |
| `reset()` | cleared | restored to initial | agent reset | filesystem restored from fixture backup | taint cleared |

SOURCE:
`aicomp_sdk/core/env/sandbox.py::SandboxEnv.snapshot`
`aicomp_sdk/core/env/sandbox.py::SandboxEnv.restore`
`aicomp_sdk/core/env/sandbox.py::SandboxEnv.reset`

CONFIDENCE:
verified

## Experimental proof

Observed sequence:

1. `search demo`
2. `snapshot()`
3. `upload report` → denied because `recent_sources` still includes `web`
4. `restore(snapshot)`
5. `upload report` → denied again
6. `reset()`
7. `upload report` → allowed

SOURCE:
`experiments/attack_surface_results.jsonl` case `state_reset_snapshot`

CONFIDENCE:
verified

## Implication

The effective security state is not an independent guardrail memory.
It is the replay trace, especially the last-5-tool-event source window.

SOURCE:
`aicomp_sdk/core/env/sandbox.py`
`aicomp_sdk/guardrails/optimal.py`

CONFIDENCE:
inferred from verified behavior
