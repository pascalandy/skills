---
name: "headless"
description: "Use when running `codex exec`, Claude Code, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them."
---

# Headless CLI agents

Load only the reference for the requested path:

- For `codex exec` or `headless-codex`, read [Run Codex headlessly](references/codex/MetaSkill.md)
- For Claude Code or `headless-claude`, read [Claude Code](references/claude/MetaSkill.md)
- For OpenCode or `headless-opencode`, read [OpenCode](references/opencode/MetaSkill.md)
- For Pi or `headless-pi`, read [Pi](references/pi/MetaSkill.md)
- For skill maintenance, follow the [update checklist](references/UPDATE.md)

Read the [glossary](references/GLOSSARY.md) only when its terminology is needed. For current CLI behavior, check the installed command's `--help` and its official documentation. Delegation policy belongs to the calling workflow, not this skill.

## Capture a review

Each reference's review recipe applies these rules:

- Give every run its own `mktemp -d` directory, with the answer, events, and stderr in separate files
- Record the exit status with `|| review_status=$?`, which also works under `set -e`. A standalone script ends with `exit "$review_status"` after inspecting the answer
- Count an empty answer as a failure even when the process exits 0
- Read the complete answer before deciding whether the review succeeded; a zero exit or an event log alone proves nothing
- The recipes pin a model and reasoning level as examples. Keep a pin only when the task or runner policy requires it; otherwise omit both options to use configured defaults
- Leave the reviewed artifact and checkout unchanged until the review exits, whether it covers a diff, plan, or document; otherwise the answer describes a stale revision
- A read-only reviewer cannot run commands that write caches or build output, such as `uv`, `uvx`, and pytest. Run the tests yourself and include their output in the prompt
- Treat a one-line "no findings" answer from a run without explicit criteria or test output as weak evidence; rerun with both

RTK leaves commands that redirect their output to a file unchanged, so the recipes capture everything. To read JSON output under RTK, use `rtk proxy jq ...`; `rtk jq` shortens long answers.

## Wait for a run

Start a long run, such as a review recipe, as one background command and wait for the harness's completion notification; a review can outlast a foreground command timeout. The recipes block until the agent exits, so they need no watcher. Without completion notifications, start it with `&`, save `$!` as `pid`, and poll `kill -0 "$pid"` from a background loop such as `until ! kill -0 "$pid" 2>/dev/null; do sleep 15; done`. Poll the process, not the answer file, which may appear only at exit. Never poll with `pgrep -f`, whose pattern also matches the polling command.
