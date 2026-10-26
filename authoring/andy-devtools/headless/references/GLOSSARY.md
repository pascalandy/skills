---
name: "Headless glossary"
description: "Vocabulary for the headless skill"
tags:
  - "kind/glossary"
  - "kind/project"
date_created: 2026-07-01
date_updated: 2026-10-26
---

# Headless glossary

This glossary defines the skill's terms. [SKILL.md](../SKILL.md) selects the procedure. `scripts/headless.py` defines the Codex, Claude Code, and Grok flags. `config.toml` sets the defaults. Each CLI reference describes its other options.

| Term | Meaning |
| --- | --- |
| Headless | Non-interactive CLI execution |
| Harness | The CLI that runs the child agent: Codex, Claude Code, Grok, Pi, or OpenCode |
| Provider | The service that serves a model to Pi or OpenCode. Several providers can serve one model |
| Code review | A CLI's built-in reviewer applies its own criteria to one diff. Codex uses `codex exec review`. It also accepts custom instructions in place of the diff. Claude Code and Grok use `/review` |
| PTY | A pseudo-terminal, distinct from ordinary stdin and stdout pipes |
| Folder trust | Grok's per-folder gate on loading a repository's instructions, skills, hooks, and Model Context Protocol (MCP) servers |
| Permission mode | A CLI's policy for allowing, denying, or requesting approval for tool calls |
| Sandbox | Execution restrictions enforced separately from the task prompt |
| Event stream | Machine-readable records of execution, distinct from the final answer |
| Session ID | An identifier for persisted conversation state |
