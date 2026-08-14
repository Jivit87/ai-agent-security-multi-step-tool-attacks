# Phase 15 backend activation

## Local workspace result

- `deterministic`: runnable
- `openai`: not runnable (`OPENAI_API_KEY` missing and `openai` package missing)
- `gpt_oss`: not runnable (`transformers` missing)
- `gemma`: not runnable (`transformers` missing)
- `gemma_4`: not runnable (`transformers` missing)

## Competition runtime target

Source inspection indicates the competition runtime uses:

- `AICOMP_MODEL_NAMES="gpt_oss,gemma"`
- GPT-OSS model server
- Gemma 4 model server

## What is still unknown locally

- Which backend the Kaggle runtime actually activates for a given run.
- Whether the hosted model server is reachable in the competition container.
- Whether the real competition container exposes GPU / CUDA and the required GGUF model files.

## Next step

Run:

- `experiments/kaggle_runtime_probe.py`
- `experiments/competition_backend_runner.py`
- `experiments/phase15_model_sink_matrix.py`

inside the Kaggle competition runtime.

