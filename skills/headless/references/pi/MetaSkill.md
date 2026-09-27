# Run Pi headlessly

Use `pi -p` from the target repository with ordinary pipes. Check `pi --help` and `pi --list-models` before choosing flags or models. The installed package's `README.md`, `docs/json.md`, and `docs/rpc.md` document its version; [Pi's official repository](https://github.com/earendil-works/pi/tree/main/packages/coding-agent) provides upstream guidance.

## Review or execute

Print mode alone does not restrict tools. For file inspection without shell execution or edits:

```bash
pi -p --no-extensions --tools read,grep,find,ls \
  "Review src/auth.ts for correctness. Report findings with file and line." < /dev/null
```

This tool set cannot run tests or obtain a diff through Bash. Supply a diff on stdin or authorize the tools needed for execution. Keep the working directory explicit in the calling process.

For an event stream, add `--mode json`:

```bash
pi -p --mode json --no-extensions --tools read,grep,find,ls \
  "Review this diff and inspect related files" < diff.patch
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
| `--mode rpc` | Start a persistent integration protocol; consult `docs/rpc.md` |

Pin the model and reasoning only when requested or required by the runner's policy. Prefer explicit session IDs over latest-session selection when runs overlap.

## Verify output

Capture stdout, stderr, and exit status separately. Prefer JSON events for automation; inspect the actual final answer and tool failures before reporting success. Some runners append terminal control sequences to text output, so do not use the last raw line as the result or merge stderr into text you intend to parse.

For maintenance, follow the [update checklist](../UPDATE.md).
