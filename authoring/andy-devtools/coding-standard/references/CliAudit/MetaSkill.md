---
name: CliAudit
description: Audit CLI tools for agent-friendliness, composability, and retry safety. USE WHEN audit CLI, agent-friendly CLI, CLI requirements, CLI composability, CLI pipeline, CLI idempotent, CLI retry safe, CLI review agent, CLI operability, CLI non-interactive, CLI safety check.
---

# CliAudit -- Agent-Friendly CLI Requirements

Audit and apply requirements that ensure CLI tools are operable by AI agents, composable in pipelines, and safe to retry.

---

## Core Concept

Human-friendly CLI design (covered by CliSpec and CliImpl) is necessary but not sufficient. Agent-operated CLIs face additional constraints: no interactive prompts in the primary path, structured output for parsing, idempotent commands for safe retries, and actionable errors that resolve in one attempt. This skill layers agent-operability requirements on top of the human-first foundation.

---

## Input Handling

### All inputs via flags

Every value the script needs must be passable as a flag. No interactive prompts as the primary path. If a flag is provided, skip any prompt for that value. Interactive prompts are acceptable only as a fallback when stdin is a TTY and the flag was omitted.

```bash
# Required pattern -- works non-interactively
mycli deploy --env staging --tag v1.2.3

# Acceptable fallback -- only when run by a human with missing flags
mycli deploy
? Which environment? staging
```

For every interactive prompt in the script, implement a `--flag` that bypasses it. When all required flags are present, the command runs silently to completion with zero prompts.

### Prefer flags over positional args

Use named flags (`--env staging`) rather than positional arguments (`mycli deploy staging`). Positional args are ambiguous when there are multiple parameters and hard to extend without breaking existing usage.

Exception: a single obvious primary argument is fine as positional (e.g., a filename: `mycli process data.csv`).

### Accept stdin where data input makes sense

Support `--stdin` or `-` for commands that accept data payloads (config, file content, lists). This enables pipeline composition without temporary files.

```bash
cat config.json | mycli config import --stdin
mycli deploy --env staging --tag $(mycli build --output tag-only)
```

---

## Help & Discovery

### Provide --help on every command and subcommand

Implement `-h` and `--help`. For scripts with subcommands, provide help at every level.

### Include examples in every --help

Examples are the most effective part of help text -- they communicate flag names, value formats, and common usage patterns in one line. Include 2-5 examples per command, covering the most common invocations.

```
$ mycli deploy --help
Deploy an image to a target environment.

Options:
  --env     Target environment (staging, production)  [required]
  --tag     Image tag (default: latest)
  --force   Skip confirmation

Examples:
  mycli deploy --env staging
  mycli deploy --env production --tag v1.2.3
  mycli deploy --env staging --force
```

### Progressive disclosure for subcommands

Top-level help lists subcommand names with one-line descriptions only. Detailed flags and examples live in each subcommand's own `--help`.

```
$ mycli --help
Usage: mycli <command> [options]

Commands:
  deploy    Deploy an image to an environment
  build     Build and tag an image
  config    Manage configuration

Run 'mycli <command> --help' for details.
```

### Provide --version

Print the version string to stdout and exit. Use semantic versioning if applicable.

---

## Output

### Separate data from messages

- **stdout** -- primary data output (results, structured data, content that gets piped)
- **stderr** -- progress messages, warnings, status updates, errors

This separation is essential for pipeline composition. If a downstream command pipes stdout, diagnostic messages on stderr won't corrupt the data stream.

### Return structured data on success

After a state-changing operation, output the key artifacts -- IDs, URLs, counts, durations. Keep it parseable.

```
deployed v1.2.3 to staging
url: https://staging.myapp.com
deploy_id: dep_abc123
duration: 34s
```

### Support --json for machine-readable output

Provide a `--json` flag that outputs the same data in JSON format. When `--json` is active, suppress all human-formatted messages from stdout -- only emit the JSON object.

