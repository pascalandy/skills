# Delegate to a headless CLI

Use this execution workflow only for `use headless-delegation with <cli> to <task>`, where the target is `claude`, `codex`, `opencode`, or `pi`. Other headless questions go directly to the matching CLI reference through [SKILL.md](../../SKILL.md).

## Execute

1. Preserve the requested CLI and model. Load its reference below for flags, permissions, and output handling
2. Select the target workdir explicitly. Do not launch into an agent's runtime-state directory. For a different PR checkout or concurrent edits, use a separate clone or worktree
3. State the task, permitted changes, expected result, and required checks in the prompt. Use an argument array or shell-safe quoting for generated input
4. Choose permissions from the CLI reference within the user's authorization. Headless mode alone does not imply read-only access. Do not broaden permissions to work around a failure without authorization
5. Launch through the current harness's process API, using ordinary pipes for non-interactive commands. Use a PTY only when the installed CLI or runner demonstrably requires one
6. Monitor until exit or the caller's deadline. Capture stdout, stderr, exit status, and the result. For background execution, retain the process handle and report how to inspect or stop it using the actual harness tools
7. Verify the requested outcome against the report and relevant artifacts. For edits, inspect the diff and run appropriate checks. Report failures or unmet checks; do not silently replace a failed delegation with your own implementation

| CLI | Authoritative run procedure |
| --- | --- |
| Claude Code | [Print mode, permissions, output, and sessions](../claude/MetaSkill.md) |
| Codex | [Exec, diff reviews, and verification](../codex/MetaSkill.md) |
| OpenCode | [Run mode, agents, and server attachment](../opencode/MetaSkill.md) |
| Pi | [Print mode, tool restrictions, and JSON output](../pi/MetaSkill.md) |

Stop a timed-out process before retrying. Inspect partial work first, then retry only after changing the cause. Keep concurrent writers in separate worktrees.

For maintenance, follow the [update checklist](../UPDATE.md).
