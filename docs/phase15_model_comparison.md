# Phase 15 model comparison

## Local result

Only the deterministic backend executed in this workspace.

| Backend | Status | Evidence |
| --- | --- | --- |
| deterministic | runnable | local benchmark completed |
| openai | not runnable | `OPENAI_API_KEY` missing; `openai` package missing |
| gpt_oss | not runnable | `transformers` missing |
| gemma | not runnable | `transformers` missing |
| gemma_4 | not runnable | `transformers` missing |

## Competition target

Source inspection points to Kaggle-hosted GPT-OSS and Gemma 4 model servers.

- GPT-OSS default model id: `openai/gpt-oss-20b`
- Gemma default model id: `google/gemma-4-26B-A4B-it`

## Comparison status

- A real model comparison could not be completed in this workspace.
- The next meaningful comparison must run inside the Kaggle competition runtime.

