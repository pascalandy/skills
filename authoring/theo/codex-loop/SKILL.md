---
name: "codex-loop"
description: "Use when the user says 'codex loop' 'sol loop' or 'better call sol'."
kind: "dev"
---

# codex-loop

Load `review-loop` and follow it with this reviewer:

- Model: the `sol` alias at `xhigh`. When the user mentions Astra: the `astra`
  alias at `high`. Read `fleet/references/active-models.toml` and resolve the
  alias to its `id`; without the fleet skill, the newest Sol or Astra
- T3: a provider whose driver is `codex`, effort option `reasoningEffort`
- Outside T3: a native Sol subagent. In Claude Code, a custom subagent only if
  it is set up to run Sol
- Name in the report: Sol
