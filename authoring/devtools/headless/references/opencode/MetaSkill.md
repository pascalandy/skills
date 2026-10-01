# Run OpenCode headlessly

Use `opencode run` to send a prompt and print the reply without opening the TUI. Check `opencode --version` and `opencode run --help` first. OpenCode v2 ships as the `@opencode/cli` npm package and v1 as `opencode-ai`; their flags and agent formats differ, so do not upgrade a runner implicitly. The [v2 run documentation](https://opencode.ai/v2/docs/cli/commands/#run) and the [v1 CLI reference](https://opencode.ai/docs/cli/) own current behavior.

## Define a read-only reviewer

Headless mode and a request to avoid edits do not enforce read-only access, and v2's built-in `plan` agent still offers edit, write, and shell tools. Define a user-level agent that denies them. Also deny subagents, which run with their own permissions. For v2, save this as `~/.config/opencode/agents/reviewer.md`:

```markdown
---
description: "Read-only code reviewer"
permissions:
  - action: edit
    resource: "*"
    effect: deny
  - action: shell
    resource: "*"
    effect: deny
  - action: subagent
    resource: "*"
    effect: deny
---
Review the requested changes. Report findings with file and line references.
```

V1 reads the same path but uses `mode: primary` and a `permission` map with `edit`, `bash`, and `task` set to `deny`; see the [v1 agents reference](https://opencode.ai/docs/agents/).

## Complete review run

Prepare an absolute prompt-file path with scope, criteria, and expected findings. Select a model from `opencode models` and configure provider authentication beforehand; in CI, provide the API key through the runner's secret mechanism. The `#high` suffix selects a v2 model variant, such as a reasoning level; variants are provider-specific.

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
model="anthropic/claude-sonnet-4-5#high"
review_dir="$(mktemp -d /tmp/opencode-review.XXXXXX)" || exit 1

review_status=0
(
  cd "$repo" || exit 1
  opencode run \
    "Follow the attached review instructions. Report findings; do not modify files." \
    --standalone \
    --model "$model" \
    --agent reviewer \
    --file "$prompt_file" \
    < /dev/null \
    > "$review_dir/result.md" \
    2> "$review_dir/stderr.log"
) || review_status=$?

if [ "$review_status" -eq 0 ] && [ ! -s "$review_dir/result.md" ]; then
  review_status=1
fi

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

Keep the message before `--file`: v1 reads every argument after `--file` as another file. `--standalone` starts a private server that receives the invocation's environment and exits with the run. On v1, drop `--standalone` and pass the variant as `--variant high` instead of the `#high` suffix.

`result.md` preserves command stdout, including the reply; do not assume it is a final-message-only protocol. OpenCode exits 0 when the reply is empty, so the recipe checks for one. Besides the pinned model, OpenCode sends the prompt and attached files to a small model from the same provider to title the session, so both models see the review material.

## Output and follow-up runs

- Add `--format json` and redirect stdout to `events.jsonl` when a consumer needs newline-delimited events. Keep stderr separate
- JSON mode emits events, not a single final-answer object. The v2 run page does not define event fields or completion/error records; verify that version's schema before writing an answer extractor. Do not copy Claude or Pi event selectors
- Use `--file <path>` repeatedly to attach review material
- Prefer `--session <id>` over `--continue`, which picks the latest session, when concurrent runs make that selection ambiguous

## Existing servers

Without `--standalone`, v2 commands use a background service and start one if none is running; it keeps running after the command exits. Commands that talk to a server accept `--server <url>`. Use that instead of `--standalone` only when intentionally targeting an existing server. Provider credentials must be available to that server; changing the client's environment does not configure an already-running process.

`opencode serve` starts an API and web server. Do not start or reconfigure one solely for a one-shot review when standalone mode suffices. Consult [v2 server commands](https://opencode.ai/v2/docs/cli/commands/#serve) for lifecycle and binding options.

For maintenance, follow the [update checklist](../UPDATE.md).
