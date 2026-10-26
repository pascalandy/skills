# Maintain the headless skill

Update documentation without installing or upgrading CLIs by default. Do not invoke billable model runs by default.

1. Read the affected CLI's installed help and official source below
2. Record version differences instead of claiming universal behavior
3. Keep Codex, Claude, and Grok flags in `scripts/headless.py`
4. Keep each CLI's default model and reasoning level in `config.toml`
5. Keep other CLIs' flags and examples in their references
6. Keep definitions in the glossary
7. Leave delegation policy to the calling workflow
8. Remove superseded recipes and stale model or local-agent lists
9. Discover availability at runtime instead of maintaining a second catalog
10. Check these parts of the procedure:
    - Routing from `SKILL.md`
    - Relative links
    - Standard input handling
    - Permissions
    - Output separation
    - Exit status
11. Use parser or stub checks for shell examples

COST: Run a live model call only when the task authorizes it and behavioral evidence needs it. A live call can consume plan quota or API credit.

12. After a Codex, Claude Code, or Grok update, run `just check --only headless`
13. For each updated CLI, run one live `--effort low` review
14. For each updated CLI, run one `--code-review --effort low` review
15. For the code review, use `--uncommitted` with Codex or Grok and `--base <branch>` with Claude
16. Confirm the `model` that answers each live review
17. Run the repository validators according to its `AGENTS.md`
18. Regenerate distributed skills according to its `AGENTS.md`
19. Commit source and generated output together

| Reference | Local checks | Official source |
| --- | --- | --- |
| Claude Code | `claude --version`, `claude --help` | [Programmatic guide](https://code.claude.com/docs/en/headless), [CLI](https://code.claude.com/docs/en/cli-reference), [permissions](https://code.claude.com/docs/en/permissions) |
| Codex | `codex --version`, `codex exec --help`, `codex exec review --help`, `codex exec resume --help`, `codex exec fork --help` | [Non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode), [commands](https://learn.chatgpt.com/docs/developer-commands#codex-exec), [configuration](https://learn.chatgpt.com/docs/config-file/config-reference), [models](https://learn.chatgpt.com/docs/models) |
| Grok | `grok --version`, `grok --help`, `grok models`, `grok inspect --json` | [Headless guide](https://docs.x.ai/build/cli/headless-scripting), [CLI](https://docs.x.ai/build/cli/reference), [permissions](https://docs.x.ai/build/features/permissions), [models](https://docs.x.ai/developers/models) |
| OpenCode | `opencode --version`, `opencode run --help`, `opencode serve --help`. Avoid v2 `opencode debug agents`: it leaves a background service running | [V2 run](https://opencode.ai/v2/docs/cli/commands/#run), [v2 agents](https://opencode.ai/v2/docs/agents/), [v1 CLI](https://opencode.ai/docs/cli/), [v1 agents](https://opencode.ai/docs/agents/) |
| Pi | `pi --version`, `pi --help`, `pi --list-models` | [CLI integration](https://pi.dev/docs/latest/cli-integration), [CLI](https://pi.dev/docs/latest/cli), [JSON events](https://pi.dev/docs/latest/json), [RPC](https://pi.dev/docs/latest/rpc) |

For Pi, locate the installed `@earendil-works/pi-coding-agent` package through the active package manager, then read its README and JSON/RPC docs as needed. For Codex model discovery, check `codex debug models --help` before using that experimental command. For Grok, `~/.grok/docs/user-guide/` and `~/.grok/CHANGELOG.md` match the installed CLI, and `~/.grok/bundled/skills/review/SKILL.md` defines `/review`.
