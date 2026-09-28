---
name: "cass"
description: "Use only when the user explicitly mentions `cass` to search local coding-agent history"
---

# CASS

CASS indexes coding-agent sessions and exposes them through a CLI and TUI

This skill is verified against cass 0.9.0. The project changes frequently, so the installed binary remains the authority for commands and schemas

## Non-negotiable rules

- Never run bare `cass` as an agent because it opens the interactive TUI
- Use `--json`, `--robot`, or another machine-readable format for every agent command
- Never edit, move, or prune provider session logs
- Preserve an existing CASS archive before replacing it
- Do not call a setup healthy because one search returned results
- Install or upgrade `cass` only when the user asks for it or approves it. A history request is not approval, even when it names `cass`. A delegated agent reports back to its parent instead of installing. Installing an unreleased build as a stability fix also needs the user to accept that tradeoff explicitly
- Never return history from a stale or unproven index without the user's explicit approval to proceed in degraded mode

Humans can run bare `cass` after agent validation is complete

## Mandatory pre-use gate

Run this gate once per skill invocation before the first history operation requested by the user, including `search`, `pack`, `view`, `expand`, `sessions`, `timeline`, or export. The canary searches and expansion in step 4 are the only history reads allowed while the gate is closed. Use them only as QA evidence and do not return their content as the user's requested result

For install, upgrade, or repair work, finish that work first, then run the gate from step 1. For an indexing diagnosis, capture the failing state before step 3 so the refresh does not erase the evidence

### 1. Check the version

```bash
cass --version
```

When the command fails, classify the failure before reporting it. `command -v` is a shell builtin, so run it through `sh -c`; both probes then work with or without an `rtk` prefix

```bash
sh -c 'command -v cass'
ls -l ~/.local/bin/cass
```

A wrapper error containing "No such file or directory" can mean a missing command or an installed binary whose loader is missing, and it may omit the command's name. For a missing command, `rtk proxy` exits 1 rather than 127. Classify with the probes, not the wrapper's wording or exit code

