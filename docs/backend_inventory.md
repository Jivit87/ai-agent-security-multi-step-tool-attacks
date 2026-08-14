# Backend inventory

## Local availability

| Backend | Available locally | Reason |
| --- | --- | --- |
| deterministic | yes |  |
| openai | no | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| gpt_oss | no | RuntimeError: Transformers SDK is not available |
| gemma | no | RuntimeError: Transformers SDK is not available |
| gemma_4 | no | RuntimeError: Transformers SDK with Gemma 4 support is not available |

## Smoke-test summary

| Backend | Scenario | Seed | Tool calls | Target tool | Tool call success | Multi-turn success | Predicate count | Cell hash | Error |
| --- | --- | ---: | ---: | --- | --- | --- | ---: | --- | --- |
| deterministic | web_discovery_single | 123 | 4 | web.search | true | false | 0 | e691672cbadd1d52 |  |
| deterministic | web_discovery_followup | 123 | 8 | web.open | true | false | 0 | fffe4478addccef4 |  |
| deterministic | email_discovery | 123 | 4 | email.read | false | false | 0 | bd2361a8fa8f916d |  |
| deterministic | local_audit | 123 | 0 | fs.read | false | false | 0 | 32a7ccbc0640f7ee |  |
| deterministic | fs_write | 123 | 4 | fs.write | true | false | 0 | 6054d3f8a54f1aa7 |  |
| deterministic | fs_delete | 123 | 1 | fs.delete | false | false | 0 | 53fa9f86e7dbfa1a |  |
| deterministic | http_post | 123 | 4 | http.post | true | false | 0 | 0afa9dcffd5dd3bf |  |
| deterministic | email_send | 123 | 4 | email.send | false | false | 0 | e939d047a8f37614 |  |
| deterministic | shell_run | 123 | 0 | shell.run | false | false | 0 | 8dbafd7af7d7368a |  |
| deterministic | web_discovery_single | 456 | 4 | web.search | true | false | 0 | e691672cbadd1d52 |  |
| deterministic | web_discovery_followup | 456 | 8 | web.open | true | false | 0 | fffe4478addccef4 |  |
| deterministic | email_discovery | 456 | 4 | email.read | false | false | 0 | bd2361a8fa8f916d |  |
| deterministic | local_audit | 456 | 0 | fs.read | false | false | 0 | 32a7ccbc0640f7ee |  |
| deterministic | fs_write | 456 | 4 | fs.write | true | false | 0 | 6054d3f8a54f1aa7 |  |
| deterministic | fs_delete | 456 | 1 | fs.delete | false | false | 0 | 53fa9f86e7dbfa1a |  |
| deterministic | http_post | 456 | 4 | http.post | true | false | 0 | 0afa9dcffd5dd3bf |  |
| deterministic | email_send | 456 | 4 | email.send | false | false | 0 | e939d047a8f37614 |  |
| deterministic | shell_run | 456 | 0 | shell.run | false | false | 0 | 8dbafd7af7d7368a |  |
| deterministic | web_discovery_single | 789 | 4 | web.search | true | false | 0 | e691672cbadd1d52 |  |
| deterministic | web_discovery_followup | 789 | 8 | web.open | true | false | 0 | fffe4478addccef4 |  |
| deterministic | email_discovery | 789 | 4 | email.read | false | false | 0 | bd2361a8fa8f916d |  |
| deterministic | local_audit | 789 | 0 | fs.read | false | false | 0 | 32a7ccbc0640f7ee |  |
| deterministic | fs_write | 789 | 4 | fs.write | true | false | 0 | 6054d3f8a54f1aa7 |  |
| deterministic | fs_delete | 789 | 1 | fs.delete | false | false | 0 | 53fa9f86e7dbfa1a |  |
| deterministic | http_post | 789 | 4 | http.post | true | false | 0 | 0afa9dcffd5dd3bf |  |
| deterministic | email_send | 789 | 4 | email.send | false | false | 0 | e939d047a8f37614 |  |
| deterministic | shell_run | 789 | 0 | shell.run | false | false | 0 | 8dbafd7af7d7368a |  |
| openai | web_discovery_single | 123 | 0 | web.search | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | web_discovery_followup | 123 | 0 | web.open | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_discovery | 123 | 0 | email.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | local_audit | 123 | 0 | fs.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_write | 123 | 0 | fs.write | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_delete | 123 | 0 | fs.delete | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | http_post | 123 | 0 | http.post | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_send | 123 | 0 | email.send | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | shell_run | 123 | 0 | shell.run | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | web_discovery_single | 456 | 0 | web.search | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | web_discovery_followup | 456 | 0 | web.open | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_discovery | 456 | 0 | email.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | local_audit | 456 | 0 | fs.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_write | 456 | 0 | fs.write | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_delete | 456 | 0 | fs.delete | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | http_post | 456 | 0 | http.post | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_send | 456 | 0 | email.send | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | shell_run | 456 | 0 | shell.run | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | web_discovery_single | 789 | 0 | web.search | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | web_discovery_followup | 789 | 0 | web.open | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_discovery | 789 | 0 | email.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | local_audit | 789 | 0 | fs.read | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_write | 789 | 0 | fs.write | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | fs_delete | 789 | 0 | fs.delete | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | http_post | 789 | 0 | http.post | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | email_send | 789 | 0 | email.send | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | shell_run | 789 | 0 | shell.run | false | false | 0 |  | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| gpt_oss | web_discovery_single | 123 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | web_discovery_followup | 123 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_discovery | 123 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | local_audit | 123 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_write | 123 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_delete | 123 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | http_post | 123 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_send | 123 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | shell_run | 123 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | web_discovery_single | 456 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | web_discovery_followup | 456 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_discovery | 456 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | local_audit | 456 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_write | 456 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_delete | 456 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | http_post | 456 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_send | 456 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | shell_run | 456 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | web_discovery_single | 789 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | web_discovery_followup | 789 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_discovery | 789 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | local_audit | 789 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_write | 789 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | fs_delete | 789 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | http_post | 789 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | email_send | 789 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gpt_oss | shell_run | 789 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_single | 123 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_followup | 123 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_discovery | 123 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | local_audit | 123 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_write | 123 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_delete | 123 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | http_post | 123 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_send | 123 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | shell_run | 123 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_single | 456 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_followup | 456 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_discovery | 456 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | local_audit | 456 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_write | 456 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_delete | 456 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | http_post | 456 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_send | 456 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | shell_run | 456 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_single | 789 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | web_discovery_followup | 789 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_discovery | 789 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | local_audit | 789 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_write | 789 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | fs_delete | 789 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | http_post | 789 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | email_send | 789 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma | shell_run | 789 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK is not available |
| gemma_4 | web_discovery_single | 123 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | web_discovery_followup | 123 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_discovery | 123 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | local_audit | 123 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_write | 123 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_delete | 123 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | http_post | 123 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_send | 123 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | shell_run | 123 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | web_discovery_single | 456 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | web_discovery_followup | 456 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_discovery | 456 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | local_audit | 456 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_write | 456 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_delete | 456 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | http_post | 456 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_send | 456 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | shell_run | 456 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | web_discovery_single | 789 | 0 | web.search | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | web_discovery_followup | 789 | 0 | web.open | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_discovery | 789 | 0 | email.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | local_audit | 789 | 0 | fs.read | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_write | 789 | 0 | fs.write | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | fs_delete | 789 | 0 | fs.delete | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | http_post | 789 | 0 | http.post | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | email_send | 789 | 0 | email.send | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | shell_run | 789 | 0 | shell.run | false | false | 0 |  | RuntimeError: Transformers SDK with Gemma 4 support is not available |

## Interpretation

- This workspace currently runs the deterministic backend only; the other backends are present in source but unavailable locally.
- GPT-OSS and Gemma backends depend on `transformers` in the local SDK path, while the Kaggle wrapper uses GGUF servers for the competition runtime.
- OpenAI backend requires `OPENAI_API_KEY` and the `openai` package.