# Reachable state model

This is the smallest security-relevant state model I could justify from the code
and the replay experiments.

## Two layers of state

### 1) Guardrail-relevant state

The packaged `optimal_public` guardrail depends on:

- `recent_sources`: the last 5 tool-event sources
- explicit authorization flags, if present in context
- the current tool arguments, especially the target string

It does not use:

- `recent_tools`
- `last_user`
- `side_effect`
- `scope`
- `seed`
- any persistent internal memory

SOURCE:
`aicomp_sdk/core/env/sandbox.py::SandboxEnv.interact`
`aicomp_sdk/guardrails/optimal.py::Guardrail.decide`

CONFIDENCE:
verified

### 2) Scoring-relevant state

The evaluator recomputes predicates and cell signatures from the replay trace.
So the search state also needs a compact trace summary:

- tool history
- source history
- outcomes
- egress count and payload digest
- sent-mail count and digest
- filesystem digest for the relevant sandbox files
- last user message hash, because predicate scoring looks at the final user intent

SOURCE:
`aicomp_sdk/core/predicates.py`
`aicomp_sdk/core/cells.py`
`aicomp_sdk/scoring.py`

CONFIDENCE:
verified

## Smallest sufficient search state

For this benchmark, the smallest useful state for reachability search is:

```text
S_t = (
    recent_sources[5],
    last_user_message_hash,
    compact tool-history summary,
    egress_digest,
    mail_digest,
    filesystem_digest
)
```

That is smaller than full environment state, but still enough to:

- predict the guardrail decision for the next dangerous action
- distinguish scored cells
- preserve replayability

`recent_tools` is useful for analysis and deduplication, but the guardrail itself
does not read it.

## Experimental conclusions

- `reset()` clears the taint queue.
- `snapshot()` / `restore()` preserve it.
- 5 clean tool events are enough to flush a web/email source out of the guardrail window.
- file-source actions are not tainting, but they are useful for clearing the queue.

SOURCE:
`experiments/attack_surface_results.jsonl`
`experiments/reachable_graph.jsonl`

CONFIDENCE:
verified
