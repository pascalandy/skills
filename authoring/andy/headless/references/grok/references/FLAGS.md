# Grok headless flag lookup

This table reflects `grok --help` in installed Grok Build 1.0.46. Before you rely on a flag, run the installed command's help. The [official CLI reference](https://docs.x.ai/build/cli/reference) tracks current behavior.

| Flag | Use |
|---|---|
| `-p`, `--single PROMPT` | Run one prompt, print the reply, and exit. A bare `PROMPT` opens the interactive UI instead |
| `--prompt-file PATH` | Read the one-shot prompt from a file. Headless mode never reads stdin |
| `--prompt-json JSON` | Pass the one-shot prompt as JSON content blocks |
| `--cwd PATH` | Set the working directory |
| `-m`, `--model MODEL` | Select a model the account lists in `grok models` |
| `--reasoning-effort`, `--effort` | Select a level the model accepts |
| `--output-format` | `plain`, `json`, `streaming-json`, or `streaming-messages-json` |
| `--include-partial-messages` | Add text and thinking deltas to `streaming-messages-json` |
| `--json-schema SCHEMA` | Constrain the answer to a JSON Schema. The flag implies `json` |
| `--always-approve` | Run every tool call without approval. Deny rules, hooks, and admin locks still apply |
| `--permission-mode MODE` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, or `plan` |
| `--allow RULE`, `--deny RULE` | Add a permission rule such as `Bash(git *)`. Repeat the flag for more rules. Deny wins |
| `--tools IDS` | Keep only these built-in tools, such as `read_file,grep,list_dir` |
| `--disallowed-tools IDS` | Remove built-in tools. `Agent` blocks subagents |
| `--sandbox PROFILE` | Restrict filesystem and network access. `GROK_SANDBOX` also selects a profile |
| `--disable-web-search` | Remove web search and fetch |
| `--no-subagents` | Disable subagent spawning |
| `--max-turns N` | Stop after N agent turns |
| `--rules TEXT` | Append rules to the system prompt |
| `--system-prompt-override TEXT` | Replace the system prompt |
| `--agent NAME`, `--agents JSON` | Select an agent, or define subagents inline |
| `--verbatim` | Send the prompt without Grok's wrapper |
| `-s`, `--session-id UUID` | Name a new session. It must not exist yet |
| `-r`, `--resume [ID]` | Resume a session. Without an ID, use the latest one |
| `-c`, `--continue` | Continue the latest session in `--cwd` |
| `--fork-session` | Resume into a new session ID |
| `-w`, `--worktree [NAME]` | Start in a new Git worktree. `--worktree-ref` sets its base |
| `--debug`, `--debug-file FILE` | Log debug output |
| `-h`, `--help` | Show command help |
| `-v`, `--version` | Show the CLI version |

Help omits three flags that the parser accepts:

- `--no-leader` starts a new agent even when the config enables the shared leader
- `--no-auto-update` skips the update check
- `--trust` records a folder trust grant in `~/.grok/trusted_folders.toml`

For `--review-only` and `--review-fix`, `scripts/headless.py` already passes these flags:

- `--cwd`, `--prompt-file`, `-m`, `--reasoning-effort`, and `--always-approve`
- `--no-leader`, `--no-auto-update`, and `--output-format streaming-messages-json`
- `--session-id` or `--resume`
- `--disallowed-tools` under `--review-only`

For `--code-review`, it passes `-p "/review …"`, `--rules`, and `--sandbox read-only` instead of the prompt file. Pass any other flag after `--`.

## Help and model discovery

```bash
grok --version
grok --help
grok models
grok inspect --json
grok leader list --json
grok sessions --help
```

`grok models` names the sign-in and lists the account's models. It exits 0 even when signed out, so read its first line. `grok inspect --json` shows the instructions, skills, hooks, and MCP servers Grok loads in the current folder. It also shows whether Grok trusts that folder. `grok leader list --json` prints `[]` when no shared leader runs.
