---
name: "coding-standard"
description: "Use when designing, implementing, or reviewing an agent-friendly CLI, including commands, flags, help text, output, errors, and safety behavior."
kind: "dev"
keywords: ["cli", "cli-spec", "cli-design", "cli-implementation", "cli-audit", "agent-friendly", "composability", "idempotent", "retry-safe"]
---

# Coding Standard

Language-agnostic coding disciplines: what good design looks like, regardless of implementation language.

## Scope

**In scope:**
- CLI surface-area design (command tree, flags, exit codes, config precedence)
- CLI implementation best practices (I/O, help text, error handling, argument parsing, subcommands, signals, distribution)
- CLI agent-friendly auditing (structured output, idempotency, non-interactive operation, retry safety)

**Out of scope:**
- Language syntax, idioms, tooling, or package managers
- Framework-specific patterns

## Output contract

Every script and CLI answers in one compact JSON line. [script-output](https://github.com/pascalandy/skills/blob/main/docs/references/script-output.md) holds the rule, how to read the answer, and why; read it before you design or change what a command prints. It overrides the sub-skills' advice on output, such as a silent success or an opt-in `--json`.

- Everything passed: `{"ok":true}` on stdout, exit 0
- Anything else: stdout stays empty, the last line of stderr is `{"ok":false,"errors":["…"]}`, and the exit code is not 0. Each error says what failed and the command that fixes it
- A warning that needs action fails the command; other detail moves to `-v`
- Data beside `ok` only when it is the command's job: a list, a dry run, `changes` such as `[["add","path"]]`, or the `file` a content command wrote
- `--help` stays text

## Routing

Load `references/ROUTER.md` to dispatch request to correct sub-skill.

When the user or project supplies its own CLI contract, follow it; use these sub-skills only for what it leaves open.

## Sub-skills

| Sub-skill | Purpose |
|-----------|---------|
| `CliSpec` | Design CLI surface before implementation. Compact spec: command tree, args/flags table, output rules, exit code map, config precedence, examples. Based on condensed [clig.dev](https://clig.dev/) rubric. |
| `CliImpl` | Build CLI tools following modern best practices. I/O streams, help text, output formatting, error handling, argument parsing, interactivity, subcommands, robustness, signals, configuration, env vars, naming, distribution. Includes 100+ item stress-testing checklist. |
| `CliAudit` | Audit CLIs for agent-friendliness, composability, retry safety. All inputs via flags, the one-line JSON answer, idempotent commands, actionable errors resolvable in one attempt, `--dry-run` and `--force` for safety. |

## Credits

- CLI Guidelines -- [clig.dev](https://clig.dev/) by Aanand Prasad, Ben Firshman, Carl Tashian, Eva Parish
- Agent-friendly requirements -- adapted from [agent-scripts](https://github.com/steipete/agent-scripts) by Peter Steinberger
