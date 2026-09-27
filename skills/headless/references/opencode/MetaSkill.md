# Run OpenCode headlessly

Use `opencode run` to send a prompt and print the reply without opening the TUI. The official [v2 run documentation](https://opencode.ai/v2/docs/cli/commands/#run) owns this procedure. Check `opencode --version` and `opencode run --help` before using it.

## Version boundary

The installed OpenCode 1.18.32 exposes `--attach` and `--dir`, but not the v2 `--standalone` or `--server` flags. The v2 recipe below is documentation-verified, not live-tested on that binary. For v1, use the [v1 CLI reference](https://opencode.ai/docs/cli/); do not mix its server flags with v2 examples or upgrade a runner implicitly.

## Complete review run

Prepare an absolute prompt-file path with scope, criteria, and expected findings. Select a model from `opencode models` and an agent whose permissions match the review; v2 lists agents through `opencode debug agents`. Headless mode and a request to avoid edits do not enforce read-only access.

This example uses the model named in the official v2 CI example. Replace it with the intended available model. Configure provider authentication beforehand; in CI, provide the API key through the runner's secret mechanism. `--standalone` starts a private server so it receives the invocation's environment.

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
model="anthropic/claude-sonnet-4-5"
review_agent="your-configured-review-agent"
review_dir="$(mktemp -d /tmp/opencode-review.XXXXXX)" || exit 1

review_status=0
(
  cd "$repo" || exit 1
  opencode run \
    --standalone \
    --model "$model" \
    --agent "$review_agent" \
    --file "$prompt_file" \
    "Follow the attached review instructions. Report findings; do not modify files." \
    < /dev/null \
    > "$review_dir/result.md" \
    2> "$review_dir/stderr.log"
) || review_status=$?

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

`result.md` preserves command stdout, including the reply; do not assume it is a final-message-only protocol. Read the full report and stderr, check the exit status, and verify the outcome. The failure handler works under `set -e`; a standalone script should finish with `exit "$review_status"` after inspection.

Reasoning controls are model- and version-specific. V1 exposes `--variant`; the v2 run page does not specify its reasoning flag. Verify the installed v2 help before adding one rather than assuming `--thinking` changes reasoning effort.

## Output and follow-up runs

- Add `--format json` and redirect stdout to `events.jsonl` when a consumer needs newline-delimited events. Keep stderr separate and follow the skill's unfiltered-capture rule
- JSON mode emits events, not a single final-answer object. The v2 run page does not define event fields or completion/error records; verify that version's schema before writing an answer extractor. Do not copy Claude or Pi event selectors
- Use `--file <path>` repeatedly to attach review material
- `--continue` continues the latest session. Avoid it when concurrent runs make that selection ambiguous; check installed help for explicit session selection

## Existing servers

V2 commands that talk to a server accept `--server <url>`. Use that instead of `--standalone` only when intentionally targeting an existing server. Provider credentials must be available to that server; changing the client's environment does not configure an already-running process.

`opencode serve` starts an API and web server. Do not start or reconfigure one solely for a one-shot review when standalone mode suffices. Consult [v2 server commands](https://opencode.ai/v2/docs/cli/commands/#serve) for lifecycle and binding options.

For maintenance, follow the [update checklist](../UPDATE.md).
