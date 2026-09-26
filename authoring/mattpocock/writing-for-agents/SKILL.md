---
name: "writing-for-agents"
description: "Use when creating or editing non-skill documents consumed by agents, such as AGENTS.md, CLAUDE.md, handoffs, or linked instructions."
---

# Writing for agents

For a skill creation or modification request, resolve `writing-great-skills` from the active catalog or its managed repository source, read it, and stop this workflow. If the authority cannot be resolved, report the missing dependency. Do not replace it with the bundled upstream skill mechanics.

For every other agent-facing document, read and apply the complete [upstream writing reference](references/upstream/writing-for-agents.md). Its linked skill mechanics remain an imported upstream snapshot, not an active local authoring route.
