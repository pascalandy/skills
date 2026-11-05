---
name: "cc-loop"
description: "Use when the user says 'cc loop', 'claude loop', 'opus loop', or 'better call opus'."
kind: "dev"
---

# cc-loop

Load `review-loop` and follow it with this reviewer:

- Model: the latest Opus at `high`
- T3: provider `claudeAgent`, effort option `effort`
- Outside T3: in Claude Code, a native subagent with `model: opus` and the
  chosen effort. Codex has no native route to Opus
- Name in the report: Opus
