---
name: headless-pi
description: Use when the user explicitly says "headless-pi" or needs to run Pi CLI commands in non-interactive print/json mode for scripting, automation, model smoke tests, or quick answers without the TUI.
---

# Headless Pi

Run Pi CLI in non-interactive headless mode using `pi -p` / `pi --print`.

## Official Documentation Sources

Use these sources when refreshing flags, modes, providers, and examples:

| Source | Use For |
|---|---|
| `https://pi.dev` | Public Pi documentation entry point. |
| `https://www.npmjs.com/package/@earendil-works/pi-coding-agent` | Current published package/version. |
| `https://github.com/earendil-works/pi` (`packages/coding-agent`) | Official source repository from package metadata. |
| Installed package `README.md` | Canonical local CLI reference for the installed version. |
| Installed package `docs/json.md` | JSON event stream reference. |
| Installed package `docs/rpc.md` | RPC integration reference. |
| `pi --help` / `pi --list-models [search]` | Final local truth for currently installed flags and available models. |

For pnpm-installed Pi, resolve the installed package docs with:

```bash
PI_CLI_JS="$(sed -n 's/^# cmd-shim-target=//p' "$(command -v pi)")"
PI_PKG_DIR="$(dirname "$(dirname "$PI_CLI_JS")")"
less "$PI_PKG_DIR/README.md"
ls "$PI_PKG_DIR/docs"
```

If that shim lookup fails, locate the package with your package manager, then read `README.md` and `docs/` from the installed `@earendil-works/pi-coding-agent` package.

## Quick Start

```bash
pi -p "Your prompt here"
pi -p --model opencode-go/kimi-k2.6 "Your prompt"
pi --print --model openrouter/z-ai/glm-5.2 "Your prompt"
```

## Model Selection

Pi model IDs use `provider/model` format. Check availability before scripting a model sweep:

```bash
pi --list-models "opencode-go/kimi-k2.6"
pi --list-models "openrouter/x-ai/grok-build-0.1"
```

Known working smoke-test examples:

```bash
pi -p --model openrouter/x-ai/grok-build-0.1 "ping"
pi -p --model openai-codex/gpt-5.5 "ping"
pi -p --model opencode-go/kimi-k2.6 "ping"
pi -p --model openrouter/z-ai/glm-5.2 "ping"
pi -p --model opencode-go/minimax-m3 "ping"
```

## Machine-Friendly Output

For a single prompt, use print mode:

```bash
pi -p --model opencode-go/kimi-k2.6 "Summarize README.md"
cat README.md | pi -p --model opencode-go/kimi-k2.6 "Summarize this text"
```

For event streams, use JSON mode:

```bash
pi --mode json --model opencode-go/kimi-k2.6 "Summarize README.md"
```

## Output Cleanup

`pi -p` can append terminal control sequences after the textual answer in some shells/harnesses. When summarizing or testing output, strip control codes before taking the last line:

```bash
pi -p --model opencode-go/kimi-k2.6 "ping" 2>&1 \
  | perl -pe 's/\e\[[0-?]*[ -\/]*[@-~]//g; s/\e[()][A-Za-z0-9]//g; s/\e[=>]//g; s/\e//g; s/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]//g'
```

For batch smoke tests, write each model output to a temp file, strip control codes, remove blank lines, then report the last remaining line.

## Flags Reference

| Flag | Short | Description |
|------|-------|-------------|
| `--print` | `-p` | Print response and exit; also reads piped stdin. |
| `--mode json` | | Output JSON event lines instead of the TUI. |
| `--mode rpc` | | Start RPC mode for process integration. |
| `--provider <name>` | | Provider override, e.g. `openrouter`, `opencode-go`, `openai-codex`. |
| `--model <pattern>` | | Model pattern or full `provider/model` ID; optional `:<thinking>` suffix is supported. |
| `--models <patterns>` | | Comma-separated patterns for interactive model cycling. |
| `--list-models [search]` | | List available models, optionally filtered. |
| `--thinking <level>` | | Thinking level: `off`, `minimal`, `low`, `medium`, `high`, `xhigh`. |
| `--api-key <key>` | | API key override for the selected provider. |
| `--prompt-template <path>` | | Load prompt template; repeatable. |

## Delegation Recipe

Use Pi headless mode without PTY for simple print-mode delegation:

```bash
pi -p --model opencode-go/kimi-k2.6 "Review src/auth.ts and report issues only"
```

Use an explicit workdir in the calling harness when the prompt depends on repository files. Pin the model when reproducibility matters.

## Gotchas

- Do not call plain `pi "prompt"` for automation; it starts interactive mode.
- Prefer `pi -p` for short one-shot work and `pi --mode json` for event-stream consumers.
- `pi -p` may emit terminal teardown/control codes after the answer; strip them before parsing.
- Validate model IDs with `pi --list-models <id>` before adding them to scripts.
- If a model supports thinking, pin `--thinking` or a `:<thinking>` suffix when reasoning budget matters.

## Update This Skill

Triggered when the user wants to refresh the skill against the latest Pi CLI documentation.

**Trigger phrases:**
- "update the headless-pi skill"
- "about skill headless-pi, UPDATE the skill"
- "skill headless-pi, check if we need to update"
- "refresh headless-pi skill"
- "sync headless-pi with latest docs"

Check the Pi README and related docs before updating this file.
