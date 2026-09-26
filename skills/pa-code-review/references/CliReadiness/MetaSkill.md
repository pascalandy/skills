---
name: CliReadiness
description: Review command-line behavior, flags, help text, exit codes, stdout/stderr, safety prompts, and agent-friendly output.
---

# CliReadiness

Use this conditional lens when the diff changes command-line tools, scripts, shell functions, task runners, or agent-facing commands.

## Investigator Evidence Focus

1. Identify changed commands, flags, positional args, environment variables, and outputs.
2. Inspect help text, examples, error messages, and exit codes.
3. Check stdout/stderr separation and whether output is readable by humans and agents.
4. Look for unsafe defaults, missing dry-run/confirmation behavior, and unclear destructive actions.
5. Check idempotency and behavior in empty, missing-file, permission-denied, and invalid-argument cases.
6. Note relevant command checks without running them unless parent explicitly allowed it.

## Subject Adaptation

- For shell scripts, inspect quoting, `set -euo pipefail` suitability, trap/cleanup, and dependency checks.
- For task runners, inspect discoverability, names, docs, and composability.
- For AI-agent tools, prefer explicit paths, deterministic output, concise errors, and non-interactive safe modes.

## Parent Synthesis Hints

CLI issues are `P1` when users or agents cannot safely run the command. Use `P2` for unclear behavior or missing edge-case handling; `P3` for help-text polish.
