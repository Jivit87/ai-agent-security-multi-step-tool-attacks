# Model-limited edges

| Backend | Edge | Status | Evidence |
| --- | --- | --- | --- |
| deterministic | clean -> email.send | MODEL_LIMITED | None |
| deterministic | clean -> http.post | REACHABLE_BUT_UNSCORED | 0afa9dcffd5dd3bf |
| openai | backend availability | UNAVAILABLE_LOCALLY | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| gpt_oss | backend availability | UNAVAILABLE_LOCALLY | RuntimeError: Transformers SDK is not available |
| gemma | backend availability | UNAVAILABLE_LOCALLY | RuntimeError: Transformers SDK is not available |
| gemma_4 | backend availability | UNAVAILABLE_LOCALLY | RuntimeError: Transformers SDK with Gemma 4 support is not available |

## Notes

- Backend-specific labels are used instead of a single global `MODEL_LIMITED` label.
- A backend that is unavailable locally is not assumed to be impossible in the competition runtime.

## Phase 14 runtime note

- Local validation can only execute the deterministic backend in this workspace.
- GPT-OSS, Gemma, and Gemma 4 remain unavailable locally because the required runtime packages are absent here.
- The competition runtime audit shows the Kaggle gateway is responsible for selecting and serving the real model backend(s).

## Phase 15 runtime note

- As of August 14, 2026, the Kaggle competition runtime has not been executed from this workspace.
- `email.send` and clean `http.post` remain unverified for the real competition model until the phase-15 Kaggle run is performed.
