# CASS maintenance and recovery

Resolve this file relative to the CASS skill directory. The installed binary remains authoritative. Recheck the relevant command in `cass capabilities --json` and `cass robot-docs` before acting

## Installation and upgrades

Compare the installed version with the current release first. Prefer CASS's upgrade command when the installed contract supports it. The verified installer remains the fallback

```bash
curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/coding_agent_session_search/main/install.sh \
  | bash -s -- --easy-mode --verify
```

Re-run `cass --version` and the mandatory pre-use loop after installation or upgrade

## Connector indexing

The mandatory pre-use loop owns routine refresh. Outside that loop, prefer connector-bounded indexing for diagnosis or maintenance. A full rebuild is a recovery operation, never a routine pre-use step

Common local roots include

```text
Codex       ~/.codex/sessions
Pi          ~/.pi/agent/sessions
Claude Code ~/.claude/projects
Claude app  ~/Library/Application Support/Claude/local-agent-mode-sessions
OpenCode    ~/.local/share/opencode
```

Target one root when diagnosing a connector

```bash
cass index --watch-once /absolute/provider/root --json --no-progress-events
```

A targeted path can still trigger an archive-wide lexical refresh. Monitor the one process with a time budget. Stop only when it exits, an explicit abort policy fires, or `cass status --json` reports `stalled` with corroborating evidence

Repeat an idempotent targeted scan after exit code 7 only when the error identifies a retryable snapshot conflict. Compare provider counts before and after the retry

### Large archives on macOS

CASS releases can regress because its SQLite and lexical-index dependencies move quickly. When a scan stops reporting progress

1. Read `cass status --json`
2. Confirm whether the database fingerprint or conversation count still advances
3. Inspect process CPU and memory
4. Check the current upstream issue before applying an old workaround
5. Stop only when evidence shows a wedge or an explicit abort policy fires

`FSQLITE_READ_WITNESS_CAP=0` has worked around some FrankenSQLite cursor loops, but it is not a universal fix. Use it only for a matching failure signature and record that it was required

### OpenCode first import

OpenCode stores current sessions in `~/.local/share/opencode/opencode.db`. A first import can take hours because CASS decodes the full `message` and `part` tables before yielding conversations

For a known large first import, verify current upstream guidance and run a bounded foreground job with false stall detection disabled

```bash
FSQLITE_READ_WITNESS_CAP=0 \
CASS_INDEX_STALL_DETECT_SECS=0 \
CASS_INDEX_STALL_ABORT_SECS=0 \
cass index --watch-once "$HOME/.local/share/opencode" --json --no-progress-events
```

Do not treat `current=0`, `total=0`, and high CPU as proof of deadlock during this phase. Confirm that the process is alive and that the installed release still has the documented long-scan behavior

After import, prove OpenCode coverage with both archive counts and a filtered search

```bash
cass search "known OpenCode topic" --agent opencode --robot --mode lexical --limit 5 --fields summary
```

## Derived-index repair

Do not rebuild solely because index age exceeds the default 30-minute threshold. In CASS 0.6.25, a successful doctor rebuild does not refresh the timestamp used for that age check

If the canonical database is readable but the lexical index remains unusable or its fingerprint differs after the bounded refresh loop, start with read-only diagnosis

```bash
cass triage --json
cass doctor --json --check
cass doctor repair --dry-run --json
```

Treat a dry run as authorized only when it returns a non-empty plan fingerprint and explicit actions. If it returns no plan, reports unchecked archive coverage, or requests operator review, stop without mutation

Before applying a plan

- confirm every action affects derived assets only
- obtain user approval for the mutating repair
- run the exact apply command emitted by the immediately preceding dry run
- restart the mandatory pre-use loop and require every gate to pass

Never invent or reuse a plan fingerprint

### CASS 0.7.1 interrupted-rebuild defect

CASS 0.7.1 can fail every incremental, full, and fingerprinted lexical rebuild with `invalid scalar Quill index state: duplicate live document id` after an interrupted or partial rebuild. This is [upstream issue #440](https://github.com/Dicklesworthstone/coding_agent_session_search/issues/440). The fix landed on `main` after the 0.7.1 tag and is not part of 0.7.1

When this exact failure repeats on 0.7.1, stop retrying. Do not install an unreleased build. Wait for the next stable release, upgrade, then restart the mandatory pre-use loop and prove both structural and functional gates

## Corrupt archive recovery

Before replacing a corrupt archive

- Record the data directory from `cass status --json`
- Move the entire directory to a timestamped backup path rather than deleting it
- Attempt CASS's read-only archive recovery first
- Rebuild from provider logs only when archive recovery cannot proceed
- Keep the backup until coverage is proven non-decreasing

## Shared-agent distribution

The CLI binary is shared through the shell `PATH`. Each agent also needs the CASS skill in its own skill directory

In this chezmoi setup, edit only the managed source skill. Apply chezmoi, then compare the rendered copies for Pi, Codex, Claude Code, OpenCode, and Agents

Do not edit applied copies under `~/.config`, `~/.codex`, `~/.pi`, or `~/.agents`
