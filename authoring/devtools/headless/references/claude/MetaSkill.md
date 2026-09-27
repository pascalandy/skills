# Run Claude Code headlessly

Use `claude -p` or `claude --print` from the target repository with ordinary pipes. Check `claude --help`, `claude --version`, and `claude auth status --text` before relying on installed behavior. The official [headless guide](https://code.claude.com/docs/en/headless) owns non-interactive behavior; the [CLI reference](https://code.claude.com/docs/en/cli-reference) owns startup options. Output format does not replace `-p`.

## Permissions

Choose an explicit permission strategy. `dontAsk` denies calls that would prompt; it does not create a filesystem sandbox. For a file review without shell execution, restrict available tools:

```bash
claude -p "Review src/auth.ts for correctness. Report findings with file and line." \
  --permission-mode dontAsk --permission-prompts none --tools "Read,Grep,Glob" \
  < /dev/null > review.md 2> review.stderr.log
```

Put the prompt before variadic flags such as `--tools` and `--allowedTools`. This review cannot run tests or obtain a Git diff through Bash. Supply the diff through stdin, or authorize narrowly scoped shell commands when needed.

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

For streaming output:

```bash
claude -p "Summarize README.md" \
  --permission-mode dontAsk --permission-prompts none \
  --tools "Read,Grep,Glob" --output-format stream-json --verbose \
  < /dev/null > events.jsonl 2> review.stderr.log
```

Add `--include-partial-messages` when the consumer needs token deltas. Use `--output-format json --json-schema '<schema>'` for schema-constrained output in the result object's `structured_output` field, not its `result` field.

## Verify completion

Preserve the process exit status and inspect the final result. Invalid flags fail on stderr; failures during a run can appear on stdout. Check `is_error` and `permission_denials` in the JSON result or the stream's final `result` record. Use one of these formats when automation must detect denied tools; text has no structured denial record. If required plugins or MCP servers are missing or failed in `system/init`, report that limitation even when the process exits 0.

## Models, limits, and context

| Option | Use |
| --- | --- |
| `--model <model>` | Select the requested alias or exact model |
| `--effort <level>` | Select a level supported by the model and installed CLI |
| `--fallback-model <model>` | Allow substitution only when the caller permits it |
| `--max-turns <n>`, `--max-budget-usd <amount>` | Bound the run |
| `--append-system-prompt <text>` | Add instructions while retaining the default prompt |
| `--system-prompt <text>` | Replace the default prompt |
| `--add-dir <path>` | Include another directory |
| `--mcp-config <file>`, `--strict-mcp-config` | Select MCP configuration |
| `--settings <file-or-json>` | Supply settings |
| `--agent <name>`, `--agents <json>` | Select or define an agent |
| `--worktree <name>` | Use an isolated Git worktree |

Use `--bare` for controlled scripted runs when you can supply context and authentication explicitly. It skips normal discovery and does not use Anthropic subscription credentials. For subscription-authenticated runs, keep normal mode; add `--setting-sources user` when repository settings and `.mcp.json` should not load. To disable all hooks for that run, pass `--settings '{"disableAllHooks":true}'`. Supply required allow rules on the CLI rather than relying on an untrusted project's rules; see [workspace trust](https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder).

## Sessions

Keep `-p` and the chosen permission/tool options on every resumed invocation. Prefer an explicit session ID over `--continue` when other runs share the directory.

- `--resume <id>`: resume a known session
- `--continue`: continue the latest session
- `--fork-session` with resume or continue: retain history under a new ID
- `--no-session-persistence`: one-off run without a saved session

For maintenance, follow the [update checklist](../UPDATE.md).
