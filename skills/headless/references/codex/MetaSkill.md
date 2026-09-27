# Run Codex headlessly

Use `codex exec` for a task that must finish without the interactive Codex UI. The calling agent owns the request, process supervision, and verification. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) own current CLI behavior; check `codex exec --help` on the installed version before relying on an option.

## Prepare the run

1. Check `codex --version`, `codex exec --help`, and `codex login status`. On a runner without saved authentication, provide `CODEX_API_KEY` only to the Codex invocation through the runner's secret facility. Keep credentials out of prompts, logs, and repository files. For GitHub Actions, follow the [Codex GitHub Action guidance](https://learn.chatgpt.com/docs/non-interactive-mode#authenticate-in-automation)
2. Set the target repository with `-C <path>`. Inspect its instructions and current changes before delegating edits. Codex normally requires a Git repository; use `--skip-git-repo-check` only for an intentionally trusted directory outside one
3. Give concurrent editing runs separate worktrees or checkouts. State the task, permitted paths, expected result, and checks in the prompt. Use the caller's process API or an argument array when passing generated or untrusted text
4. Choose `-s read-only` for inspection or `-s workspace-write` for edits. Set `-c 'approval_policy="never"'` for an unattended run. Broader access or approval bypass requires an authorized, isolated runner. Do not use `--full-auto`; CLI 0.157.1 rejects it
5. Close stdin with `< /dev/null` whenever the prompt is an argument. Codex reads piped stdin until EOF and appends it to the prompt, and an agent harness usually leaves stdin open, so the run prints `Reading additional input from stdin...` and hangs. Omit the redirect only when stdin carries the prompt or deliberate context

## Choose a run

For an inline inspection task, keep the workspace read-only and use the configured model:

```bash
codex exec -C /path/to/repo -s read-only -c 'approval_policy="never"' "Review src/auth.ts for race conditions. Report findings with file and line." < /dev/null
```

For a dedicated diff review, use `codex exec review`. Confirm the checkout and branch, fetch the base if you need its latest remote state, and keep the checkout stable during the review. This example explicitly selects GPT-6 Sol at High reasoning; omit the model and reasoning options to use configured defaults. Each run gets a separate output directory:

```bash
repo="/absolute/path/to/repository"
review_dir="$(mktemp -d /tmp/codex-review.XXXXXX)" || exit 1

review_status=0
codex exec \
  -C "$repo" \
  review \
  --base origin/main \
  -m gpt-6-sol \
  -c 'model_reasoning_effort="high"' \
  -c 'sandbox_mode="read-only"' \
  -c 'approval_policy="never"' \
  --ephemeral --json \
  -o "$review_dir/result.md" \
  < /dev/null \
  > "$review_dir/events.jsonl" \
  2> "$review_dir/stderr.log" || review_status=$?

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

The failure handler preserves the exit status even with `set -e`. In a standalone script, finish with `exit "$review_status"` after processing the report so `printf` does not hide a failed run. Follow [Observe and verify](#observe-and-verify) before treating the review as complete.

Choose exactly one review target:

| Target | Scope |
| --- | --- |
| `--base origin/main` | Changes against the specified base branch in this checkout |
| `--uncommitted` | Staged, unstaged, and untracked changes |
| `--commit <SHA>` | Changes introduced by one commit |
| Custom prompt | Review instructions supplied as an argument or through `-` on stdin |

These targets conflict with one another. For an audit with custom criteria and an explicit diff scope, use ordinary `codex exec` with a prompt file as shown below; put the comparison and criteria in that prompt.

The review commands do not accept `-s` and otherwise inherit the configured sandbox, which can be `workspace-write`. Pin `sandbox_mode` as shown. Read-only mode can block tests that write build artifacts; run those separately or use an explicitly authorized writable checkout. On CLI 0.157.1, `codex exec review` accepts `-m`, `--json`, and `-o`, while `codex review` accepts none of them. Use `codex review` for a simple terminal report with the configured review model. Check both commands' `--help` on the installed version.

For file edits, use `workspace-write`. The first command keeps the configured model; the second selects Astra and High reasoning:

```bash
codex exec -C /path/to/repo -s workspace-write -c 'approval_policy="never"' "Fix the bug in src/auth.ts. Run the relevant tests and report results." < /dev/null
codex exec -C /path/to/repo -s workspace-write -c 'approval_policy="never"' -m gpt-6-astra -c 'model_reasoning_effort="high"' "Refactor src/auth.ts. Limit edits to that file and run the relevant tests." < /dev/null
```

To pass the complete prompt from a Markdown file, use `-` for stdin. Change the sandbox to `workspace-write` if that prompt authorizes edits. To add context to an inline prompt, pipe it in; Codex appends it as a `<stdin>` block:

```bash
codex exec -C /path/to/repo -s read-only -c 'approval_policy="never"' --json - < prompt.md
git -C /path/to/repo diff main | codex exec -C /path/to/repo -s read-only -c 'approval_policy="never"' "Review this diff for regressions."
```

`-m` also accepts `gpt-6-sol` and `gpt-6-luna` when available to the account. Check the [current Codex model list](https://learn.chatgpt.com/docs/models) for model names and supported reasoning levels; an installed CLI's catalog can differ by sign-in and rollout. Omit `-m` and `model_reasoning_effort` to use the configured defaults.

## Observe and verify

Add `-o result.md` when the caller needs the final message in a file. `--json` emits JSONL events on stdout; without it, stdout contains the final message and progress goes to stderr. No PTY is needed. Retain stderr and the exit status for diagnosis. The stderr header names the effective `model`, `sandbox`, and `approval`; check it when a setting matters.

Watch the process until it exits or the caller's deadline expires. With `--json`, capture the `thread_id` from `thread.started`, inspect `turn.completed`, `turn.failed`, and `error`, and read the final agent message. A started thread or zero exit code alone does not prove the task succeeded; a read-only run asked to edit still exits 0. Inspect the actual diff and run relevant checks before reporting completion.

If Codex fails or asks for unavailable access, report the error and unmet task. Retry only after changing the cause; do not silently widen the sandbox or repeat a write task whose result is uncertain. Terminate a timed-out child and inspect partial changes before another attempt.

## Continue or structure a task

- Resume a persisted run with `codex exec resume <SESSION_ID> "<follow-up>" < /dev/null`. Prefer the captured ID over `--last` when other runs may exist. An `--ephemeral` run has no saved session to resume. Check `codex exec resume --help` for the installed version's options
- Use `--output-schema <schema.json>` when downstream code needs a validated final JSON shape; use `--json` when it needs the execution event stream
- Pass `-m <model>` or `-c 'model_reasoning_effort="high"'` only when the task specifies them or the runner has a deliberate model policy

For the complete `codex exec` flag map and help commands, read [flag lookup](references/FLAGS.md). For maintenance, follow the [update checklist](../UPDATE.md).
