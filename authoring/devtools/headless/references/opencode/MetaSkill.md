---
name: headless-opencode
description: Use when the user explicitly says "headless-opencode" or needs to run OpenCode CLI commands in non-interactive mode for scripting, automation, CI/CD, or quick answers without the TUI.
---

# Headless OpenCode

Run OpenCode CLI in non-interactive headless mode using `opencode run`.

## Quick Start

```bash
opencode run "Your prompt here"
opencode run --agent 1-kimi "Your prompt"
```

## Agent Selection

**Core agents (numbered for Tab cycling):**
```bash
opencode run --agent 1-kimi "Your prompt"    # Kimi 2.5 Turbo (default)
opencode run --agent 2-opus "Your prompt"    # Claude Opus 4-6
opencode run --agent 3-gpt "Your prompt"     # GPT-5.4
opencode run --agent 4-sonnet "Your prompt"  # Claude Sonnet 4-6
```

**Specialized agents:**
```bash
opencode run --agent worker "Your prompt"     # GPT-5.4 general worker
opencode run --agent worker1 "Your prompt"   # Claude Sonnet (thinking)
opencode run --agent worker2 "Your prompt"   # GLM 5.1
opencode run --agent worker3 "Your prompt"   # agt mini (GPT-5.4-mini)
opencode run --agent glm "Your prompt"       # GLM 5.1
opencode run --agent gptmini "Your prompt"   # GPT-5.4 mini
opencode run --agent gpthigh "Your prompt"   # GPT-5.4 high reasoning
opencode run --agent gptxhigh "Your prompt"  # GPT-5.4 xhigh reasoning
opencode run --agent gemini "Your prompt"    # Gemini 3.1 Pro
opencode run --agent flash "Your prompt"     # Gemini 3 Flash
```

## Session Management

**Continue last session:**
```bash
opencode run --continue "Now add error handling examples"
```

**Fork session with different agent:**
```bash
opencode run --continue --fork --agent 2-opus "Now add error handling examples"
```

**Named session:**
```bash
opencode run --title "Code Review Session" "Review this PR"
```

**Share session:**
```bash
opencode run --share "Explain this code"
```

## File Attachments & Output

**Attach files:**
```bash
opencode run --file src/main.py --file README.md "Review these files"
```

**JSON output for programmatic use:**
```bash
opencode run --format json "List all functions in this file"
```

## Server Mode (Avoid MCP Cold Boot)

Start a headless server to avoid MCP initialization delays:

```bash
# Terminal 1: Start headless server
opencode serve

# Terminal 2: Run commands against it
opencode run --attach http://localhost:4096 "Explain async/await"
```

## Flags Reference

| Flag | Short | Description |
|------|-------|-------------|
| `--agent` | | Agent to use (preferred) |
| `--model` | `-m` | Model to use (provider/model format) |
| `--variant` | | Model variant (provider-specific reasoning effort, e.g., high, max, minimal) |
| `--thinking` | | Show thinking blocks |
| `--command` | | Command to run (use message for args) |
| `--continue` | `-c` | Continue the last session |
| `--session` | `-s` | Session ID to continue |
| `--fork` | | Fork the session when continuing |
| `--file` | `-f` | File(s) to attach |
| `--format` | | Output format: `default` or `json` |
| `--title` | | Title for the session |
| `--share` | | Share the session |
| `--attach` | | Attach to running server (e.g., `http://localhost:4096`) |
| `--password` | `-p` | Basic auth password (defaults to OPENCODE_SERVER_PASSWORD) |
| `--dir` | | Directory to run in, or path on remote server if attaching |
| `--port` | | Port for local server (defaults to random if not specified) |
| `--pure` | | Run without external plugins |
| `--log-level` | | Log level: DEBUG, INFO, WARN, ERROR |
| `--print-logs` | | Print logs to stderr |

## Output Handling

- Default: formatted text to stdout
- `--format json`: raw JSON events for parsing
- Progress and diagnostics appear on stderr
- Keep stderr visible for debugging; use `--format json` for clean machine-readable output

## Gotchas

- Agents are defined in `dot_config/opencode/opencode.json.tmpl` — the numbered agents (1-kimi, 2-opus, etc.) are custom configurations
- `--continue` resumes with the same agent; use `--fork` to switch agents mid-session
- When using `--attach`, the server must already be running via `opencode serve`
- For CI/CD automation, prefer `--format json` for reliable output parsing
- Use `--variant` to specify reasoning effort (high, max, minimal) for supported models
- Use `--thinking` to display model thinking blocks in output
- Use `--pure` to run without loading external plugins
- Use `--dir` when attaching to specify the remote working directory

## Update This Skill

Triggered when the user wants to refresh the skill against the latest official documentation.

**Trigger phrases:**
- "update the headless-opencode skill"
- "about skill headless-opencode, UPDATE the skill"
- "skill headless-opencode, check if we need to update"
- "refresh headless-opencode skill"
- "sync headless-opencode with latest docs"

Load `references/UPDATE.md` and follow the `npx nia-docs` workflow to check the official CLI documentation.
