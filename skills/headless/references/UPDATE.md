# Maintain the headless skill

Update documentation without installing or upgrading CLIs or invoking billable model runs by default.

1. Read the affected CLI's installed help and official source below. Record version differences instead of claiming universal behavior
2. Keep command flags and examples in that CLI's reference. Keep process supervision in the delegation reference and definitions in the glossary
3. Remove superseded recipes and stale model or local-agent lists. Discover availability at runtime instead of maintaining a second catalog
4. Check routing from SKILL.md, relative links, stdin handling, permissions, output separation, and exit status. Use parser or stub checks for shell examples; run live model calls only when behavioral evidence needs them and the task authorizes them
5. Run repository validators and regenerate distributed skills according to the repository's AGENTS.md. Commit source and generated output together

| Reference | Local checks | Official source |
| --- | --- | --- |
| Claude Code | `claude --version`, `claude --help` | [Programmatic guide](https://code.claude.com/docs/en/headless), [CLI](https://code.claude.com/docs/en/cli-reference), [permissions](https://code.claude.com/docs/en/permissions) |
| Codex | `codex --version`, `codex exec --help`, `codex review --help`, `codex exec review --help`, `codex exec resume --help` | [Non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode), [commands](https://learn.chatgpt.com/docs/developer-commands#codex-exec), [models](https://learn.chatgpt.com/docs/models) |
| OpenCode | `opencode --version`, `opencode run --help`, `opencode serve --help`, `opencode agent list` | [CLI](https://opencode.ai/docs/cli/) |
| Pi | `pi --version`, `pi --help`, `pi --list-models` | Installed package docs, [upstream repository](https://github.com/earendil-works/pi/tree/main/packages/coding-agent) |

For Pi, locate the installed `@earendil-works/pi-coding-agent` package through the active package manager, then read its README and JSON/RPC docs as needed. For Codex model discovery, check `codex debug models --help` before using that experimental command.

For delegation changes, check that the strict execution trigger remains distinct from CLI guidance. Use the current harness's actual process tools instead of copying runner-specific pseudocommands.
