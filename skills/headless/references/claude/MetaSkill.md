---
name: headless-claude
description: |
  Use only when the user explicitly says `headless-claude` to use claude -p (print mode) commands.
source: https://code.claude.com/docs/en/cli-reference
---

# Headless Claude

## Scope

Run Claude Code CLI in non-interactive print mode (`-p`) for scripting, automation, CI/CD, or quick answers without the TUI.
If behavior differs across versions, trust the installed CLI help output (`claude --help`) over external documentation.

**Important:** Print mode (`-p`) with default permissions **will hang** waiting for approval prompts. For truly unattended execution, always pair `-p` with a permission strategy (see Permissions section).

## Permissions and safety

In headless mode, permission handling determines whether the run completes or hangs. Resolve this first.

| Goal | Recommended shape | Why |
| --- | --- | --- |
| Analysis only, no edits | `claude -p --permission-mode plan "query"` | Safe default for audits, summaries, reviews; never hangs |
| Auto-approve edits, prompt on commands | `claude -p --permission-mode acceptEdits "query"` | Edits proceed; Bash commands still prompt (may hang) |
| Skip prompts, keep sandbox | `claude -p --permission-mode dontAsk "query"` | No prompts but tools remain sandboxed |
| Fully automatic | `claude -p --permission-mode auto "query"` | Claude decides what to approve |
| Fully unattended with all tools | `claude -p --dangerously-skip-permissions "query"` | Skips all prompts; highest risk |
| Enable bypass as an option (not default) | `claude -p --allow-dangerously-skip-permissions "query"` | Makes bypass available without enabling it by default; for sandboxes |
| Fine-grained tool allowlist | `claude -p --allowedTools "Bash(git:*)" "Read" "query"` | Specific commands auto-approved, rest prompt |
| Restrict available tools | `claude -p --tools "Bash,Read" "query"` | Only listed tools exist in context |
| Block specific tools | `claude -p --disallowedTools "Edit" "query"` | Named tools removed from context entirely |
| Disable all skills | `claude -p --disable-slash-commands "query"` | Skip skill resolution for faster startup |

Permission mode choices: `default`, `plan`, `acceptEdits`, `dontAsk`, `auto`, `bypassPermissions`.

Important:

- **Default print mode hangs** on any permission prompt. Always specify a permission strategy.
- `--permission-mode plan` is the safest unattended default (read-only analysis, no edits).
- `--dangerously-skip-permissions` is equivalent to `--permission-mode bypassPermissions`.
- Ask before escalating to `--dangerously-skip-permissions`.

## Essential command patterns

### One-shot query (safe unattended)

```bash
claude -p --permission-mode plan "Explain this function"
```

### Pipe content

```bash
cat logs.txt | claude -p --permission-mode plan "Summarize these errors"
```

### Continue most recent conversation

```bash
claude -c -p "Check for type errors"
```

### Resume a named session

```bash
claude -r "auth-refactor" "Finish this PR"
```

### Resume from a PR

```bash
claude --from-pr 42 -p "Continue the review"
claude --from-pr https://github.com/org/repo/pull/42 -p "Check status"
```

### Models

```bash
claude --model opus -p "Review this code"         # Alias: latest Opus (currently 4.7)
claude --model sonnet -p "Quick summary"          # Alias: latest Sonnet (currently 4.6)
claude --model claude-opus-4-7 -p "Deep analysis" # Pin an exact version
claude --model claude-sonnet-4-6 -p "Detailed analysis"
```

Use `--fallback-model` to auto-fallback when the primary model is overloaded (print mode only):

```bash
claude -p --fallback-model sonnet "Review this code"
```

### Beta headers

Include beta headers in API requests (API key users only):

```bash
claude -p --betas beta1 beta2 "query"
```

### Verbose mode

```bash
claude -p --verbose "query"
```

### Effort level

```bash
claude --effort low -p "Quick check"
claude --effort medium -p "Standard review"
claude --effort high -p "Deep code review"
claude --effort xhigh -p "Extended reasoning"
claude --effort max -p "Exhaustive analysis"
```

Options: `low`, `medium`, `high`, `xhigh`, `max`. Available levels depend on the model (e.g., `max` is currently the top tier on Opus 4.7). Session-scoped; does not persist to settings.

### Chrome integration

