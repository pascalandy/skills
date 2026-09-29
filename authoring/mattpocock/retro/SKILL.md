---
name: "retro"
description: "Review a coding session for evidence-backed improvements to agent navigation, instructions, checks, or tools."
---

Review the coding agent's **environment** so future runs go better. This is not an incident postmortem or a review limited to the skills loaded in the session.

## Procedure

1. Read the primary sources for the session the user names: conversation, tool results, relevant diffs, and checks. Default to the current session. If the relevant history is inaccessible, identify what is missing and ask for it rather than reconstructing events.
2. Look for recurring, preventable friction in the categories below. Treat them as prompts, not a requirement to produce a finding in each category. Inspect the existing mechanism before proposing a replacement.
3. Keep a finding only when you can cite a specific session observation and explain how the proposed change would help a future run. For each, give the observation, existing mechanism or gap, smallest proposed change, and a way to verify it. Rank by likely impact and recurrence, taking implementation cost into account. Separate facts from inference.
4. Present the findings to the user. If none pass the evidence bar, say so and stop. Suggest changes; do not edit the environment as part of the retrospective.

## Where to look

- **Navigation**: time lost finding files or hidden dependencies. Would a pointer to existing information shorten the path?
- **Automated checks**: a missed mistake a check could have caught. Read the repository's check commands, hooks, and CI first; repair or wire an existing check before proposing a new one. Recommend a new guardrail when the observed failure and expected benefit justify its cost, not solely because a repo lacks CI or linting.
- **Coding standards**: a rule that was wrong, missing, or unclear. For a mechanical, repeated violation, consider a deterministic check where it is cheaper and more reliable than prose. Load `writing-for-agents` using the available skill mechanism before proposing edits to agent-facing instructions.
- **Steering files**: oversized global or repository `AGENTS.md`/`CLAUDE.md` instructions that belong in referenced material or an existing check.
- **Tool economy**: expensive or noisy tool calls with a demonstrably simpler alternative.
- **No-ops**: instructions that did not change behavior in the observed run. Distinguish a useless instruction from one the agent failed to follow.
- **Information access**: missing logs or read-only access that materially blocked the task.

## Publishing findings

If the user wants issues, draft one per finding for the relevant repository in the language of the conversation. Keep each under about 40 lines. Use a Conventional Commit-style title such as `fix(commit): document non-interactive hunk staging`: `fix` for wrong instructions, `docs` for unclear ones, `feat` for a missing step. Include `## Why` (observation and evidence), `## Scope` (specific change), and `## Verification` (the scenario that should work afterward); add tradeoffs and blast radius only when material.

Before publishing, search open issues for duplicates and update the existing issue instead where appropriate. For a public repository, redact session IDs, local paths, hostnames, private project names, and unrelated conversation details. Run `2nd-pass` on the drafts. Publish only when authorized, using the repository's labels; link the finding to a PR if one exists. Read published issues back and return their links.
