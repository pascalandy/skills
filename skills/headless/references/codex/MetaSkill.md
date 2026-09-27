# Run Codex headlessly

Use `codex exec` for a task that must finish without the interactive Codex UI. The calling agent owns the request, process supervision, and verification. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) own current CLI behavior; check `codex exec --help` on the installed version before relying on an option.

## Prepare the run

1. Check `codex --version`, `codex exec --help`, and `codex login status`. On a runner without saved authentication, provide `CODEX_API_KEY` only to the Codex invocation through the runner's secret facility. Keep credentials out of prompts, logs, and repository files. For GitHub Actions, follow the [Codex GitHub Action guidance](https://learn.chatgpt.com/docs/non-interactive-mode#authenticate-in-automation)
2. Set the target repository with `-C <path>`. Inspect its instructions and current changes before delegating edits. Codex normally requires a Git repository; use `--skip-git-repo-check` only for an intentionally trusted directory outside one
3. Give concurrent editing runs separate worktrees or checkouts. State the task, permitted paths, expected result, and checks in the prompt. Use the caller's process API or an argument array when passing generated or untrusted text
4. Choose `-s read-only` for inspection or `-s workspace-write` for edits. Set `-c 'approval_policy="never"'` for an unattended run. Broader access or approval bypass requires an authorized, isolated runner. Do not use deprecated `--full-auto` in new commands

## Run and observe

Pass a complete prompt on stdin:

```bash
codex exec -C /path/to/repo -s read-only -c 'approval_policy="never"' --json - < prompt.md
```

For edits, use `-s workspace-write`. Add `-o result.md` when the caller needs the final message in a file. `--json` emits JSONL events on stdout; without it, stdout contains the final message and progress goes to stderr. No PTY is needed. Retain stderr and the exit status for diagnosis.

Watch the process until it exits or the caller's deadline expires. With `--json`, capture the `thread_id` from `thread.started`, inspect `turn.completed`, `turn.failed`, and `error`, and read the final agent message. A started thread or zero exit code alone does not prove the task succeeded. Inspect the actual diff and run relevant checks before reporting completion.

If Codex fails or asks for unavailable access, report the error and unmet task. Retry only after changing the cause; do not silently widen the sandbox or repeat a write task whose result is uncertain. Terminate a timed-out child and inspect partial changes before another attempt.

## Continue or structure a task

- Resume a persisted run with `codex exec resume <SESSION_ID> "<follow-up>"`. Prefer the captured ID over `--last` when other runs may exist. An `--ephemeral` run has no saved session to resume. Check `codex exec resume --help` for the installed version's options
- Use `--output-schema <schema.json>` when downstream code needs a validated final JSON shape; use `--json` when it needs the execution event stream
- Pass `-m <model>` or `-c 'model_reasoning_effort="high"'` only when the task specifies them or the runner has a deliberate model policy. Check local help and current model availability instead of preserving model names from old examples

For maintenance of this reference, follow [the update checklist](references/UPDATE.md).