Enable or disable Claude in Chrome integration:

```bash
claude -p --chrome "query"       # Enable Chrome integration
claude -p --no-chrome "query"    # Disable Chrome integration
```

### IDE integration

Automatically connect to IDE on startup if exactly one valid IDE is available:

```bash
claude -p --ide "Review this code"
```

### Agents

Use `--agent` to select a configured subagent, or `--agents` to define one inline:

```bash
claude --agent my-custom-agent -p "Review this PR"
claude --agents '{"reviewer":{"description":"Reviews code","prompt":"You are a code reviewer"}}' -p "Check this diff"
```

## Output handling

### Text output (default)

```bash
claude -p "query"
```

### JSON output

```bash
claude -p --output-format json "query"
```

### Streaming JSON

```bash
claude -p --output-format stream-json "query"
```

Additional stream-json flags:

```bash
# Include partial message events
claude -p --output-format stream-json --include-partial-messages "query"

# Bidirectional: read stream-json input, write stream-json output
claude -p --input-format stream-json --output-format stream-json "query"

# Echo user messages back on stdout for acknowledgment
claude -p --input-format stream-json --output-format stream-json --replay-user-messages "query"
```

### Structured output with JSON Schema

```bash
claude -p --json-schema '{"type":"object","properties":{"summary":{"type":"string"}}}' "Summarize this file"
```

### Budget limits

```bash
claude -p --max-budget-usd 5.00 "Expensive task"
```

### Turn limits

```bash
claude -p --max-turns 3 "Limited interaction"
```

## Fast startup

Use `--bare` to skip hooks, LSP, plugin sync, attribution, auto-memory, background prefetches, keychain reads, and CLAUDE.md auto-discovery. Claude retains Bash, file read, and file edit tools. Sets `CLAUDE_CODE_SIMPLE=1`. Skills still resolve via `/skill-name`. Anthropic auth uses strictly `ANTHROPIC_API_KEY` or `apiKeyHelper` via `--settings` (OAuth and keychain are never read).

When using `--bare`, provide context explicitly:

```bash
claude --bare -p "Quick question about Python syntax"
claude --bare --system-prompt "You are a Python expert" --add-dir ../lib -p "Review"
```

Available context flags with `--bare`: `--system-prompt`, `--append-system-prompt`, `--add-dir`, `--mcp-config`, `--settings`, `--agents`, `--plugin-dir`, `--verbose`.

## System prompt customization

Claude Code provides four flags for customizing the system prompt. All four work in both interactive and non-interactive modes.

| Flag | Behavior | Example |
| --- | --- | --- |
| `--system-prompt` | Replaces the entire default prompt | `claude --system-prompt "You are a Python expert"` |
| `--system-prompt-file` | Replaces with file contents | `claude --system-prompt-file ./prompts/review.txt` |
| `--append-system-prompt` | Appends to the default prompt | `claude --append-system-prompt "Always use TypeScript"` |
| `--append-system-prompt-file` | Appends file contents to the default prompt | `claude --append-system-prompt-file ./style-rules.txt` |

`--system-prompt` and `--system-prompt-file` are mutually exclusive. The append flags can be combined with either replacement flag. For most use cases, use an append flag. Appending preserves Claude Code's built-in capabilities while adding your requirements. Use a replacement flag only when you need complete control over the system prompt.

### Cache-friendly system prompt for scripted workloads

```bash
claude -p --exclude-dynamic-system-prompt-sections "query"
```

Moves per-machine sections (working directory, environment info, memory paths, git status) from the system prompt into the first user message. This improves prompt-cache reuse across different users/machines running the same task. Only applies with the default system prompt; ignored when `--system-prompt` or `--system-prompt-file` is set.

## Session management

```bash
# Named session (display name)
claude -n "review-session" -p "Start reviewing this PR"

# Explicit session UUID
claude --session-id "550e8400-e29b-41d4-a716-446655440000" -p "query"

# Continue most recent session in current directory
claude -c -p "Now check the tests"

# Resume by ID or name
claude -r "auth-refactor" "Continue where we left off"

# Resume from a PR
claude --from-pr 42 -p "Continue"

# Fork a session (new ID, keeps history)
claude --resume abc123 --fork-session "Try a different approach"

# Disable session persistence (one-off, no disk trace)
claude -p --no-session-persistence "One-off question"
```

