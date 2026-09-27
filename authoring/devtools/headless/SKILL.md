---
name: "headless"
description: "Use when the user asks how to run `codex exec`, Claude Code, OpenCode, or Pi non-interactively."
---

# Headless CLI agents

Load only the reference for the requested path:

- For `codex exec` or `headless-codex`, read [Run Codex headlessly](references/codex/MetaSkill.md)
- For Claude Code or `headless-claude`, read [Claude Code](references/claude/MetaSkill.md)
- For OpenCode or `headless-opencode`, read [OpenCode](references/opencode/MetaSkill.md)
- For Pi or `headless-pi`, read [Pi](references/pi/MetaSkill.md)
- For skill maintenance, follow the [update checklist](references/UPDATE.md)

Read the [glossary](references/GLOSSARY.md) only when its terminology is needed. For current CLI behavior, check the installed command's `--help` and its official documentation.

Capture reviewer output without filtering. Use the plain CLI commands below, or `rtk proxy <command>` when RTK is required; for example, `rtk proxy env CLAUDE_CODE_EFFORT_LEVEL=xhigh claude ...`. Use `rtk proxy jq ...` to extract an answer from JSON without shortening it. Event logs are execution records; read the complete final answer before deciding whether the review succeeded. Delegation policy belongs to the calling workflow, not this skill.
