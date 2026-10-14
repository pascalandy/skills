---
name: "coding-standard"
description: "Use when designing, implementing, or reviewing an agent-friendly CLI, including commands, flags, help text, output, errors, and safety behavior."
kind: "dev"
keywords: ["cli", "cli-spec", "cli-design", "cli-implementation", "cli-audit", "agent-friendly", "composability", "idempotent", "retry-safe"]
---

# Coding Standard

Language-agnostic coding disciplines: what good design looks like, regardless of implementation language.

## Output contract

Every script and CLI answers in one compact JSON line. [script-output](https://github.com/pascalandy/skills/blob/main/docs/references/script-output.md) holds the rule, how to read the answer, and why; read it before you design or change what a command prints. It overrides the sub-skills' advice on output, such as a silent success or an opt-in `--json`.

- Everything passed: `{"ok":true}` on stdout, exit 0
- Anything else: stdout stays empty, the last line of stderr is `{"ok":false,"errors":["…"]}`, and the exit code is not 0. Each error says what failed and the command that fixes it
- A warning that needs action fails the command; other detail moves to `-v`
- Data beside `ok` only when it is the command's job: a list, a dry run, `changes` such as `[["add","path"]]`, or the `file` a content command wrote
- `--help` stays text

## Sub-skills

When the user or project supplies its own CLI contract, follow it; use these sub-skills only for what it leaves open. Load the file of the row that matches the request:

| Request | Load |
|---|---|
| Write a CLI spec: design the surface and parameters before implementing, or refactor an existing surface: command tree, args and flags tables, output rules, exit code map, config precedence, examples, from a condensed [clig.dev](https://clig.dev/) rubric | [references/CliSpec/MetaSkill.md](references/CliSpec/MetaSkill.md) |
| Build or implement a CLI, or review its code or UX: I/O streams, help text, output, errors, argument parsing, interactivity, subcommands, robustness, signals, configuration, env vars, naming, distribution, and a 100+ item stress-test checklist | [references/CliImpl/MetaSkill.md](references/CliImpl/MetaSkill.md) |
| Audit a CLI for agent-friendliness: requirements, structured output, composability and pipelines, all inputs via flags, idempotent and retry-safe commands, non-interactive operation, operability, errors resolvable in one attempt, safety checks with `--dry-run` and `--force` | [references/CliAudit/MetaSkill.md](references/CliAudit/MetaSkill.md) |

## Out of scope

- Language syntax, idioms, tooling, package managers, and framework patterns: use `coding-language`

## Credits

- CLI Guidelines -- [clig.dev](https://clig.dev/) by Aanand Prasad, Ben Firshman, Carl Tashian, Eva Parish
- Agent-friendly requirements -- adapted from [agent-scripts](https://github.com/steipete/agent-scripts) by Peter Steinberger
