---
name: "codex-loop"
description: "Use when the user says 'codex loop' 'sol loop' or 'better call sol'."
kind: "dev"
---

# codex-loop

Load `review-loop` and follow it with this reviewer:

- Model: the latest Sol at `xhigh`. When the user mentions Astra: the latest
  Astra at `high`
- T3: a provider whose driver is `codex`, effort option `reasoningEffort`
- Outside T3: a native Sol subagent. In Claude Code, a custom subagent only if
  it is set up to run Sol
- Name in the report: Sol
