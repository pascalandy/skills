# CASS QA canaries

Use only these registered canaries during the functional gate. They come from the cross-provider ACv4 demo of 2026-08-21 and were re-verified on CASS 0.9.0 on 2026-09-26

| Provider slug | Lexical query | Passing evidence |
|---|---|---|
| `codex` | `ACv4` | At least one result tagged `codex` |
| `pi_agent` | `ACv4` | At least one result tagged `pi_agent` |
| `opencode` | `Explication projet ACv4` | At least one result tagged `opencode` |
| `claude_code` | `ACv4` | At least one result tagged `claude_code` |

The `claude_code` canary currently resolves to Claude app sessions, so it does not prove the `~/.claude/projects` root

Use `--mode lexical --no-maintenance --limit 3 --fields summary` for each probe. Expand one exact returned hit from any required provider with `--message-index` and require the target message to contain the canary term

If a registered canary returns no result, report `canary drift or provider failure`; do not replace it during the same invocation. Register or replace a canary only after an independently verified provider search proves the new query and this file is updated at the source
