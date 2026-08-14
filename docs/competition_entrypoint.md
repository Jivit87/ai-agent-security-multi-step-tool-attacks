# Competition entrypoint

## Submission artifact

- `attack.py` in the submission root.
- Must define `AttackAlgorithm`.
- Must inherit from `AttackAlgorithmBase`.
- Must implement `run(env, config) -> list[AttackCandidate]`.

## Gateway / inference path

Source:

- `kaggle_evaluation/jed_attack_134815/jed_attack_gateway.py`
- `kaggle_evaluation/jed_attack_134815/jed_attack_inference_server.py`

Execution shape:

1. Kaggle launches the competition gateway.
2. Gateway loads the competitor submission from `/kaggle/working/attack.py`.
3. Gateway starts the attacker thread with `RemoteEnv`.
4. `RemoteEnv` forwards `reset`, `interact`, `snapshot`, and `restore` calls back through `predict()`.
5. Gateway replays every returned `AttackCandidate` and scores verified findings.

## Environment variables

- `KAGGLE_IS_COMPETITION_RERUN=1` enables serving mode.
- `AICOMP_MODEL_NAMES` defaults to `gpt_oss,gemma`.
- `GPT_OSS_GGUF_REPO`, `GPT_OSS_GGUF_FILE`, `GPT_OSS_MODEL_PATH`
- `GEMMA_GGUF_REPO`, `GEMMA_GGUF_FILE`, `GEMMA_MODEL_PATH`

## Runtime defaults from source

- Competition budget: `8750.0` seconds in the gateway.
- Local evaluator default red-team budget: `1800.0` seconds.
- Replay hop limit: `4`.
- Search-side default max tool hops: `8`.

## Unknowns in this workspace

- Actual Kaggle model mount paths are not available here.
- The real competition model selection is controlled by the gateway/runtime environment, not by the local workspace.

