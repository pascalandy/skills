# Run OpenCode headlessly

Use `opencode run` to send a prompt and print the reply without opening the text user interface (TUI). First check `opencode --version` and `opencode run --help`. OpenCode v2 ships as the `@opencode/cli` npm package. V1 ships as `opencode-ai`. Their flags and agent formats differ, so do not upgrade a runner implicitly. The [v2 run documentation](https://opencode.ai/v2/docs/cli/commands/#run) and [v1 CLI reference](https://opencode.ai/docs/cli/) describe current behavior.

## Define a read-only reviewer

Headless mode and a request to avoid edits do not enforce read-only access. V2's built-in `plan` agent still offers edit, write, and shell tools. Define a user-level agent that denies them. Also deny subagents because they use their own permissions.

DATA LOSS: Check whether `~/.config/opencode/agents/reviewer.md` already exists. Saving this agent over that file removes its current instructions.

For v2, save this agent as `~/.config/opencode/agents/reviewer.md`:

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

V1 reads the same path but uses `mode: primary` and a `permission` map. Set `edit`, `bash`, and `task` to `deny`. See the [v1 agents reference](https://opencode.ai/docs/agents/).

## Complete review run

Prepare an absolute prompt-file path with scope, criteria, and expected findings. Read `provider`, `model`, and `reasoning-level` from the `[opencode]` table of [config.toml](../../config.toml), unless the request specifies them. The provider selects the account that pays because several providers can serve one model. Before the run, confirm the pair with `opencode models` and configure provider authentication. In continuous integration (CI), provide the API key through the runner's secret mechanism. The `#<reasoning-level>` suffix selects a v2 model variant. Variants depend on the provider.

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
model="<provider>/<model>#<reasoning-level>"   # from [opencode] in config.toml
review_dir="$(mktemp -d /tmp/opencode-review.XXXXXX)" || exit 1

review_status=0
(
  cd "$repo" || exit 1
  opencode run \
    "Follow the attached review instructions. Report findings. Do not modify files." \
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

Keep the message before `--file` because v1 reads every later argument as another file. The `--standalone` flag starts a private server. It receives the invocation's environment and exits with the run. On v1, omit `--standalone`. Pass the variant as `--variant <reasoning-level>` instead of a suffix.

`result.md` preserves command stdout, including the reply. Do not assume stdout contains only the final message. OpenCode exits 0 when the reply is empty, so the recipe checks for one. OpenCode also sends the prompt and attached files to a small model from the same provider. That model titles the session, so both models see the review material.

## Output and follow-up runs

- Add `--format json` and redirect stdout to `events.jsonl` when a consumer needs newline-delimited events. Keep stderr separate
- JSON mode emits events, not one final-answer object. The v2 run page does not define event fields or completion and error records. Before you write an answer extractor, verify that version's schema. Do not copy Claude or Pi event selectors
- Use `--file <path>` repeatedly to attach review material
- Prefer `--session <id>` over `--continue`, which picks the latest session, when concurrent runs make that selection ambiguous

## Existing servers

Without `--standalone`, v2 commands use a background service. They start one if none is running. The service keeps running after the command exits. Commands that talk to a server accept `--server <url>`. Use that flag instead of `--standalone` only when you intend to target an existing server. Provider credentials must be available to that server. Changing the client's environment does not configure an already-running process.

`opencode serve` starts an API and web server. If standalone mode suffices, do not start or reconfigure a server for one review. Consult [v2 server commands](https://opencode.ai/v2/docs/cli/commands/#serve) for lifecycle and binding options.

