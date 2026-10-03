---
name: "Headless glossary"
description: "Vocabulary for the headless skill"
tags:
  - "kind/glossary"
  - "kind/project"
date_created: 2026-07-01
date_updated: 2026-10-03
---

# Headless glossary

Definitions only. [SKILL.md](../SKILL.md) selects the procedure; `scripts/headless.py` owns the Codex and Claude flags, `config.toml` owns the defaults, and each CLI reference owns the rest.

| Term | Meaning |
| --- | --- |
| Headless | Non-interactive CLI execution |
| Harness | The CLI that runs the child agent: Codex, Claude Code, Pi, or OpenCode |
| Provider | The service that serves a model to Pi or OpenCode; several providers can serve one model |
| Code review | A CLI's built-in reviewer applying its own criteria to one diff: `codex exec review`, which also takes custom instructions in place of the diff, or Claude Code's `/review` |
| PTY | A pseudo-terminal; distinct from ordinary stdin/stdout pipes |
| Permission mode | A CLI's policy for allowing, denying, or requesting approval for tool calls |
| Sandbox | Execution restrictions enforced separately from the task prompt |
| Event stream | Machine-readable records of execution, distinct from the final answer |
| Session ID | An identifier for persisted conversation state |
