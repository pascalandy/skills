---
name: "ag-loop"
description: "Use when the user says 'ag loop', 'antigravity loop', 'neon loop', or 'better call neon'."
kind: "dev"
---

# ag-loop

Load `review-loop` and follow it with this reviewer:

- Model: the `neon` alias at `high`. Read `fleet/references/active-models.toml`
  and resolve it to its `id`; without the fleet skill, the newest Gemini Neon
- T3: the enabled provider whose driver is `antigravity`, effort option
  `thought_level`
- Outside T3: the Antigravity CLI, `agy -p --model <id> --effort high`. Confirm
  the ID with `agy models` on first use; it needs a signed-in `agy`
- Route: Antigravity calls Google directly, never the CLIProxy hub
- Name in the report: Neon
