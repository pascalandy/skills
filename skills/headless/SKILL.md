---
name: "headless"
description: "Use when an agent needs to run a bounded Codex task through the non-interactive `codex exec` CLI, including delegated edits, read-only analysis, or machine-readable automation. This skill covers Codex only."
---

# Run Codex headlessly

Use `codex exec` for a task that must finish without the interactive Codex UI. The calling agent owns the work request, process supervision, and verification of the result. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands) own the current CLI behavior; check `codex exec --help` on the installed version before relying on an option.

## Prepare the run

1. Check that `codex` is installed and authenticated. `codex --version`, `codex exec --help`, and `codex login status` expose the local state without starting a task. In automation outside a signed-in machine, provide `CODEX_API_KEY` only to the Codex process through the runner's secret facility. Keep credentials out of prompts, logs, and repository files
2. Set the target repository with `-C <path>`. Check its instructions and current changes before delegating edits. Codex normally requires a Git repository; use `--skip-git-repo-check` only for an intentionally trusted non-repository directory
3. Give concurrent editing runs separate worktrees or checkouts. Name the task, permitted paths, expected result, and any checks in the prompt. Use the caller's process API or an argument array when the prompt contains generated or untrusted text
4. Choose the smallest sandbox that can complete the task: `-s read-only` for inspection, `-s workspace-write` for edits. Set `-c 'approval_policy="never"'` so an unattended run does not wait for approval. Broader access or approval bypass requires authorization and an isolated runner. Do not use deprecated `--full-auto` in new commands

## Run and observe

For a read-only task, pass the complete prompt on stdin:

```bash
codex exec -C /path/to/repo -s read-only -c 'approval_policy="never"' --json - < prompt.md
```

For edits, use `-s workspace-write`. Add `-o result.md` when the caller needs the final message in a separate file. `--json` emits JSONL events on stdout; without it, stdout contains the final message and progress goes to stderr. A PTY is not required for this non-interactive command. Keep stderr and the process exit status available for diagnosis.

Watch the process until it exits or the caller's deadline expires. With `--json`, retain the `thread_id` from `thread.started`, inspect `turn.completed`, `turn.failed`, and `error`, and read the final agent message. Do not treat a started thread or a zero exit code alone as proof that the requested files changed or checks passed. Inspect the actual diff and run the relevant verification before reporting completion.

If Codex fails or asks for unavailable access, report the error and the unmet task. Retry only after changing the cause; do not silently widen the sandbox or repeat a write task whose result is uncertain. Terminate a timed-out child process and inspect its partial changes before another attempt.

## Continue or structure a task

- Resume a persisted run with `codex exec resume <SESSION_ID> "<follow-up>"`. Prefer the captured ID over `--last` when other runs may exist. An `--ephemeral` run has no saved session to resume
- Use `--output-schema <schema.json>` when downstream code needs a validated final JSON shape. Use `--json` when it needs the execution event stream; the two outputs serve different purposes
- Pass `-m <model>` or `-c 'model_reasoning_effort="high"'` only when the task specifies them or the runner has a deliberate model policy. Check local help and current model availability instead of preserving model names from old examples

For GitHub Actions, follow the [Codex GitHub Action](https://learn.chatgpt.com/docs/non-interactive-mode#authenticate-in-automation) guidance for credential isolation.
