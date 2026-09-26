# CASS QA canaries

Use only these registered canaries during the mandatory functional gate. They come from the cross-provider ACv4 demo completed with CASS 0.6.25 on 2026-08-21

| Provider slug | Lexical query | Passing evidence |
|---|---|---|
| `codex` | `ACv4` | At least one result tagged `codex` |
| `pi_agent` | `ACv4` | At least one result tagged `pi_agent` |
| `opencode` | `Explication projet ACv4` | At least one result tagged `opencode` |
| `claude` | `ACv4` | At least one result tagged `claude` |

Use `--mode lexical --limit 3 --fields summary` for each probe. Expand one exact returned hit from any required provider and require non-empty surrounding conversation

If a registered canary returns no result, report `canary drift or provider failure`; do not replace it during the same invocation. Register or replace a canary only after an independently verified provider search proves the new query and this file is updated at the source
