# Competition runtime requirements

## Submission contract

- Provide `attack.py` with `AttackAlgorithm` inheriting `AttackAlgorithmBase`.
- `run(env, config)` must return `list[AttackCandidate]` with replayable `user_messages` only.

## Runtime knobs from source

- Local evaluation CLI defaults attack/defense budget to `1800s`.
- Kaggle gateway uses `DEFAULT_BUDGET_S = 8750.0` for the hosted run.
- Replays are validated with `max_tool_hops = 4`.
- Search-side `AttackRunConfig.max_tool_hops` defaults to `8`.

## Model/backend configuration

- `AICOMP_MODEL_NAMES` defaults to `gpt_oss,gemma` in the Kaggle gateway.
- `GPT_OSS_GGUF_REPO` / `GPT_OSS_GGUF_FILE` / `GPT_OSS_MODEL_PATH` configure the GPT-OSS GGUF server.
- `GEMMA_GGUF_REPO` / `GEMMA_GGUF_FILE` / `GEMMA_MODEL_PATH` configure the Gemma GGUF server.
- `KAGGLE_IS_COMPETITION_RERUN=1` enables Kaggle serving mode.

## Local dependency gap

- This workspace does not currently have `transformers`, `openai`, or the Kaggle GGUF runtime packages required to run the model backends locally.
- Therefore backend validation here is limited to source inspection and the deterministic agent.