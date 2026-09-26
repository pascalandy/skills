---
name: CliImpl
description: Build CLI tools (Python, JS, Bash, Go) following modern best practices. USE WHEN build CLI, implement CLI, create CLI, CLI implementation, CLI best practices, CLI help text, CLI errors, CLI output, CLI flags, CLI args, CLI subcommands, review CLI UX, CLI code review.
---

# CliImpl -- Build CLI Tools

Implement CLI tools following modern best practices based on [clig.dev](https://clig.dev/). Human-first design while maintaining composability.

---

## Core Concept

Transform a CLI spec (or a vague request) into working code that follows established conventions. This skill covers the full implementation surface: I/O streams, help text, output formatting, error handling, argument parsing, interactivity, subcommands, robustness, future-proofing, signals, configuration, environment variables, naming, and distribution. Language-specific guidance for Python, TypeScript/Node, and Bash.

---

## Core Philosophy

1. **Human-first design** -- CLIs are for humans, not just scripts
2. **Simple parts that work together** -- Composable via pipes, stdin/stdout, exit codes
3. **Consistency** -- Follow established conventions (flags, env vars, behavior)
4. **Say just enough** -- Not too verbose, not too silent
5. **Ease of discovery** -- Help, examples, suggestions
6. **Conversation as norm** -- Trial-and-error is expected; guide the user
7. **Robustness** -- Handle errors gracefully, feel solid
8. **Empathy** -- Delight users, exceed expectations

---

## Essential Rules

### I/O Streams

| Stream    | Purpose                                | Example                    |
| --------- | -------------------------------------- | -------------------------- |
| `stdout`  | Primary output, data, machine-readable | Results, JSON, piped data  |
| `stderr`  | Messages, logs, progress, errors       | Status, warnings, spinners |
| Exit `0`  | Success                                |                            |
| Exit non-zero | Failure (map codes to failure modes) |                          |

### Help

- `-h` and `--help` show full help (exit 0, ignore other flags)
- No args + required args: concise help (description + 1-2 examples + "use --help")
- Lead with examples, not option lists
- Include support path (URL, issue tracker)
- Suggest likely fixes on typos ("Did you mean...?")
- If expecting stdin and it's a TTY, show help immediately (don't hang)

### Output

- Human-readable by default; detect TTY for formatting
- `--plain` for stable, line-based output (scripts, grep/awk)
- `--json` for structured output
- Brief success messages; verbose only when state changes
- Suggest next commands in workflows
- Color: intentional (not decorative); disable via `NO_COLOR`, `TERM=dumb`, `--no-color`
- No animations/spinners when stdout is not TTY
- No debug noise by default; use `--debug` or `DEBUG=1`

### Errors

- Rewrite for humans: what happened + how to fix
- High signal-to-noise; group similar errors
- Important info at the end (eye drawn there)
- Unexpected errors: debug path + bug report instructions

### Arguments & Flags

- Prefer flags over positional args
- Full-length flags for everything (`--help`, not just `-h`)
- One-letter flags for common options only
- Standard names: `--help`, `--version`, `--dry-run`, `--verbose`, `--json`, `--force`, `--output`, `--quiet`, `--debug`, `--no-input`
- Sensible defaults (right thing for most users)
- Prompt for missing input (TTY only); never require prompts
- Confirm dangerous actions; support `--dry-run`
- `-` for stdin/stdout when flag takes a file
- Order-independent flags/subcommands when possible
- Never accept secrets via flags (use `--password-file` or stdin)

### Interactivity

- Prompt only when stdin is TTY
- Support `--no-input` to disable all prompts
- Password prompts: don't echo
- Ctrl-C always exits quickly

### Subcommands

- Consistent flags across subcommands
- Consistent naming pattern (noun verb or verb noun)
- Avoid ambiguous names (update vs upgrade)

### Robustness

- Validate input early; fail fast with clear message
- Responsive < 100ms; show progress for long ops
- Network calls timeout (configurable)
- Recoverable on rerun; crash-only design
- Handle misuse (scripts, bad networks, concurrent instances)

### Future-Proofing

- Treat interfaces as contracts (flags, env vars, config, output)
- Additive changes preferred
- Warn before breaking changes; deprecate gracefully
- No catch-all subcommand (blocks future commands)
- No arbitrary abbreviations of subcommands

### Signals

- Ctrl-C: exit immediately, acknowledge, timeout cleanup
- Second Ctrl-C: force stop (document behavior)

### Configuration

- Precedence: flags > env > project config > user config > system config
- Follow XDG spec (`~/.config/...`)
- Never silently edit other programs' config

### Environment Variables

- Names: `UPPERCASE_WITH_UNDERSCORES` (no leading digit)
- Single-line values preferred
- Respect: `NO_COLOR`, `FORCE_COLOR`, `DEBUG`, `EDITOR`, `HTTP_PROXY`, `PAGER`, `HOME`, `TMPDIR`
- Read `.env` for project context (not as full config)
- Never read secrets from env vars (use files/stdin)

### Naming

- Simple, memorable, lowercase
- Dashes only if needed; short but not cryptic
- Easy to type

### Distribution

- Single binary when possible
- Easy uninstall (document it)

### Analytics

- No telemetry without consent (opt-in preferred)
- Transparent collection; consider alternatives

---

## References

For detailed stress-testing checklist, see `references/checklist.md`.

For high-level concepts summary, see `references/High-Level Concepts.md`.

For the full guidelines with complete examples, see `references/full-guidelines.md`.

For table of contents, see `references/index.md`.

---

## Language-Specific Notes

### Python

- Use `argparse`, `click`, or `typer`
- Return exit codes from `main()`; use `raise SystemExit(main())`
- No tracebacks for expected errors; `--debug` for unexpected
- Handle Ctrl-C cleanly (exit 130, no traceback)
- Separate TTY detection for stdout vs stderr

### TypeScript/Node

- Use `commander`, `yargs`, `oclif`, or `node:util parseArgs`
- Separate stdout/stderr; handle async failures
- `--debug` for stack traces
- Avoid premature `process.exit()`; prefer `process.exitCode`

### Bash

- Shebang matches features (`#!/usr/bin/env bash` for Bash-only)
- Robust flag parsing; handle quotes/whitespace
- `trap` for cleanup; `mktemp` for temp files
- Lint with `shellcheck`

---

## Output Format

Return working code that follows all applicable rules above. Include inline comments for non-obvious decisions. When reviewing existing CLI code, reference specific checklist items from `references/checklist.md`.
