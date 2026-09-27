# Run Claude Code headlessly

Use `claude -p` from the target repository with ordinary pipes. Check `claude --help`, `claude --version`, and `claude auth status --text` before relying on installed behavior. The [programmatic guide](https://code.claude.com/docs/en/headless) and [CLI reference](https://code.claude.com/docs/en/cli-reference) own the full flag list.

## Permissions

Choose an explicit permission strategy. `dontAsk` denies calls that would prompt; it does not create a filesystem sandbox. For a file review without shell execution, restrict available tools:

```bash
claude -p --permission-mode dontAsk --tools "Read,Grep,Glob" \
  "Review src/auth.ts for correctness. Report findings with file and line." < /dev/null
```

This review cannot run tests or obtain a Git diff through Bash. Supply the diff through stdin, or authorize narrowly scoped shell commands when needed.

| Option | Use |
| --- | --- |
| `--permission-mode plan` | Explore without source edits; do not assume it guarantees unattended completion |
| `--permission-mode acceptEdits` | Approve edits; other operations may still need permission |
| `--permission-mode dontAsk` | Deny operations that would prompt |
| `--allowedTools` | Pre-approve specified tools or command rules |
| `--tools` | Restrict which built-in tools are available |
| `--disallowedTools` | Deny named tools |
| `--permission-mode auto` | Automatic approval decisions, subject to availability and policy |
| `--permission-mode bypassPermissions` | Bypass permission checks only with authorization in an isolated runner |

Use [permission documentation](https://code.claude.com/docs/en/permissions) for rule syntax. Diagnose denied tools before retrying; do not default to bypass.

## Input and output

```bash
claude -p --permission-mode dontAsk --tools "Read,Grep,Glob" \
  --output-format json "Review this diff and inspect related files" < diff.patch
```

Use `text` for a plain answer, `json` for a result with session metadata, or `stream-json` for events. Add `--verbose` with streaming output:

```bash
claude -p --permission-mode dontAsk --tools "Read,Grep,Glob" \
  --output-format stream-json --verbose "Summarize README.md" < /dev/null
```

Use `--output-format json --json-schema '<schema>'` for a structured result. Capture stdout and stderr separately, preserve the exit status, and inspect the final result for errors and denied tools before declaring success.

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

Use `--bare` only when deliberately supplying context and authentication yourself: it skips normal discovery and does not use Anthropic subscription credentials. Consult installed help for exact behavior.

## Sessions

Keep `-p` and the chosen permission/tool options on every resumed invocation. Prefer an explicit session ID over `--continue` when other runs share the directory.

- `--resume <id>`: resume a known session
- `--continue`: continue the latest session
- `--fork-session` with resume or continue: retain history under a new ID
- `--no-session-persistence`: one-off run without a saved session

For maintenance, follow the [update checklist](../UPDATE.md).
