# Run Claude Code headlessly

Use `claude -p` or `claude --print` from the target repository with ordinary pipes. Check `claude --help`, `claude --version`, and `claude auth status --text` before relying on installed behavior. The official [headless guide](https://code.claude.com/docs/en/headless) owns non-interactive behavior; the [CLI reference](https://code.claude.com/docs/en/cli-reference) owns startup options. Output format does not replace `-p`.

## Review run

Prepare an absolute prompt-file path with the review scope and criteria. This complete example selects Opus 5.5 at `xhigh`, captures raw events, and extracts the final answer:

```bash
repo="/absolute/path/to/repository"
prompt_file="/absolute/path/to/reviewer-prompt.md"
review_dir="$(mktemp -d /tmp/claude-review.XXXXXX)" || exit 1

review_status=0
(
  cd "$repo" || exit 1
  claude --print \
    --model claude-opus-5-5 \
    --setting-sources user \
    --settings '{"disableAllHooks":true,"env":{"CLAUDE_CODE_EFFORT_LEVEL":"xhigh"}}' \
    --permission-mode dontAsk --permission-prompts none \
    --tools "Read,Grep,Glob" \
    --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
    --no-session-persistence \
    --output-format stream-json --verbose \
    < "$prompt_file" \
    > "$review_dir/events.jsonl" \
    2> "$review_dir/stderr.log"
) || review_status=$?

if ! jq -ers '[.[] | select(.type == "result")] | last | .result |
  select(type == "string" and length > 0)' \
  "$review_dir/events.jsonl" > "$review_dir/result.md"; then
  if [ "$review_status" -eq 0 ]; then review_status=1; fi
fi

printf 'Exit status: %s\nReview files: %s\n' \
  "$review_status" "$review_dir"
```

Requires `jq` and access to [Opus 5.5](https://code.claude.com/docs/en/model-config). `result.md` holds the complete final answer; `events.jsonl` keeps execution metadata and failures. [Verify completion](#verify-completion) before trusting the answer.

Print mode loads the reviewed repository's `.claude/settings.json` without a trust prompt, so that file can change the environment, including the API endpoint and effort. `--setting-sources user` skips project and local settings. `CLAUDE_CODE_EFFORT_LEVEL` overrides `--effort` and can come from the shell or any settings file; the value in `--settings` takes precedence over both, so the recipe pins effort there.

This tool set cannot run tests or obtain a Git diff through Bash. Include the diff in the prompt file when needed.

## Permissions

Choose an explicit permission strategy. `dontAsk` denies calls that would prompt; it does not create a filesystem sandbox. Put an inline prompt before variadic flags such as `--tools` and `--allowedTools`.

| Option | Use |
| --- | --- |
| `--permission-mode plan` | Explore without source edits; do not assume it guarantees unattended completion |
| `--permission-mode acceptEdits` | Approve edits; other operations may still need permission |
| `--permission-mode dontAsk` | Deny operations that would prompt |
| `--permission-prompts none` | Do not wait for a permission host; requires v2.1.259 or later |
| `--allowedTools` | Pre-approve specified tools or command rules |
| `--tools` | Restrict which built-in tools are available |
| `--disallowedTools` | Deny named tools |
| `--permission-mode auto` | Automatic approval decisions, subject to availability and policy |
| `--permission-mode bypassPermissions` | Bypass permission checks only with authorization in an isolated runner |

Use [permission documentation](https://code.claude.com/docs/en/permissions) for rule syntax. Diagnose denied tools before retrying; do not default to bypass.

Permission mode and allow rules still govern calls when prompts are disabled. `--tools` restricts built-in tools, not startup hooks or configured MCP servers. Use `--strict-mcp-config` with an explicit MCP configuration when the run must limit those servers.

## Input and output

```bash
claude -p "Review this diff and inspect related files" \
  --permission-mode dontAsk --permission-prompts none \
  --tools "Read,Grep,Glob" --output-format json \
  < diff.patch > result.json 2> review.stderr.log
```

| Output format | Result |
| --- | --- |
| `text` | Plain response text |
| `json` | One result object with session metadata and response text in `result` |
| `stream-json` | JSONL events ending with a `result` record; use `--verbose` |

The [review run](#review-run) uses streaming output and extracts its final `result` record.

Add `--include-partial-messages` when the consumer needs token deltas. Use `--output-format json --json-schema '<schema>'` for schema-constrained output in the result object's `structured_output` field, not its `result` field.

## Verify completion

Preserve the process exit status and inspect the final result. Invalid flags fail on stderr; failures during a run can appear on stdout. Check `is_error` and `permission_denials` in the JSON result or the stream's final `result` record. Use one of these formats when automation must detect denied tools; text has no structured denial record. If required plugins or MCP servers are missing or failed in `system/init`, report that limitation even when the process exits 0.

## Models, limits, and context

| Option | Use |
| --- | --- |
| `--model <model>` | Select the requested alias or exact model |
| `--effort <level>` | Select a level supported by the model and installed CLI; `CLAUDE_CODE_EFFORT_LEVEL` overrides it |
| `--fallback-model <model>` | Allow substitution only when the caller permits it |
| `--max-turns <n>`, `--max-budget-usd <amount>` | Bound the run |
| `--append-system-prompt <text>` | Add instructions while retaining the default prompt |
| `--system-prompt <text>` | Replace the default prompt |
| `--add-dir <path>` | Include another directory |
| `--mcp-config <file>`, `--strict-mcp-config` | Select MCP configuration |
| `--settings <file-or-json>` | Supply settings |
| `--agent <name>`, `--agents <json>` | Select or define an agent |
| `--worktree <name>` | Use an isolated Git worktree |

Use `--bare` for controlled scripted runs when you can supply context and authentication explicitly. It skips normal discovery and does not use Anthropic subscription credentials. For subscription-authenticated runs, keep normal mode with the review run's `--setting-sources user` and `--settings`. Supply required allow rules on the CLI rather than relying on an untrusted project's rules; see [workspace trust](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder).

## Sessions

Keep `-p` and the chosen permission/tool options on every resumed invocation. Prefer an explicit session ID over `--continue` when other runs share the directory.

- `--resume <id>`: resume a known session
- `--continue`: continue the latest session
- `--fork-session` with resume or continue: retain history under a new ID
- `--no-session-persistence`: one-off run without a saved session

For maintenance, follow the [update checklist](../UPDATE.md).