## MCP servers

Load MCP servers for headless runs:

```bash
# From config file
claude --mcp-config ./mcp.json -p "query"

# Only use servers from this config (ignore all others)
claude --strict-mcp-config --mcp-config ./mcp.json -p "query"
```

## Additional directories and worktrees

```bash
# Grant access to additional directories
claude --add-dir ../apps ../lib -p "Review all modules"

# Run in an isolated git worktree
claude -w feature-auth -p "Implement auth module"

# Worktree with tmux session
claude -w feature-auth --tmux -p "Implement auth module"
```

## Settings override

```bash
# Load settings from file or JSON string
claude --settings ./settings.json -p "query"

# Control which setting sources are loaded
claude --setting-sources user,project -p "query"
```

## Debugging

```bash
claude --verbose -p "query"
claude --debug "api,mcp" -p "query"
claude --debug-file /tmp/claude-debug.log -p "query"
```

Note: `--mcp-debug` is deprecated; use `--debug mcp` instead.

## Subcommands

```bash
claude agents                        # List configured subagents (grouped by source)
claude auth login                    # Sign in (supports --email, --sso, --console)
claude auth logout                   # Log out
claude auth status                   # Auth status as JSON (exit 0 if logged in, 1 if not)
claude auth status --text            # Human-readable auth status
claude auto-mode defaults            # Print built-in auto-mode classifier rules as JSON
claude auto-mode config              # Effective auto-mode config with settings applied
claude mcp                           # Configure MCP servers
claude plugin                        # Manage plugins (alias: claude plugins)
claude remote-control                # Start a Remote Control server (no local TUI)
claude setup-token                   # Generate a long-lived OAuth token for CI/scripts
claude update                        # Check for and install updates
```

## Failure handling

- On non-zero exit, report the exact failure and ask before retrying with broader permissions.
- If a run hangs waiting for permission prompts, rerun with `--permission-mode plan` (read-only) or `--dangerously-skip-permissions` (full access).
- Prefer the narrowest permission escalation that fits the task.
- Ask before escalating permission levels.

## Verification shortcuts

```bash
claude --help
claude --version
claude auth status --text
```

## Remote Control and web sessions

Start a Remote Control server to control Claude Code from Claude.ai or the Claude app:

```bash
# Start remote control server (runs in server mode, no local interactive session)
claude remote-control --name "My Project"

# Start interactive session with Remote Control enabled
claude --remote-control "My Project"
claude --rc "My Project"  # Short form

# Set prefix for auto-generated session names
claude remote-control --remote-control-session-name-prefix dev-box

# Create a new web session on claude.ai
claude --remote "Fix the login bug"

# Resume a web session in your local terminal
claude --teleport
```

## Hooks and initialization

```bash
# Run initialization hooks and start interactive mode
claude --init

# Run initialization hooks and exit (no interactive session)
claude --init-only

# Run maintenance hooks and start interactive mode
claude --maintenance

# Include all hook lifecycle events in output stream (requires --output-format stream-json)
claude -p --output-format stream-json --include-hook-events "query"
```

## Additional flags

### Plugin directory

```bash
claude --plugin-dir ./my-plugins -p "query"
```

### Auto mode

Auto mode is now part of the `Shift+Tab` cycle by default. `--enable-auto-mode` was removed in v2.1.111; start directly in auto mode with:

```bash
claude --permission-mode auto -p "query"
```

### Channels (Research preview)

```bash
# Listen for channel notifications from MCP servers
claude --channels plugin:my-notifier@my-marketplace -p "query"

# Enable development channels not on the approved allowlist
claude --dangerously-load-development-channels server:webhook -p "query"
```

### Teammate display mode

```bash
claude --teammate-mode in-process -p "query"  # Options: auto, in-process, tmux
```

### Permission prompt tool

```bash
claude -p --permission-prompt-tool mcp_auth_tool "query"
```

## Update This Skill

**Trigger phrases:**
- "update the headless-claude skill"
- "about skill headless-claude, UPDATE the skill"
- "skill headless-claude, check if we need to update"
- "refresh headless-claude skill"
- "sync headless-claude with latest docs"

Load `references/UPDATE.md` and follow the `npx nia-docs` workflow to check the official CLI documentation.
