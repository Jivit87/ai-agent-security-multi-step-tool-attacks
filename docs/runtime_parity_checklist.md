# Runtime parity checklist

## Contract parity

- [x] `AttackAlgorithm.run(env, config) -> list[AttackCandidate]`
- [x] Replay re-executes returned candidates in a fresh environment
- [x] Replay hop limit is `4`
- [x] `AttackCandidate` carries only `user_messages`

## Model/backend parity

- [x] Local deterministic backend exists
- [ ] GPT-OSS runtime available locally
- [ ] Gemma runtime available locally
- [ ] Gemma 4 runtime available locally
- [ ] OpenAI runtime available locally

## Prompt / chat parity

- [x] Sandbox injects a runtime instruction string into the runtime history
- [x] Tool descriptions are serialized into the agent runtime
- [x] Tool call schema is supplied to the backend
- [x] Chat-template backends use backend-specific prompt builders
- [x] GPT-OSS uses HF chat-template backend
- [x] Gemma uses HF chat-template backend with JSON envelope tool parser
- [x] Gemma 4 uses processor-backed / llama.cpp-compatible tool calls

## Generation parity

- [x] Local HF backends default to `do_sample=False`
- [x] HF backends default `max_new_tokens=256`
- [x] llm.cpp backend defaults `temperature=0.0` when `do_sample=False`
- [x] OpenAI Responses agent uses Responses API tool calls
- [x] OpenAI backend requires `OPENAI_API_KEY`

## Runtime gaps

- [ ] Actual competition model mount path
- [ ] Actual Kaggle runtime package set
- [ ] Exact hosted system prompt
- [ ] Exact hosted chat template for the selected competition backend
- [ ] Whether `gpt_oss` or `gemma` is the only active backend in a given run

