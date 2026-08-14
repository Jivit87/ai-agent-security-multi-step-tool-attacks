# Provenance sink matrix

| Sink | Provenance | Guardrail | Predicate effect | Verdict |
| --- | --- | --- | --- | --- |
| http.post | clean | ALLOW | payload-ready when clean | PERMITTED |
| http.post | web | DENY | payload-ready when clean | BLOCKED |
| http.post | email | DENY | payload-ready when clean | BLOCKED |
| http.post | file | ALLOW | payload-ready when clean | BLOCKED |
| http.post | mixed | DENY | payload-ready when clean | BLOCKED |
| fs.write/fs.delete | clean | DENY | protected path blocked | BLOCKED |
| fs.write/fs.delete | web | DENY | protected path blocked | BLOCKED |
| fs.write/fs.delete | email | DENY | protected path blocked | BLOCKED |
| fs.write/fs.delete | file | DENY | protected path blocked | BLOCKED |
| fs.write/fs.delete | mixed | DENY | protected path blocked | BLOCKED |
| shell.run | clean | ALLOW | needs taint, but taint triggers guardrail | BLOCKED |
| shell.run | web | DENY | needs taint, but taint triggers guardrail | BLOCKED |
| shell.run | email | DENY | needs taint, but taint triggers guardrail | BLOCKED |
| shell.run | file | ALLOW | needs taint, but taint triggers guardrail | BLOCKED |
| shell.run | mixed | DENY | needs taint, but taint triggers guardrail | BLOCKED |
| email.send | clean | ALLOW | clean state required | PERMITTED |
| email.send | web | DENY | clean state required | BLOCKED |
| email.send | email | DENY | clean state required | BLOCKED |
| email.send | file | ALLOW | clean state required | BLOCKED |
| email.send | mixed | DENY | clean state required | BLOCKED |

## Interpretation

- Clean provenance is the only provenance class that keeps `http.post` and `email.send` in play.
- Web/email provenance collides with the guardrail on dangerous sinks.
- `DESTRUCTIVE_WRITE` remains blocked because the protected target is filtered directly.
- `UNTRUSTED_TO_ACTION` is structurally blocked because the required taint is the same taint the guardrail uses to deny the sink.