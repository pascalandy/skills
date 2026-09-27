# Run Pi headlessly

Use `pi -p` or `pi --print` for a one-shot text response. Check `pi --help` and `pi --list-models` for installed flags and models. The official [CLI integration guide](https://pi.dev/docs/latest/cli-integration) explains modes; the [CLI reference](https://pi.dev/docs/latest/cli) owns startup options.

## Choose a mode

| Invocation | Output and lifetime | Use |
| --- | --- | --- |
| `pi -p` / `pi --print` | Final assistant text on stdout, then exit | A review report or one-shot answer |
| `pi --mode json` | JSONL events on stdout, then exit | Structured progress and tool activity |
| `pi --mode rpc` | JSONL commands on stdin; responses and events on stdout until shutdown | Bidirectional process control |

With terminal stdin and stdout, plain `pi` opens the TUI. Redirecting either stream selects print mode unless JSON or RPC was selected. Prefer an explicit mode in scripts; `--mode text` alone does not force one-shot execution. JSON mode needs no additional `-p` and does not constrain the model's answer to a JSON schema.

## Review or execute

For a complete review run, prepare an absolute prompt-file path that defines the scope, criteria, and expected findings. This example selects GLM 5.3 Flash through OpenCode Go and requests `max` reasoning. Pi 0.87.1 on `mbp` lists `opencode-go/glm-5.3-flash` with thinking enabled. Before running elsewhere, confirm it with `pi --list-models glm-5.3-flash` and check provider authentication. Pi [clamps thinking to supported levels](https://pi.dev/docs/latest/cli#models); `--thinking max` requests that level but does not prove the provider uses effective `max`.

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
review_dir="$(mktemp -d /tmp/pi-review.XXXXXX)" || exit 1

review_status=0
(
  cd "$repo" || exit 1
  pi --print \
    --model opencode-go/glm-5.3-flash \
    --thinking max \
    --no-session --no-extensions \
    --tools read,grep,find,ls \
    < "$prompt_file" \
    > "$review_dir/result.md" \
    2> "$review_dir/stderr.log"
) || review_status=$?

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

`result.md` contains the final assistant text. The failure handler works under `set -e`; a standalone script should end with `exit "$review_status"` after inspecting the report. Print mode alone does not restrict tools: this allowlist excludes shell execution and edits. Supply a diff in the prompt file when needed; this tool set cannot run tests or obtain a diff through Bash.

For an event stream, select `--mode json`:

```bash
pi --mode json --model opencode-go/glm-5.3-flash --thinking max \
  --no-session --no-extensions --tools read,grep,find,ls \
  "Review this diff and inspect related files" \
  < diff.patch > events.jsonl 2> review.stderr.log
```

## Model and session options

| Option | Use |
| --- | --- |
| `--model <provider/model>` | Select a model verified with `--list-models` |
| `--thinking <level>` | Select a supported reasoning level from installed help |
| `--session <path-or-id>` | Resume a specific session |
| `--continue` | Continue the latest session |
| `--no-session` | Avoid saving a one-off session |
| `--append-system-prompt <text-or-file>` | Add instructions |
| `--prompt-template <path>` | Load a prompt template |
| `--no-tools` | Disable tools |
| `--tools <names>` | Allow only the named tools |
| `--no-extensions` | Disable extension discovery |

Pin the model and reasoning only when requested or required by the runner's policy. Prefer explicit session IDs over latest-session selection when runs overlap.

## Verify output

Preserve the process exit status and keep stderr separate from the report or event stream.

- Print mode sends errors to stderr and exits nonzero when the final assistant response stops with `error` or `aborted`
- JSON mode can exit 0 despite an assistant error or abort. Consume the full stream and inspect the final assistant message's `stopReason` and tool failures. `message_end.message` is authoritative; `message_update` contains deltas. Wait through `agent_settled`, since `agent_end` can precede retries or queued work
- RPC prompt acceptance is not completion. Continue consuming events through `agent_settled`; see the [RPC protocol](https://pi.dev/docs/latest/rpc)

The [JSON event reference](https://pi.dev/docs/latest/json) owns event shapes and framing. These semantics describe the latest official docs; check the installed version's docs before depending on particular events. Completion still requires inspecting the review findings or changed artifacts.

For maintenance, follow the [update checklist](../UPDATE.md).
