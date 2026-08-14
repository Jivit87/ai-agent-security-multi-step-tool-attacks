# Phase 13 results

## Summary

| Backend | Attempts | Tool success | Multi-turn success | http.post | email.send | Unique cells | Unique mechanisms | Predicates | Verified breach | Verified score | Mean latency (s) | Median latency (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| deterministic | 54 | 0.44 | 0.00 | 0.11 | 0.00 | 9 | 7 | 0 | 0.00 | 0.00 | 0.062 | 0.055 |
| openai | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 | 0.000 |
| gpt_oss | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 | 0.000 |
| gemma | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 | 0.000 |
| gemma_4 | 54 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 1 | 0 | 0.00 | 0.00 | 0.000 | 0.000 |

## Interpretation

- This workspace can only validate the deterministic backend locally.
- GPT-OSS and Gemma-family backends are source-present but not runnable here because the required runtime packages are absent.
- The next phase should be executed in the official Kaggle runtime if the goal is to validate those backends against the real competition model servers.