```bash
$ mycli deploy --env staging --json
{"version":"v1.2.3","environment":"staging","url":"https://staging.myapp.com","deploy_id":"dep_abc123","duration_seconds":34}
```

### Keep output concise on success

Brief confirmation with key data. Avoid decorative output, banners, or excessive whitespace. The caller needs the result, not congratulations.

---

## Error Handling

### Fail fast on bad input

Validate all flags and required inputs before doing any work. If a required flag is missing or a value is invalid, error immediately -- do not partially execute and then fail.

### Make errors actionable

Every error message must include:
1. What went wrong
2. The correct invocation to fix it
3. Where to find valid values (when applicable)

```
Error: No image tag specified.
  mycli deploy --env staging --tag <image-tag>
  Available tags: mycli build list --output tags
```

Vague errors ("invalid input", "operation failed") cause retry loops. Specific errors get resolved in one attempt.

### Use meaningful exit codes

| Code | Meaning |
|------|---------|
| `0`  | Success |
| `1`  | General error |
| `2`  | Invalid usage (bad flags, missing required args) |

Add command-specific codes only when the caller needs to branch on them. Document non-standard codes in `--help`.

### Write errors to stderr

Error messages go to stderr, not stdout. This keeps stdout clean for piped data even when the command fails.

---

## Safety & Reliability

### Make commands idempotent

Running the same command twice must produce the same end state. If the desired state already exists, return success (exit 0) and indicate it was a no-op.

```bash
$ mycli deploy --env staging --tag v1.2.3
deployed v1.2.3 to staging

$ mycli deploy --env staging --tag v1.2.3
already deployed, no-op
```

This is critical because agents retry on timeouts, context loss, and transient failures. A non-idempotent command that creates duplicates or errors on re-run breaks automated workflows.

### Provide --dry-run for destructive or state-changing actions

Let the caller preview what would happen without committing. The dry-run output should use the same format as the real execution so parsing logic works for both.

```bash
$ mycli deploy --env production --tag v1.2.3 --dry-run
Would deploy v1.2.3 to production
  - Stop 3 running instances
  - Pull image registry.io/app:v1.2.3
  - Start 3 new instances
No changes made.
```

### Provide --yes or --force to skip confirmations

Destructive operations should confirm by default when stdin is a TTY. Provide `--yes` or `--force` to bypass confirmation for non-interactive use.

```bash
# human -- gets confirmation prompt
$ mycli delete --env staging
Are you sure? [y/N]

# agent/script -- skips prompt
$ mycli delete --env staging --yes
```

---

## Command Structure

### Use a consistent naming pattern

Pick one pattern and apply it uniformly:

- **noun-verb**: `mycli service list`, `mycli service create`
- **verb-noun**: `mycli list services`, `mycli create service`

Consistency matters because agents generalize from patterns. If `list` works on one resource, the same syntax should work on every resource.

### Standard flags across all subcommands

These flags should behave identically everywhere they appear:

| Flag | Behavior |
|------|----------|
| `-h, --help` | Show help and exit |
| `--version` | Print version and exit |
| `--json` | Output in JSON format |
| `--dry-run` | Preview without executing |
| `--yes, --force` | Skip confirmation prompts |
| `--verbose` | Increase output detail |
| `--quiet` | Suppress non-essential output |

Only include the flags that are relevant to the script. A simple script with no destructive operations doesn't need `--dry-run` or `--force`.

---

## Applicability

Not every script needs every requirement above. Scale to the complexity of the tool:

**Simple script** (single operation, no subcommands): flags for inputs, `--help` with examples, actionable errors, proper exit codes, stdout/stderr separation.

**Multi-command tool**: all of the above, plus progressive help discovery, consistent command structure, `--json`, `--dry-run`, idempotency.

The non-negotiable baseline for any script: no hanging on missing input, `--help` works, errors are actionable, exit codes are correct.

---

## Output Format

When auditing an existing CLI, produce a pass/fail assessment organized by section (Input Handling, Help & Discovery, Output, Error Handling, Safety & Reliability, Command Structure). For each failing item, include the specific fix needed with a code example.
