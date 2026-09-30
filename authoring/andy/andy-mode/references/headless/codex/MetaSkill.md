# Run Codex headlessly

Use `codex exec` for a task that must finish without the interactive Codex UI. The calling agent owns the request, process supervision, and verification. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) own current CLI behavior; check `codex exec --help` on the installed version before relying on an option.

## Prepare the run

1. Check `codex --version`, `codex exec --help`, and `codex login status`. On a runner without saved authentication, provide `CODEX_API_KEY` only to the Codex invocation through the runner's secret facility. Keep credentials out of prompts, logs, and repository files. For GitHub Actions, follow the [Codex GitHub Action guidance](https://learn.chatgpt.com/docs/non-interactive-mode#authenticate-in-automation)
2. Set the target repository with `-C <path>`. Inspect its instructions and current changes before delegating edits. Codex normally requires a Git repository; use `--skip-git-repo-check` only for an intentionally trusted directory outside one
3. Give concurrent editing runs separate worktrees or checkouts. State the task, permitted paths, expected result, and checks in the prompt. Use the caller's process API or an argument array when passing generated or untrusted text
4. Choose `-s read-only` for inspection or `-s workspace-write` for edits. Set `-c 'approval_policy="never"'` for an unattended run. Broader access or approval bypass requires an authorized, isolated runner. Use explicit sandbox flags. Installed CLI 0.159.0 rejects `--full-auto`, although the non-interactive guide describes it as a deprecated compatibility flag
5. Close stdin with `< /dev/null` whenever the prompt is an argument. Codex reads piped stdin until EOF and appends it to the prompt, and an agent harness usually leaves stdin open, so the run prints `Reading additional input from stdin...` and hangs. Omit the redirect only when stdin carries the prompt or deliberate context

## Run a review

Use ordinary `codex exec` to give a child agent a review of code, a plan, a document, or supplied context. Default Codex reviews to GPT-6.1 Sol with `xhigh` reasoning. An explicit model or reasoning choice in the request overrides that default. Other tasks use the configured model unless the request selects one.

Write the scope, criteria, and expected findings to a prompt file. Include relevant check results. For a diff, name the comparison in the prompt, such as `git diff origin/main...HEAD`. Confirm the checkout and branch, and fetch the base if you need its latest remote state.

