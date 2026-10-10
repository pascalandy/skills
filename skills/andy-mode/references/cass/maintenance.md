# CASS maintenance and recovery

The installed binary remains authoritative. Recheck the relevant command in `cass capabilities --json` and `cass robot-docs` before acting

## Installation and upgrades

Compare the installed version with the latest release first

```bash
cass upgrade --check --json
```

When `is_newer` is true, `cass upgrade --yes` runs the checksum-verified installer without a prompt. When the upgrade command is unavailable, use the verified installer

```bash
curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.sh \
  | bash -s -- --easy-mode --verify
```

Re-run `cass --version` and the mandatory pre-use gate, including its functional gate, after installation or upgrade. When the new version differs from the version the skill is verified against, recheck the skill and update its source

## Initial indexing

If `cass status --json` reports `initialized=false` and recommends `cass index --full`, build the initial archive once

```bash
cass index --full --json --no-progress-events
```

Require `success=true`, then restart the pre-use gate. Do not use `--full` for later refreshes

## Connector indexing

The mandatory pre-use gate owns routine refresh. Outside that gate, prefer connector-bounded indexing for diagnosis or maintenance. After initial indexing, a full rebuild is a recovery operation, never a routine pre-use step

Common local roots include

```text
Codex       ~/.codex/sessions
Pi          ~/.pi/agent/sessions
Claude Code ~/.claude/projects
Claude app  ~/Library/Application Support/Claude/claude-code-sessions
Claude app  ~/Library/Application Support/Claude/local-agent-mode-sessions
OpenCode    ~/.local/share/opencode
```

Target one root when diagnosing a connector

```bash
cass index --watch-once /absolute/provider/root --json --no-progress-events
```

A targeted path can still trigger an archive-wide lexical refresh. Monitor the one process with a time budget. Stop only when it exits, an explicit abort policy fires, or `cass status --json` reports `stalled` with corroborating evidence

When the structured error identifies an incomplete scan, CASS keeps the committed work. Repeat the idempotent targeted scan once. Exit 7 means another process holds the lock. Wait for it before starting another run. Exit 9 is a general error. Inspect `err.kind` before deciding what to do. Compare provider counts before and after a retry

### Large archives on macOS

CASS releases can regress because its SQLite and lexical-index dependencies move quickly. When a scan stops reporting progress

1. Read `cass status --json`, including `rebuild_progress`
2. Confirm whether the database fingerprint or conversation count still advances
3. Inspect process CPU and memory
4. Check the current upstream issue before applying an old workaround. `cass robot-docs recipes` maps known stall signatures to their issues
5. Stop only when evidence shows a wedge or an explicit abort policy fires

### OpenCode first import

OpenCode stores current sessions in `~/.local/share/opencode/opencode.db`. A first import can take hours because CASS decodes the full `message` and `part` tables before yielding conversations

For a known large first import, verify current upstream guidance and run a bounded foreground job with false stall detection disabled

```bash
CASS_INDEX_STALL_DETECT_SECS=0 \
CASS_INDEX_STALL_ABORT_SECS=0 \
cass index --watch-once "$HOME/.local/share/opencode" --json --no-progress-events
```

Do not treat `current=0`, `total=0`, and high CPU as proof of deadlock during this phase. Confirm that the process is alive and that the installed release still has the documented long-scan behavior

After import, prove OpenCode coverage with both archive counts and a filtered search

```bash
cass search "known OpenCode topic" --agent opencode --robot --mode lexical --no-maintenance --limit 5 --fields summary
```

## Derived-index repair

Do not rebuild solely because index age exceeds the default 30-minute threshold

If the canonical database is readable but the lexical index remains unusable or its fingerprint differs after the bounded refresh loop, start with read-only diagnosis

```bash
cass triage --json
cass doctor --json --check
cass doctor repair --dry-run --json
```

On a multi-GB archive, `doctor --check` can take several minutes despite the "few seconds" in `robot-docs recipes`. Its stderr heartbeat names the last completed phase. Run it in the background with a time budget. It defers the full-page integrity probe above its size limit, so warnings that report unchecked integrity or coverage do not signal damage

A `repair-previously-failed` health class comes from a marker under `doctor/failure-markers/`. Read it before acting. When its `applied_actions` is empty and `user_data_modified` is false, the earlier repair changed nothing. The marker only blocks a repeated mutating repair

Treat a dry run as authorized only when it returns a non-empty plan fingerprint and explicit actions. If it returns no plan, reports unchecked archive coverage, or requests operator review, stop without mutation

Before applying a plan

- confirm every action affects derived assets only
- obtain user approval for the mutating repair
- run the exact apply command emitted by the immediately preceding dry run
- restart the mandatory pre-use gate and require every gate to pass

Never invent or reuse a plan fingerprint

## Corrupt archive recovery

Before replacing a corrupt archive

- Record the data directory from `cass status --json`
- Move the entire directory to a timestamped backup path rather than deleting it
- Attempt CASS's read-only archive recovery first
- Rebuild from provider logs only when archive recovery cannot proceed
- Keep the backup until coverage is proven non-decreasing

## Shared-agent distribution

The CLI binary is shared through the shell `PATH`. Each agent also needs the andy-mode skill, which carries the `cass` route, in its own skill directory. `just install-skills` ships the skill to one machine and `just sync-fleet` ships it to every machine, but neither installs the `cass` binary, which each machine needs separately

Edit only the managed source at `authoring/andy/andy-mode/` in `pascalandy/skills`, then follow that repository's `AGENTS.md` to regenerate and install the copies. Never edit an installed copy
