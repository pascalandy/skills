# Grok headless flag lookup

This table reflects `grok --help` in installed Grok Build 1.0.46. Run the installed command's help before relying on a flag; the [official CLI reference](https://docs.x.ai/build/cli/reference) tracks current behavior.

| Flag | Use |
|---|---|
| `-p`, `--single PROMPT` | Run one prompt, print the reply, and exit; a bare `PROMPT` opens the interactive UI instead |
| `--prompt-file PATH` | Read the one-shot prompt from a file; headless mode never reads stdin |
| `--prompt-json JSON` | Pass the one-shot prompt as JSON content blocks |
| `--cwd PATH` | Set the working directory |
| `-m`, `--model MODEL` | Select a model the account lists in `grok models` |
| `--reasoning-effort`, `--effort` | Select a level the model accepts |
| `--output-format` | `plain`, `json`, `streaming-json`, or `streaming-messages-json` |
| `--include-partial-messages` | Add text and thinking deltas to `streaming-messages-json` |
| `--json-schema SCHEMA` | Constrain the answer to a JSON Schema; implies `json` |
| `--always-approve` | Run every tool call without approval; deny rules, hooks, and admin locks still apply |
| `--permission-mode MODE` | `default`, `acceptEdits`, `auto`, `dontAsk`, `bypassPermissions`, or `plan` |
| `--allow RULE`, `--deny RULE` | Add a permission rule such as `Bash(git *)`; repeatable, and deny wins |
| `--tools IDS` | Keep only these built-in tools, such as `read_file,grep,list_dir` |
| `--disallowed-tools IDS` | Remove built-in tools; `Agent` blocks subagents |
| `--sandbox PROFILE` | Restrict filesystem and network access; also `GROK_SANDBOX` |
| `--disable-web-search` | Remove web search and fetch |
| `--no-subagents` | Disable subagent spawning |
| `--max-turns N` | Stop after N agent turns |
| `--rules TEXT` | Append rules to the system prompt |
| `--system-prompt-override TEXT` | Replace the system prompt |
| `--agent NAME`, `--agents JSON` | Select an agent, or define subagents inline |
| `--verbatim` | Send the prompt without Grok's wrapper |
| `-s`, `--session-id UUID` | Name a new session; it must not exist yet |
| `-r`, `--resume [ID]` | Resume a session; without an ID, the latest one |
| `-c`, `--continue` | Continue the latest session in `--cwd` |
| `--fork-session` | Resume into a new session ID |
| `-w`, `--worktree [NAME]` | Start in a new Git worktree; `--worktree-ref` sets its base |
| `--debug`, `--debug-file FILE` | Log debug output |
| `-h`, `--help`; `-v`, `--version` | Show help or the CLI version |

Help omits these flags, and the parser accepts them: `--no-leader` starts a new agent even when the config enables the shared leader, `--no-auto-update` skips the update check, and `--trust` records a folder trust grant in `~/.grok/trusted_folders.toml`.

For `--review-only` and `--review-fix`, `scripts/headless.py` already passes `--cwd`, `--prompt-file`, `-m`, `--reasoning-effort`, `--always-approve`, `--no-leader`, `--no-auto-update`, `--output-format streaming-messages-json`, and `--session-id` or `--resume`, plus `--disallowed-tools` under `--review-only`. For `--code-review`, it passes `-p "/review …"` and `--rules` in place of the prompt file, plus `--sandbox read-only`. Pass any other flag after `--`.

## Help and model discovery

```bash
grok --version
grok --help
grok models
grok inspect --json
grok leader list --json
grok sessions --help
```

`grok models` names the sign-in and lists the account's models; it exits 0 even when signed out, so read its first line. `grok inspect --json` shows the instructions, skills, hooks, and MCP servers Grok loads in the current folder, and whether it trusts it. `grok leader list --json` prints `[]` when no shared leader runs.
