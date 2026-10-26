# Run Pi headlessly

Use `pi -p` or `pi --print` for a one-shot text response. Check `pi --help` and `pi --list-models` for installed flags and models. The official [CLI integration guide](https://pi.dev/docs/latest/cli-integration) explains modes. The [CLI reference](https://pi.dev/docs/latest/cli) describes startup options.

## Choose a mode

| Invocation | Output and lifetime | Use |
| --- | --- | --- |
| `pi -p` / `pi --print` | Final assistant text on stdout, then exit | A review report or one-shot answer |
| `pi --mode json` | Newline-delimited JSON (JSONL) events on stdout, then exit | Structured progress and tool activity |
| `pi --mode rpc` | Remote procedure call (RPC) commands as JSONL on stdin. Responses and events on stdout until shutdown | Bidirectional process control |

With terminal stdin and stdout, plain `pi` opens the text user interface (TUI). Redirecting either stream selects print mode unless you selected JSON or RPC mode. Prefer an explicit mode in scripts. `--mode text` alone does not force one-shot execution. JSON mode needs no additional `-p`. It does not constrain the model's answer to a JSON schema.

## Review or execute

For a review, prepare an absolute prompt-file path with the scope, criteria, and expected findings.
Read `provider`, `model`, and `reasoning-level` from the `[pi]` table of [config.toml](../../config.toml), unless the request specifies them. Pass the values as `--model <provider>/<model>` and `--thinking <reasoning-level>`. Several providers can serve one model.

COST: Confirm the selected provider before a live run. That provider charges its associated account for the request.

Before the run, confirm the model with `pi --list-models <model>`. Also check authentication for the selected provider. Pi [limits thinking to supported levels](https://pi.dev/docs/latest/cli#models). The `--thinking` flag requests a level but does not prove that the provider uses it.

For Opus 5.5 paid through OpenRouter, check the connection and model before using the review recipe below:

```bash
pi auth check --provider openrouter --json
pi --list-models openrouter/anthropic/claude-opus-5.5
```
Require a `status` value of `ready` and a matching provider and model row. Warnings about other models do not invalidate a matching OpenRouter row. The authentication check alone does not prove that a live request will work.

In the recipe, set `model="openrouter/anthropic/claude-opus-5.5"`. Set `thinking` from the request or `[pi]`. The `claude-code` provider uses the Claude Code connection. The OpenRouter provider charges the OpenRouter account. If either check fails, report the failure without selecting another provider.

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
model="<provider>/<model>"       # from [pi] in config.toml
thinking="<reasoning-level>"
review_dir="$(mktemp -d /tmp/pi-review.XXXXXX)" || exit 1
review_status=0
(
  cd "$repo" || exit 1
  pi --print \
    --model "$model" \
    --thinking "$thinking" \
    --no-session --no-extensions --no-mcp --no-approve \
    --tools read,grep,find,ls \
    < "$prompt_file" \
    > "$review_dir/result.md" \
    2> "$review_dir/stderr.log"
) || review_status=$?
if [ "$review_status" -eq 0 ] && [ ! -s "$review_dir/result.md" ]; then
  review_status=1
fi
printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```
`result.md` contains the final assistant text. Pi exits 0 when that text is empty, so the recipe checks the file.

The `--no-approve` flag ignores the reviewed repository's trust-gated settings, extensions, and skills. Print mode otherwise loads them after a saved trust decision or when `defaultProjectTrust: "always"` permits them.

Print mode alone does not restrict tools. The built-in allowlist excludes shell execution and edits. The `--no-mcp` flag excludes Model Context Protocol (MCP) tools. The four allowed tools cannot run tests or obtain a diff through Bash. If the review needs a diff, include it in the prompt file.

For an event stream, select `--mode json`:

```bash
pi --mode json --model "$model" --thinking "$thinking" \
  --no-session --no-extensions --no-mcp --no-approve --tools read,grep,find,ls \
  "Review this diff and inspect related files" \
  < diff.patch > events.jsonl 2> review.stderr.log
```

For OpenRouter Opus, use JSON mode when you must verify the billing route. In the final assistant `message_end.message`, require `provider` to equal `openrouter`. Require `model` to equal `anthropic/claude-opus-5.5`. Print mode outputs only text, so its answer cannot prove the provider.

## Model and session options

| Option | Use |
| --- | --- |
| `--model <provider/model>` | Select a model verified with `--list-models` |
| `--thinking <level>` | Select a supported reasoning level from installed help |
| `--session <path-or-id>` | Resume a specific session |
| `--continue` | Continue the latest session. When runs overlap, prefer `--session` with an explicit ID |
| `--no-session` | Avoid saving a one-off session |
| `--append-system-prompt <text-or-file>` | Add instructions |
| `--prompt-template <path>` | Load a prompt template |
| `--no-tools` | Disable tools |
| `--tools <names>` | Allow named tools. MCP tools remain unless `--no-mcp` disables them |
| `--no-extensions` | Disable extension discovery |
| `--no-mcp` | Disable MCP servers and their tools |

## Verify output

Preserve the process exit status and keep stderr separate from the report or event stream.

- Print mode sends errors to stderr and exits nonzero when the final assistant response stops with `error` or `aborted`
- JSON mode can exit 0 despite an assistant error or abort. Inspect the full stream for tool failures and the final assistant message's `stopReason`. `message_end.message` is authoritative. The `message_update` events contain deltas. Wait through `agent_settled` because `agent_end` can precede retries or queued work
- RPC prompt acceptance is not completion. Continue reading events through `agent_settled`. See the [RPC protocol](https://pi.dev/docs/latest/rpc)

The [JSON event reference](https://pi.dev/docs/latest/json) describes event shapes and framing. These rules describe the latest official docs. Check the installed version's docs before you depend on particular events. Completion still requires you to inspect the review findings or changed artifacts.