Start a fresh session for an independent review. This recipe leaves web search and local image viewing disabled. The calling agent can enable either before launch as shown in [Choose optional tools](#choose-optional-tools).

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
model="gpt-6.1-sol"
reasoning="xhigh"
web_search="disabled"
view_image=false
review_dir="$(mktemp -d /tmp/codex-review.XXXXXX)" || exit 1

review_status=0
codex exec \
  -C "$repo" \
  -s read-only \
  -m "$model" \
  -c "model_reasoning_effort=\"$reasoning\"" \
  -c "web_search=\"$web_search\"" \
  -c "features.view_image=$view_image" \
  -c 'approval_policy="never"' \
  --ephemeral --json \
  -o "$review_dir/result.md" \
  - \
  2> "$review_dir/stderr.log" \
  > "$review_dir/events.jsonl" \
  < "$prompt_file" || review_status=$?

if [ ! -s "$review_dir/result.md" ] ||
  grep -q '^Review was interrupted' "$review_dir/result.md"; then
  if [ "$review_status" -eq 0 ]; then review_status=1; fi
fi

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

Follow [Observe and verify](#observe-and-verify) before treating the review as complete.

For an inline review, use the same invocation with the prompt as its last argument instead of `-`, and replace `< "$prompt_file"` with `< /dev/null`.

## Choose optional tools

Set the recipe's capability variables before the invocation. For current external facts, set `web_search="live"`. For local screenshots or diagrams, set `view_image=true`. Both may be enabled for the same task. These options change tools available to the child; the read-only filesystem sandbox remains in place.

| Task | Change to the review recipe |
| --- | --- |
| Review local code or supplied text | Keep `web_search="disabled"` and `view_image=false` |
| Verify a claim against current official documentation | Set `web_search="live"` and ask for source links |
| Inspect local screenshots or diagrams | Set `view_image=true` and name the image paths in the prompt |
| Supply an image with the initial prompt | Add `-i /absolute/path/screenshot.png` before `-s read-only` |

For example, to review a design screenshot against current requirements, set `web_search="live"` and `view_image=true`, add `-i`, and supply both the requirements URL and review criteria in the prompt.

`-i` accepts multiple paths. Put another option after its paths so an inline prompt is not consumed as an image path.

`features.view_image` lets the child inspect local images during the task. `-i` supplies an image directly and does not require that tool. Neither option enables image generation. Installed CLI 0.159.0 ignores the `tools.view_image` setting still shown in the configuration reference. Its [feature registry](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/features/src/lib.rs) defines `features.view_image`. Confirm the effective value with `codex -c 'features.view_image=false' features list` or the same command with `true`.

## Delegate another task

Use the same prompt and capture pattern for research, analysis, or implementation. Omit each model or reasoning override that the request does not specify to use its configured default. Keep optional tools disabled unless the calling agent chooses them for that task.

For file edits, use `workspace-write` and inspect the resulting diff. This inline example keeps the configured model:

```bash
codex exec -C /path/to/repo -s workspace-write \
  -c 'approval_policy="never"' \
  -c 'web_search="disabled"' -c 'features.view_image=false' \
  "Fix the bug in src/auth.ts. Limit edits to that file. Run the relevant tests and report results." \
  < /dev/null
```

For a whole prompt in a file, pass `-` as in the review recipe. To add context to an inline prompt, pipe the context into the command. Codex appends it as a `<stdin>` block.

Check the [current Codex model list](https://learn.chatgpt.com/docs/models) for model names and supported reasoning levels; an installed CLI's catalog can differ by sign-in and rollout.

## Observe and verify

Add `-o result.md` when the caller needs the final message in a file. `--json` emits JSONL events on stdout; without it, stdout contains the final message and progress goes to stderr. No PTY is needed. Retain stderr and the exit status for diagnosis. Without `--json`, the stderr header names the effective `model`, `sandbox`, and `approval`; `--json` omits that header.

[Wait for the process](../../../playbooks/headless.md#wait-for-a-run) until it exits or the caller's deadline expires. With `--json`, capture the `thread_id` from `thread.started`, inspect `turn.completed`, `turn.failed`, and `error`, and read the final agent message. A started thread or zero exit code alone does not prove the task succeeded; a read-only run asked to edit still exits 0. Inspect the actual diff and run relevant checks before reporting completion.

If Codex fails or asks for unavailable access, report the error and unmet task. Retry only after changing the cause; do not silently widen the sandbox or repeat a write task whose result is uncertain. Terminate a timed-out child and inspect partial changes before another attempt.

## Continue or structure a task

- Resume or fork only for intentional continuity. A fork preserves the earlier conversation in a new session; it is not an independent review
- Use `codex exec resume <SESSION_ID>` to continue a persisted run and `codex exec fork <SESSION_ID>` to branch its history. Use the captured ID rather than the latest-session shortcut when other runs may exist. An `--ephemeral` run has no saved session to resume or fork
- On installed CLI 0.159.0, resume and fork accept `-m`, `--json`, and `-o` but not `-s` or `--add-dir`. Pin permissions and optional tools again on each follow-up. For a follow-up review, also pass the selected review model and reasoning level from the recipe
- Use `--output-schema <schema.json>` when downstream code needs a validated final JSON shape; use `--json` when it needs the execution event stream

For example, after a persisted analysis run, continue it with explicit permissions and a distinct answer file:

```bash
codex exec resume "$session_id" \
  -c 'sandbox_mode="read-only"' -c 'approval_policy="never"' \
  -c 'web_search="disabled"' -c 'features.view_image=false' \
  -o followup.md "Explain the tradeoff you identified." < /dev/null
```

Replace `resume` with `fork` to preserve the original session while starting a continuation. Check each subcommand's installed help before using its options.

## Codex's special review commands

Ordinary `exec` remains the standard delegation path. `codex exec review` and `codex review` offer code-review shortcuts with built-in criteria. Choose one of `--base`, `--uncommitted`, `--commit`, or a custom prompt. A custom prompt can be an argument or `-` on stdin; it conflicts with those target flags.

Installed CLI 0.159.0 supports `-m`, `--json`, and `-o` on `exec review`, while standalone `review` supports none of them. Set the sandbox through `-c 'sandbox_mode="read-only"'` because these commands lack `-s`. A configured `review_model` can select a different model from the parent session. Use ordinary `exec` for the explicit review model and optional tools described above. The [0.159.0 review thread](https://github.com/openai/codex/blob/rust-v0.159.0/codex-rs/core/src/session/review.rs) disables web search.

For the complete `codex exec` flag map and help commands, read [flag lookup](references/FLAGS.md). For maintenance, follow the [update checklist](../UPDATE.md).
