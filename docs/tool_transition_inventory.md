# Tool transition inventory

Generated from the tool registry and handler schemas.

| Tool | Arguments | Output | Side effect | Source label | Environment effect | Can influence later selection? |
|---|---|---|---|---|---|---|
| `web.search` | `query` | JSON page-hit list | `NETWORK` | `web` | searches public offline corpus; sets last source to `web` | yes, because output enters the agent history |
| `web.open` | `id` | page content text | `NETWORK` | `web` | reads a public page by id; sets last source to `web` | yes |
| `email.list` | `folder`, `limit?`, `cursor?` | JSON message summaries | `READ` | `email` | reads local mail folder summaries; sets last source to `email` | yes |
| `email.read` | `id` | JSON message body | `READ` | `email` | reads full local email message; sets last source to `email` | yes |
| `email.send` | `to`, `subject`, `body` | `sent` | `SHARE` | `tool` | appends a sent message to mailbox state | yes |
| `fs.read` | `path` | file text | `READ` | `file` | reads a sandbox file; sets last source to `file` | yes |
| `fs.write` | `path`, `content` | `ok` | `WRITE` | `file` | writes a sandbox file; sets last source to `file` | yes |
| `fs.delete` | `path` | `ok` | `WRITE` | `file` | deletes a sandbox file; sets last source to `file` | yes |
| `shell.run` | `cmd` | command output | `EXEC` | `tool` | runs a sandboxed command; sets last source to `tool` | yes |
| `http.post` | `url`, `data` | `ok` | `SHARE` | `tool` | records egress to the sink; sets last source to `tool` | yes |

## Notes

- The guardrail only reasons over the `recent_sources` window and the current
  tool arguments.
- `email.send`, `http.post`, `shell.run`, `fs.write`, and `fs.delete` are the
  dangerous-operation classes.
- `fs.read` is not dangerous by itself, but it is useful because it advances the
  rolling source queue while preserving search context.

SOURCE:
`aicomp_sdk/core/tools/*.py`
`aicomp_sdk/core/tools/registry.py`
`aicomp_sdk/core/tools/schema.py`
`aicomp_sdk/agents/tool_specs.py`

CONFIDENCE:
verified
