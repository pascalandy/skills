# CASS QA canaries

Use only this registered canary during the functional gate. It was verified on CASS 0.10.0 on 2026-10-10

- Query: `README`
- Registered providers: `codex`, `pi_agent`, `opencode`, `claude_code`
- Passing evidence: at least one result tagged with each required provider slug

Use `--mode lexical --no-maintenance --limit 3 --fields summary` for each probe. Expand one exact returned hit from any required provider with `--message-index` and require the target message to contain the canary query

If the canary returns no result for a required provider, report `canary drift or provider failure`; do not replace it during the same invocation. Register a provider or replace the query only after an independently verified provider search proves it and this file is updated at the source
