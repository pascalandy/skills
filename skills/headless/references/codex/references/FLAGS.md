# Codex exec flag lookup

This table reflects `codex exec --help` in installed Codex CLI 0.159.0. Run the installed command's help before relying on a flag; the [official command reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) tracks current behavior.

| Flag | Use |
|---|---|
| `PROMPT` or `-` | Pass inline instructions or read the whole prompt from stdin; with an inline prompt, piped stdin is appended as a `<stdin>` block, so close it with `< /dev/null` when unused |
| `-C`, `--cd` | Set the target repository |
| `-s`, `--sandbox` | Set `read-only`, `workspace-write`, or `danger-full-access` |
| `-c`, `--config` | Override a config key, including `approval_policy`, `model_reasoning_effort`, `web_search`, `tools.view_image`, and `sandbox_mode` for subcommands that lack `-s` |
| `-m`, `--model` | Select a model available to the account |
| `-p`, `--profile` | Load a named config profile |
| `--worktree` | Start in a new managed Git worktree |
| `--add-dir` | Grant write access to another directory |
| `-i`, `--image` | Attach image files to the initial prompt |
| `--json` | Emit JSONL execution events on stdout |
| `-o`, `--output-last-message` | Write the final agent message to a file |
| `--output-schema` | Validate the final response against a JSON Schema file |
| `--color` | Choose `always`, `never`, or `auto` color output |
| `--ephemeral` | Do not persist the session for later resume |
| `--thread-source` | Set the new thread's source classification |
| `--skip-git-repo-check` | Allow a run outside Git for an intentionally trusted directory |
| `--enable`, `--disable` | Override a feature flag for the run |
| `--strict-config` | Fail on config keys this CLI version does not recognize |
| `--ignore-user-config` | Skip the user's `config.toml`; authentication still uses `CODEX_HOME` |
| `--ignore-rules` | Skip user and project execpolicy `.rules` files |
| `--oss`, `--local-provider` | Use a local model provider such as Ollama or LM Studio |
| `--approve-for-me` | Route approval requests through automatic review; the run uses the `workspace-write` sandbox |
| `--dangerously-bypass-approvals-and-sandbox` | Remove both controls; use only with authorization in an isolated runner |
| `--dangerously-bypass-hook-trust` | Run untrusted hooks; use only in automation that vets the hooks |
| `-h`, `--help`; `-V`, `--version` | Show command help or the CLI version |

For unattended runs, `-c 'approval_policy="never"'` prevents approval requests; actions outside the sandbox fail. `approval_policy="on-request"` can ask for approval and belongs in a supervised run. Use explicit sandbox flags as described in [Prepare the run](../MetaSkill.md#prepare-the-run).

For the default and opt-in web search and image settings, follow [Choose optional tools](../MetaSkill.md#choose-optional-tools). Add `--strict-config` to reject unrecognized configuration keys.

## Help and model discovery

```bash
codex --version
codex --help
codex exec --help
codex review --help
codex exec review --help
codex exec resume --help
codex exec fork --help
codex login status
codex debug models --help
codex debug models | jq -r '.models[] | [.slug, ([.supported_reasoning_levels[].effort] | join(","))] | @tsv'
```

`codex debug models` is experimental. Its output shows the catalog visible to this CLI, while model access still depends on the account and runner. Use each subcommand's help for its supported options. Installed 0.159.0 supports `exec fork`; the official command page may lag that installation.
