---
name: "dsf-loop"
description: "Use when the user says 'dsf loop', 'deepseek loop', or 'better call deepseek'."
kind: "dev"
configuration-is-needed: true
---

# dsf-loop

Load `review-loop` and follow it with this reviewer:

- Model: `ds4p1-slow`, DeepSeek V4.1 Flash through Pascal's cliproxy hub, at
  `max`
- T3: provider `pi`, model `openrouter-hub/ds4p1-slow`, effort option
  `thinking`
- Outside T3: Pi headless, as the `headless` skill's Pi reference says, with
  `--model openrouter-hub/ds4p1-slow --thinking max`. The recipe keeps no session, so
  each round is a fresh run with the round 1 brief and the ledger. Its tools
  cannot run git, so put the diff in the prompt file
- Name in the report: DeepSeek Flash (`ds4p1-slow`)
