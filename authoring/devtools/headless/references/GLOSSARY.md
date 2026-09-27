---
name: "Headless glossary"
description: "Vocabulary for the headless skill"
tags:
  - "kind/glossary"
  - "kind/project"
date_created: 2026-07-01
date_updated: 2026-09-27
---

# Headless glossary

Definitions only. [SKILL.md](../SKILL.md) selects the procedure; each CLI reference owns its flags.

| Term | Meaning |
| --- | --- |
| Headless | Non-interactive CLI execution |
| Target CLI | The command-line application selected to perform the task |
| Workdir | The directory used as the child process's project context |
| PTY | A pseudo-terminal; distinct from ordinary stdin/stdout pipes |
| Permission mode | A CLI's policy for allowing, denying, or requesting approval for tool calls |
| Sandbox | Execution restrictions enforced separately from the task prompt |
| Event stream | Machine-readable records of execution, distinct from the final answer |
| Structured result | A final response with a defined schema |
| Session ID | An identifier for persisted conversation state |
| Process handle | The runner's identifier for a live process; not necessarily a session ID |
| Ephemeral run | A run without a saved resumable conversation; explicit logs may still be written |
| Model pinning | Selecting a model explicitly instead of using configured defaults |
