# Runtime parity

## What matches between local and competition code

- Submission contract: `AttackAlgorithm.run(env, config) -> list[AttackCandidate]`.
- Replay validation: evaluator replays returned candidates in a fresh environment.
- Attack replay hop limit: evaluator replay uses `max_tool_hops = 4`.

## What differs

- Local SDK backends are Python implementations (`deterministic`, `openai`, `gpt_oss`, `gemma`, `gemma_4`).
- Competition runtime routes through `kaggle_evaluation/jed_attack_134815/*` and launches Kaggle model servers.
- GPT-OSS/Gemma competition backends are GGUF/llama.cpp servers, not the local HF `transformers` implementations.
- `KAGGLE_IS_COMPETITION_RERUN=1` switches the gateway/inference servers into serving mode.

## Local parity status

- Deterministic backend: fully runnable locally.
- GPT-OSS backend: not runnable locally in this workspace (`transformers` missing).
- Gemma backend: not runnable locally in this workspace (`transformers` missing).
- Gemma 4 backend: not runnable locally in this workspace (`transformers` missing, and the Kaggle runtime is a GGUF/llama.cpp path).

## Phase 15 note

- The Kaggle competition runtime is still unexecuted in this workspace.
- Phase 15 therefore remains a source-level and harness-level validation phase until the scripts are run inside Kaggle.