| State | Signal | Action |
|---|---|---|
| Not installed | `command -v cass` prints nothing and `~/.local/bin/cass` does not exist | Report that `cass` is not installed on this machine and point to [installation](references/maintenance.md#installation-and-upgrades) |
| Installed, not on `PATH` | `command -v cass` prints nothing and `~/.local/bin/cass` exists | Report a `PATH` problem. Do not reinstall |
| Installed but broken | `cass` is found but fails to run, such as exit 126, a loader error, or a crash | Diagnose through [references/maintenance.md](references/maintenance.md). Do not report it as missing |

Keep the gate closed in every state. Install only under the install rule in [non-negotiable rules](#non-negotiable-rules), and do not search other directories for the binary

When the version differs from 0.9.0, check the installed contract before relying on this skill. Do not load the entire capabilities response into context

```bash
cass capabilities --json | jq '{version, commands: [.commands[] | select(.name == "index" or .name == "status" or .name == "search" or .name == "expand" or .name == "sources") | {name, flags: [.arguments[]?.name]}]}'
cass robot-docs guide
```

Add the user's requested command to the filter. Capabilities lists only parent commands, so the nested `sources agents list` probe in step 2 must still parse as valid JSON. If the contract differs from this skill, follow the binary, flag the skill drift, and run step 4

Completion criterion: `cass --version` succeeds, and the version is 0.9.0 or the installed contract lists every command and flag this skill uses plus the requested operation. If `cass --version` fails, the gate stays closed and the report names one of the three failure states

### 2. Pass the structural gate

```bash
cass status --json | jq '{healthy, initialized, index: {status: .index.status, fresh: .index.fresh, stalled: .index.stalled, fingerprint: .index.fingerprint}, pending, search_completeness, recommended_action, recommended_commands}'
cass sources agents list --json
```

The structural gate passes only when

- `healthy` is true
- `index.status` is `ready` and `index.fresh` is true
- `index.fingerprint.matches_current_db_fingerprint` is true
- `pending.sessions` is zero
- `search_completeness.complete` and `search_completeness.can_search` are true
- `search_completeness.quarantined_conversations` is zero or explained
- no provider required for the task appears in `disabled_agents`

Use the full `status` response when counts or fingerprints matter. The faster `health` response may omit the current database fingerprint

Completion criterion: every status-derived condition passes in one response, and the provider check also passes

If `initialized` is false and status recommends an initial full index, follow [initial indexing](references/maintenance.md#initial-indexing). Then restart this gate

### 3. Refresh when needed

Run one incremental refresh when step 2 fails only on freshness or pending sessions, or when the request concerns recent work such as the current session, a handoff, or today's activity. A passing structural gate does not prove that recent sessions are ingested

```bash
cass index --json --no-progress-events
```

Never add `--full`, `--force-rebuild`, or `--semantic` here. The command can take minutes on a large archive even when little changed. Monitor the one running process with a time budget informed by prior runs. Do not launch a duplicate because output is quiet

Completion criterion: the command exits successfully with `success=true`, then step 2 passes again. If it fails, inspect the structured error before deciding whether to retry

Do not substitute `search --refresh`. Its refresh failure is non-fatal, so search may continue against an old index

### 4. Pass the functional gate after a setup change

Run this step after an install, upgrade, or repair, or when step 1 flags drift. Skip it otherwise

Read [references/canaries.md](references/canaries.md). Run its registered lexical canary for each provider required by the task or explicitly expected in the setup. Do not invent a topic or test every connector CASS knows

```bash
cass search "CANARY_QUERY" --robot --mode lexical --no-maintenance --agent PROVIDER_SLUG --limit 3 --fields summary
```

If the required provider has no registered canary, keep the gate closed and report the missing QA fixture. A broad unfiltered query can be dominated by one provider and does not prove connector coverage

Expand one returned hit with the coordinates from that same hit

```bash
cass expand SOURCE_PATH --message-index LINE_NUMBER --source SOURCE_ID --conversation-id CONVERSATION_ID -C 3 --json
```

Completion criterion: every required provider returns a correctly tagged result, and the expanded message marked `is_target` contains the canary query

### 5. Open or stop

Open the gate and perform the requested history operation only after every required step passes

If a structured response recommends another incremental refresh after the first one, follow that recommendation once. If the same blocker survives two consecutive refresh-and-status cycles, stop repeating it and enter diagnosis

```bash
cass triage --json
cass doctor --json --check
```

Follow structured `next_command` or `recommended_commands` only while the blocker changes or the response identifies a retryable condition. Do not scrape diagnostic prose to invent a repair. Keep the gate closed when the index is stalled, its fingerprint differs, required coverage fails, quarantine is unexplained, or the same recommendation repeats

Report the failed condition and the last safe evidence. Continue against the existing index only when the user explicitly accepts degraded results. Before further diagnosis or repair, read [references/maintenance.md](references/maintenance.md)

## Search workflow

Start narrow, stay read-only, and bound the output

```bash
cass search "query" --robot --robot-meta --mode lexical --no-maintenance --fields summary --limit 5 --max-tokens 2000 --timeout 2000
```

Narrow with `--agent SLUG`, `--workspace PATH`, or `--days N`. `cass capabilities --json | jq '.connectors'` lists agent slugs. An unknown slug returns zero hits without an error. Choose `--mode hybrid` or `--mode semantic` only when the question needs conceptual retrieval

Check every response before using it

- A `maintenance-required` error ends the attempt. Report it and return to the pre-use gate instead of rebuilding
- `budget.timed_out` true means empty or short results do not prove absence
- A passing structural gate remains authoritative when search reports an age-only `_meta.index_freshness.fresh=false` warning. Continue without refreshing. For newly written sessions, follow step 3

Follow a useful hit with its surrounding conversation. Pass `source_path`, `line_number`, `source_id`, and `conversation_id` from the same hit

```bash
cass expand SOURCE_PATH --message-index LINE_NUMBER --source SOURCE_ID --conversation-id CONVERSATION_ID -C 5 --json
```

Never pass a hit's `line_number` to `-n`. That flag addresses a physical file line and lands on the wrong message

For current-workspace discovery and handoff

```bash
cass sessions --current --json
cass sessions --workspace "$(pwd)" --json --limit 10
cass search "handoff topic" --robot --robot-meta --mode lexical --no-maintenance --fields summary --limit 10 --timeout 2000
```

## Maintenance and recovery

Read [references/maintenance.md](references/maintenance.md) when the request involves installation, upgrade, explicit indexing, diagnosis, repair, corrupt archive recovery, OpenCode's first import, or distributing this skill. Do not load it for an ordinary search after a green pre-use gate

## Self-documentation

Use CASS's own current documentation instead of expanding this skill with copied command reference

```bash
cass capabilities --json
cass introspect --json
cass robot-docs commands
cass robot-docs schemas
cass robot-docs examples
cass robot-docs exit-codes
cass robot-docs recipes
cass robot-docs doctor
```

Prose examples can lag the binary. In 0.9.0, `robot-docs examples` and the upstream `SKILL.md` still expand hits with `-n`. Argument descriptions in `capabilities` win

When this skill and the installed CLI disagree, follow the installed CLI. Then update this skill's source with the verified behavior and version, as described under shared-agent distribution in [references/maintenance.md](references/maintenance.md)
