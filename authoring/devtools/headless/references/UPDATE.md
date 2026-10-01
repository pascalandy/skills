# Maintain the headless skill

Update documentation without installing or upgrading CLIs or invoking billable model runs by default.

1. Read the affected CLI's installed help and official source below. Record version differences instead of claiming universal behavior
2. Keep Codex and Claude flags in `scripts/headless.py`, other CLIs' flags and examples in their reference, and definitions in the glossary. Leave delegation policy to the calling workflow
3. Remove superseded recipes and stale model or local-agent lists. Discover availability at runtime instead of maintaining a second catalog
4. Check routing from SKILL.md, relative links, stdin handling, permissions, output separation, and exit status. Use parser or stub checks for shell examples; run live model calls only when behavioral evidence needs them and the task authorizes them. After a Codex or Claude Code update, run `just check --only headless`, then one live `--effort low` review per CLI, and confirm its `model` line
5. Run repository validators and regenerate distributed skills according to the repository's AGENTS.md. Commit source and generated output together

| Reference | Local checks | Official source |
| --- | --- | --- |
| Claude Code | `claude --version`, `claude --help` | [Programmatic guide](https://code.claude.com/docs/en/headless), [CLI](https://code.claude.com/docs/en/cli-reference), [permissions](https://code.claude.com/docs/en/permissions) |
| Codex | `codex --version`, `codex exec --help`, `codex exec resume --help`, `codex exec fork --help` | [Non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode), [commands](https://learn.chatgpt.com/docs/developer-commands#codex-exec), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [models](https://learn.chatgpt.com/docs/models) |
| OpenCode | `opencode --version`, `opencode run --help`, `opencode serve --help`. Avoid v2 `opencode debug agents`: it leaves a background service running | [V2 run](https://opencode.ai/v2/docs/cli/commands/#run), [v2 agents](https://opencode.ai/v2/docs/agents/), [v1 CLI](https://opencode.ai/docs/cli/), [v1 agents](https://opencode.ai/docs/agents/) |
| Pi | `pi --version`, `pi --help`, `pi --list-models` | [CLI integration](https://pi.dev/docs/latest/cli-integration), [CLI](https://pi.dev/docs/latest/cli), [JSON events](https://pi.dev/docs/latest/json), [RPC](https://pi.dev/docs/latest/rpc) |

For Pi, locate the installed `@earendil-works/pi-coding-agent` package through the active package manager, then read its README and JSON/RPC docs as needed. For Codex model discovery, check `codex debug models --help` before using that experimental command.
