---
name: "cass"
description: "Use only when the user explicitly mentions `cass` to install, update, diagnose, index, or search local coding-agent history"
---

# CASS

CASS indexes coding-agent sessions and exposes them through a CLI and TUI

The project changes frequently. Treat the installed binary as the authority for commands and schemas, and verify the latest release before installation or upgrade work

## Non-negotiable rules

- Never run bare `cass` as an agent because it opens the interactive TUI
- Use `--json`, `--robot`, or another machine-readable format for every agent command
- Never edit, move, or prune provider session logs
- Preserve an existing CASS archive before replacing it
- Do not call a setup healthy because one search returned results
- Do not install an unreleased build as a stability fix unless the user explicitly accepts that tradeoff
- Never return history from a stale or unproven index without the user's explicit approval to proceed in degraded mode

Humans can run bare `cass` after agent validation is complete

## Mandatory pre-use loop

Run this loop once per skill invocation before the first history operation requested by the user, including `search`, `pack`, `view`, `expand`, `sessions`, `timeline`, or export. The canary searches and expansion in step 4 are the only history reads allowed while the gate is closed. Use them only as QA evidence and do not return their content as the user's requested result

For install or upgrade work, make the binary available first, then restart at step 1. For an indexing diagnosis, capture the failing state before step 2 so the refresh does not erase the evidence

### 1. Discover the installed contract

Do not rely on remembered flags or schemas

```bash
cass --version
cass capabilities --json | jq '{version, commands: [.commands[] | select(.name == "index" or .name == "status" or .name == "search" or .name == "expand" or .name == "quarantine" or .name == "sources")]}'
cass robot-docs guide
```

Add the user's requested command to the filter when it is not already present. Use `robot-docs commands` or `robot-docs examples` to verify nested subcommands when available. When the installed contract lists only their parent, require the actual nested probe in step 3 to parse as valid JSON. Do not load the entire capabilities response into context

Completion criterion: the binary responds, the installed contract lists every top-level command in the pre-use loop plus the requested operation, and every documented flag matches. Step 3 must still prove the nested readiness probes. If the contract differs from this skill, follow the binary and flag the skill drift

### 2. Refresh once

Run the ordinary incremental indexer without `--full`, `--force-rebuild`, or semantic indexing

```bash
cass index --json --no-progress-events
```

This command can take minutes on a large archive even when little changed. Monitor the one running process with a time budget informed by prior runs. Do not launch a duplicate because output is quiet

Completion criterion: the command exits successfully with `success=true`. This proves ingestion completed, not that the search index is ready

Do not substitute `search --refresh`. Its refresh failure is non-fatal, so search may continue against an old index

### 3. Pass the structural gate

```bash
cass status --json | jq '{healthy, initialized, index: {status: .index.status, fresh: .index.fresh, stalled: .index.stalled, fingerprint: .index.fingerprint}, pending, search_completeness, recommended_action, recommended_commands}'
cass quarantine list --json
cass sources agents list --json
```

The structural gate passes only when

- `healthy` is true
- `index.status` is `ready` and `index.fresh` is true
- `index.fingerprint.matches_current_db_fingerprint` is true
- `pending.sessions` is zero
- `search_completeness.complete` and `search_completeness.can_search` are true
- quarantine contains no unexplained conversations
- no provider required for the task is unexpectedly disabled

Use the full `status` response when counts or fingerprints matter. The faster `health` response may omit the current database fingerprint

Completion criterion: every status-derived condition passes in one response, and the adjacent quarantine and provider checks also pass

### 4. Pass the functional gate

Read [references/canaries.md](references/canaries.md). Run its validated lexical canary for each provider required by the task or explicitly expected in the setup. Do not invent a topic or test every connector CASS knows

```bash
cass search "ACv4" --robot --mode lexical --agent codex --limit 3 --fields summary
```

If the required provider has no registered canary, keep the gate closed and report the missing QA fixture. A broad unfiltered query can be dominated by one provider and does not prove connector coverage

Expand one returned hit with its exact path and line number

```bash
cass expand /path/from/search.jsonl -n 42 -C 3 --json
```

Completion criterion: every required provider returns a correctly tagged result, and one exact hit expands into non-empty surrounding conversation

### 5. Open or stop

Open the gate and perform the requested history operation only after steps 1 through 4 pass

If a structured response recommends another incremental refresh after the first one, follow that recommendation once. If the same blocker survives two consecutive refresh-and-status cycles, stop repeating it and enter diagnosis

```bash
cass capabilities --json | jq '{commands: [.commands[] | select(.name == "triage" or .name == "doctor")]}'
cass triage --json
cass doctor --json --check
```

Follow structured `next_command` or `recommended_commands` only while the blocker changes or the response identifies a retryable condition. Do not scrape diagnostic prose to invent a repair. Keep the gate closed when the index is stalled, its fingerprint differs, required coverage fails, quarantine is unexplained, or the same recommendation repeats

Report the failed condition and the last safe evidence. Continue against the existing index only when the user explicitly accepts degraded results. Before further diagnosis or repair, read [references/maintenance.md](references/maintenance.md)

## Search workflow

Start narrow and control output size

```bash
cass search "query" --robot --mode lexical --limit 5 --fields summary
cass search "query" --robot --agent codex --limit 5 --fields summary
cass search "query" --robot --agent pi_agent --limit 5 --fields summary
```

Follow a useful hit with its source and nearby conversation

```bash
cass view /path/to/session.jsonl -n 42 --json
cass expand /path/to/session.jsonl -n 42 -C 5 --json
```

For current-workspace discovery and handoff

```bash
cass sessions --current --json
cass sessions --workspace "$(pwd)" --json --limit 10
cass search "handoff topic" --robot --fields summary --limit 10
```

Use `--robot-meta` when latency, cache behavior, fallback mode, or index freshness matters

## Maintenance and recovery

Read [references/maintenance.md](references/maintenance.md) when the request involves installation, upgrade, explicit indexing, diagnosis, repair, corrupt archive recovery, OpenCode's first import, or distributing this skill. Do not load it for an ordinary search after a green pre-use loop

## Self-documentation

Use CASS's own current documentation instead of expanding this skill with copied command reference

```bash
cass capabilities --json
cass introspect --json
cass robot-docs commands
cass robot-docs schemas
cass robot-docs examples
cass robot-docs exit-codes
```

When this skill and the installed CLI disagree, follow the installed CLI and update the chezmoi source skill with the verified behavior
