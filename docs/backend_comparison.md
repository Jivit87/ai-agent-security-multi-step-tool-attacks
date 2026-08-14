# Backend comparison

## Local availability

| Backend | Available locally | Reason |
| --- | --- | --- |
| deterministic | yes |  |
| openai | no | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| gpt_oss | no | RuntimeError: Transformers SDK is not available |
| gemma | no | RuntimeError: Transformers SDK is not available |
| gemma_4 | no | RuntimeError: Transformers SDK with Gemma 4 support is not available |

## Comparison

| Backend | Attempts | Tool success | Multi-turn success | http.post | email.send | Unique cells | Unique mechanisms | Predicates | Verified breach | Verified score | Mean latency (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 54 | 0.44 | 0.00 | 0.11 | 0.00 | 9 | 7 | 0 | 0.00 | 0.00 | 0.062 |
| openai | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 |
| gpt_oss | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 |
| gemma | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 |
| gemma_4 | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 |

## Interpretation

- The current workspace can only execute the deterministic backend. GPT-OSS and Gemma family backends are source-present but not locally runnable because their runtime dependencies are missing.
- The competition runtime uses the Kaggle gateway and model servers, which are distinct from the local HF/OpenAI code paths.