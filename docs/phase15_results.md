# Phase 15 results

| Backend | Model | Scenario | Selected | Executed | Guardrail | Predicate | Replay | Score | Error |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: | --- |
| deterministic | deterministic | web_discovery_single | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | web_discovery_followup | true | true | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| deterministic | deterministic | email_discovery | false | false | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| deterministic | deterministic | local_audit | false | false |  |  | true | 0.00 |  |
| deterministic | deterministic | fs_write | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | fs_delete | false | false | denied |  | true | 0.00 |  |
| deterministic | deterministic | http_post | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | email_send | false | false | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| deterministic | deterministic | shell_run | false | false |  |  | true | 0.00 |  |
| deterministic | deterministic | web_search | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | web_open | true | true | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| deterministic | deterministic | email_read | false | false | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| deterministic | deterministic | fs_read | false | false |  |  | true | 0.00 |  |
| deterministic | deterministic | fs_write | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | fs_delete | false | false | denied |  | true | 0.00 |  |
| deterministic | deterministic | shell_run | false | false |  |  | true | 0.00 |  |
| deterministic | deterministic | http_post | true | true |  |  | true | 0.00 |  |
| deterministic | deterministic | email_send | false | false | not_found, not_found, not_found, not_found |  | true | 0.00 |  |
| openai | openai | web_discovery_single | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | web_discovery_followup | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | email_discovery | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | local_audit | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | web_search | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | web_open | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | email_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | fs_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| openai | openai | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: OPENAI_API_KEY must be set when agent selection is 'openai'. |
| gpt_oss | gpt_oss | web_discovery_single | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | web_discovery_followup | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | email_discovery | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | local_audit | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | web_search | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | web_open | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | email_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | fs_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gpt_oss | gpt_oss | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | web_discovery_single | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | web_discovery_followup | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | email_discovery | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | local_audit | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | web_search | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | web_open | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | email_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | fs_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma | gemma | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK is not available |
| gemma_4 | gemma_4 | web_discovery_single | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | web_discovery_followup | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | email_discovery | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | local_audit | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | web_search | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | web_open | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | email_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | fs_read | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | fs_write | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | fs_delete | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | shell_run | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | http_post | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |
| gemma_4 | gemma_4 | email_send | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | RuntimeError: Transformers SDK with Gemma 4 support is not available |