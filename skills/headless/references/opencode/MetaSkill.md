# Run OpenCode headlessly

Use `opencode run` from an explicit target directory. Check `opencode run --help` and the [official CLI reference](https://opencode.ai/docs/cli/) for installed flags. Run with ordinary pipes; do not request interactive mode for automation.

```bash
opencode run --dir /path/to/repo --format json \
  "Review src/auth.ts for correctness. Report findings only." < /dev/null
```

The prompt does not enforce read-only access. Inspect the selected agent's permissions before a review; do not add `--auto` merely to get past denied operations.

## Agent and model selection

Use `opencode agent list` and `opencode models` to discover configured agents and models. Agent names are local configuration, not portable model aliases.

| Option | Use |
| --- | --- |
| `--agent <name>` | Select a configured agent |
| `--model <provider/model>` | Select a model directly |
| `--variant <name>` | Set model-specific reasoning effort |
| `--thinking` | Include thinking output |
| `--pure` | Skip external plugins |

## Input, output, and sessions

| Option | Use |
| --- | --- |
| `--file <path>` | Attach a file; repeat for multiple files |
| `--format json` | Emit JSON events |
| `--session <id>` | Resume a specific session |
| `--continue` | Resume the latest session |
| `--fork` | Fork with `--session` or `--continue` |
| `--title <text>` | Name the session |
| `--share` | Share the session only when requested |
| `--dir <path>` | Select the local or attached server's working directory |

Prefer explicit session IDs for concurrent runs. Save stdout and stderr separately and inspect the final event and exit status; a completed process alone does not verify the requested outcome.

## Reuse a server

For repeated runs, an existing server avoids repeated MCP startup:

```bash
opencode serve
```

Then, from another process:

```bash
opencode run --attach http://localhost:4096 --dir /path/to/repo \
  --format json "Review the current changes" < /dev/null
```

Manage the server's lifetime explicitly. Check `opencode serve --help` for binding and authentication options before exposing it beyond the local machine.

For maintenance, follow the [update checklist](../UPDATE.md).
