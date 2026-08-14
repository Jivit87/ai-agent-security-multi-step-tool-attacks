# Competition runtime audit

## Model and backend surface

- `kaggle_evaluation/jed_attack_134815/jed_attack_gateway.py`
  - `MODEL_NAMES = os.getenv("AICOMP_MODEL_NAMES", "gpt_oss,gemma")`
  - The gateway resolves remote model servers for `gpt_oss` and `gemma`.
  - `DEFAULT_BUDGET_S = 8750.0`
  - `DEFAULT_MAX_TOOL_HOPS = AttackRunConfig.max_tool_hops` which resolves to `8`.

- `kaggle_evaluation/jed_attack_134815/gpt_oss_model_server.py`
  - `SPEC.model_label = "GPT-OSS"`
  - `SPEC.backend_label = "gpt_oss"`
  - Default GGUF repo/file:
    - `unsloth/gpt-oss-20b-GGUF`
    - `gpt-oss-20b-Q4_K_M.gguf`

- `kaggle_evaluation/jed_attack_134815/gemma_model_server.py`
  - `SPEC.model_label = "Gemma"`
  - `SPEC.backend_label = "gemma_4"`
  - Default GGUF repo/file:
    - `unsloth/gemma-4-26B-A4B-it-GGUF`
    - `gemma-4-26B-A4B-it-UD-Q4_K_M.gguf`

- `aicomp_sdk/agents/gpt_oss_agent.py`
  - Local HF fallback model id: `openai/gpt-oss-20b`
  - Env vars: `GPT_OSS_MODEL_ID`, `GPT_OSS_MODEL_PATH`

- `aicomp_sdk/agents/gemma_agent.py`
  - Local HF fallback model id: `google/gemma-3-4b-it`
  - Env vars: `GEMMA_MODEL_ID`, `GEMMA_MODEL_PATH`

- `aicomp_sdk/agents/gemma4_agent.py`
  - Local HF/GGUF model id: `google/gemma-4-26B-A4B-it`
  - Env vars: `GEMMA4_MODEL_ID`, `GEMMA4_MODEL_PATH`

- `aicomp_sdk/agents/openai_agent.py`
  - Default model: `gpt-4o-mini`
  - Requires `OPENAI_API_KEY`

## Tool and prompt interface

- `kaggle_evaluation/jed_attack_134815/remote_agent.py`
  - Model-server protocol:
    - `next_action`
    - `reset_state`
    - `snapshot_state`
    - `restore_state`
    - `unload`

- `kaggle_evaluation/jed_attack_134815/jed_attack_inference_server.py`
  - Competition attack entrypoint loads `attack.py` from `/kaggle/working/attack.py`
  - Requires class `AttackAlgorithm`
  - Requires inheritance from `AttackAlgorithmBase`
  - Runs the attack inside a `RemoteEnv`

- `aicomp_sdk/core/env/sandbox.py`
  - Default runtime instruction string is injected into the runtime history:
    - “You are a tool-using assistant operating in a sandbox...”
  - The agent sees user messages, tool results, and runtime instructions.

## Local availability status

- The local workspace does not have:
  - `transformers`
  - `openai`
- Therefore only `deterministic` is runnable locally here.

## Unknowns

- The actual Kaggle-mounted model path in the competition container is not present in this workspace.
- The exact competition-chosen backend at submission time is not fully determined from source alone if Kaggle-side env vars change `AICOMP_MODEL_NAMES`.
- The exact system prompt inside the hosted model server depends on the loaded agent backend and chat template.

