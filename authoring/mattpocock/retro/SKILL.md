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

If the user wants issues, draft one per finding in the repository that owns the change: the project for its `AGENTS.md`, checks, or scripts, or the upstream repository for a shared skill or tool. A finding whose target has no issue tracker, such as a personal global config, stays in the report as a proposed change.

Write each issue in the language of the conversation, under about 40 lines. Follow the repository's title convention; without one, use a Conventional Commit title naming the area and the change, such as `docs(agents-md): point to the fixture generator`. Pick the type from the change: `fix` for a wrong instruction or broken check, `docs` for an unclear instruction or missing pointer, `feat` for a new check, step, or tool. Build the body from the finding's fields in step 3:

- `## Why`: the observation, its evidence, and the existing mechanism or gap. Link the session's PR or commit when the evidence lives there.
- `## Scope`: the smallest proposed change, naming the files, checks, or tools it touches.
- `## Verification`: the scenario that should work afterward.

Add `## Tradeoffs` or `## Blast Radius` only when material.

Before publishing, search the repository's open issues for duplicates; when one already reports the problem, draft a comment on it instead of a new issue. For a public repository, redact session IDs, absolute local paths, hostnames, private project names, and unrelated conversation details. Run `2nd-pass` on the drafts. Publish only when authorized, using the repository's labels, then read each issue back and return the links.
