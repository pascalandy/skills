---
name: headless-codex
description: |
  Use only when the user explicitly says `headless-codex` to use codex exec commands.
---

# Headless Codex

Run OpenAI Codex CLI in non-interactive headless mode using `codex exec`.

## Quick Start

```bash
codex exec "Your prompt here"
codex exec -m gpt-5.4 "Your prompt"
```

## Model Selection

**Override the default model:**
```bash
codex exec -m gpt-5.4 "Your prompt"
codex exec -m gpt-5-codex "Your prompt"
```

**Use local OSS model (requires Ollama):**
```bash
codex exec --oss "Your prompt"
```

## Reasoning Effort

Control the model's reasoning depth with inline config:

```bash
codex exec -c 'model_reasoning_effort="high"' "Analyze this codebase"
codex exec -c 'model_reasoning_effort="xhigh"' "Deep architectural review"
```

Reasoning effort values: `none`, `minimal`, `low`, `medium`, `high`, `xhigh`

## Session Management

**Resume the most recent session:**
```bash
codex exec resume --last "Continue where we left off"
```

**Resume a specific session:**
```bash
codex exec resume SESSION_ID "Follow-up question"
```

**Resume from any directory:**
```bash
codex exec resume --last --all "Continue from anywhere"
```

**Ephemeral run (no session persistence):**
```bash
codex exec --ephemeral "One-off task"
```

## File Attachments & Images

**Attach images:**
```bash
codex exec -i screenshot.png "Explain this UI"
codex exec -i image1.png,image2.png "Compare these images"
```

**Set working directory:**
```bash
codex exec -C /path/to/project "Analyze this repo"
```

## Output Handling

**JSON output for programmatic use:**
```bash
codex exec --json "List all functions"
```

**Save final message to file:**
```bash
codex exec -o output.txt "Generate a summary"
```

**Disable colors:**
```bash
codex exec --color never "Plain text output"
```

## Approvals & Sandboxing

Be explicit about approvals and sandboxing for unattended execution.

| Goal | Recommended Command | Why |
|------|---------------------|-----|
| Read-only analysis (safest) | `codex exec -s read-only "Review this code"` | Safe default for audits, summaries, reviews |
| Workspace edits (automated) | `codex exec -s workspace-write "Refactor this file"` | Lets Codex modify files without hanging on approval prompts |
| Low-friction local work | `codex --full-auto "Quick task"` | On main CLI: shortcut for `-a on-request -s workspace-write` |
| Externally sandboxed only | `codex exec --dangerously-bypass-approvals-and-sandbox "Risky task"` | Highest risk; only with explicit user permission |

**Important:**
- For truly unattended headless execution, use `-s workspace-write` or `-s read-only`
- `--full-auto` is on the main `codex` CLI, not `codex exec`; it maps to `--ask-for-approval on-request` plus `--sandbox workspace-write`
- Ask before using `--dangerously-bypass-approvals-and-sandbox` or `danger-full-access`

## Piping Input

**Pipe a prompt from stdin:**
```bash
cat prompt.md | codex exec -s read-only -
```

**Pipe with model and reasoning:**
```bash
cat prompt.md | codex exec -m gpt-5.4 -c 'model_reasoning_effort="xhigh"' -s read-only -
```

## Flags Reference

| Flag | Short | Description |
|------|-------|-------------|
| `--model` | `-m` | Model to use (e.g., `gpt-5.4`, `gpt-5-codex`) |
| `--ask-for-approval` | `-a` | Approval mode: `never`, `on-request`, `untrusted` (on main CLI, not exec) |
| `--sandbox` | `-s` | Sandbox policy: `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | | Shortcut for `-a on-request -s workspace-write` (on main CLI) |
| `--config` | `-c` | Inline config override (e.g., `-c 'model_reasoning_effort="high"'`) |
| `--enable` | | Enable a feature (repeatable) |
| `--disable` | | Disable a feature (repeatable) |
| `--json` | | Output newline-delimited JSON events |
| `--output-last-message` | `-o` | Write final message to file |
| `--color` | | Color mode: `always`, `never`, `auto` |
| `--image` | `-i` | Attach image(s) to the prompt |
| `--cd` | `-C` | Set working directory |
| `--add-dir` | | Additional directories that should be writable |
| `--ephemeral` | | Run without persisting session |
| `--output-schema` | | Path to a JSON Schema file for structured output |
| `--profile` | `-p` | Load configuration profile |
| `--oss` | | Use local OSS model provider (Ollama/LM Studio) |
| `--local-provider` | | Specify local provider: `lmstudio` or `ollama` |
| `--skip-git-repo-check` | | Allow running outside a Git repository |
| `--dangerously-bypass-approvals-and-sandbox` | | Bypass all approvals and sandboxing (dangerous) |

## Subcommands

| Command | Description |
|---------|-------------|
| `codex exec resume` | Resume a previous exec session by ID |
| `codex exec resume --last` | Resume the most recent session |
| `codex exec resume --all` | Include sessions from any directory |
| `codex exec review` | Run a code review against the current repository |

## Output Handling Best Practices

- Default: formatted text to stdout
- `--json`: newline-delimited JSON events for parsing
- Progress and diagnostics appear on stderr
- Keep stderr visible for debugging
- Use `--json` or `-o` for clean machine-readable output
- If the user only wants a concise summary, run Codex, then summarize the result in plain language
- When relevant, include changed files, tests run, warnings, and the session ID in your summary

## Failure Handling

- On non-zero exit, report the exact failure and ask before retrying with broader access
- If a run stalls because Codex needs approvals, rerun with explicit sandbox level (`-s read-only` or `-s workspace-write`)
- If resume warns about a model mismatch, keep the existing model unless the user wants to switch
- Ask before escalating from `read-only` to `workspace-write`
- Ask again before any `danger-full-access` or `--dangerously-bypass-approvals-and-sandbox`

## Verification Shortcuts

```bash
codex --help
codex exec --help
codex exec resume --help
codex login --help
```

## Gotchas

- `codex exec` is the headless command; plain `codex` launches the interactive TUI
- `--full-auto` is NOT the same as fully unattended; it still prompts on-request
- For CI/CD automation, always use explicit sandbox level (`-s read-only` or `-s workspace-write`)
- Approval flag `-a` is on the main `codex` CLI, not `codex exec` - use `--full-auto` on main CLI or configure sandbox in exec
- Session resume uses the original working directory unless overridden with `-C`
- When using `--oss`, ensure Ollama or LM Studio is running first
- Use `--enable` and `--disable` to toggle feature flags
- Use `--output-schema` for structured JSON output with schema validation

## Update This Skill

Triggered when the user wants to refresh the skill against the latest official documentation.

**Trigger phrases:**
- "update the headless-codex skill"
- "about skill headless-codex, UPDATE the skill"
- "skill headless-codex, check if we need to update"
- "refresh headless-codex skill"
- "sync headless-codex with latest docs"

Load `references/UPDATE.md` and follow the `npx nia-docs` workflow to check the official CLI documentation.
