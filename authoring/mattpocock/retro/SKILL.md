---
name: "retro"
description: "Review a coding session for evidence-backed improvements to agent navigation, instructions, checks, or tools."
---

Review the coding agent's **environment** so future runs go better. This is not an incident postmortem or a review limited to the skills loaded in the session.

## Procedure

1. Read the primary sources for the session the user names: conversation, tool results, relevant diffs, and checks. Default to the current session. If the relevant history is inaccessible, identify what is missing and ask for it rather than reconstructing events.
2. Look for candidates for improvement in the categories below. Treat them as prompts, not a requirement to produce a finding in each category. Inspect the existing mechanism before proposing a replacement.
3. Keep a finding only when you can cite a specific session observation and explain how the proposed change would help a future run. Rank by likely impact and recurrence, taking implementation cost into account. Separate facts from inference.
4. Present the findings to the user. A finding is easier to act on when it covers what happened and the evidence, what exists today, the smallest change, and how to check it worked; tradeoffs and blast radius help when material. If none pass the evidence bar, say so and stop. Suggest changes; do not edit the environment as part of the retrospective.

## Where to look

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer** make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: are there automated checks that could catch errors the agent made? Linting, typing, tests, filesystem linters? Read the repo's own check command first (its `package.json` or build-tool `lint`/`check` scripts, its CI workflow), so a check that already exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no pre-commit hook and no CI job running its lint, typecheck, or test command) is itself a finding: an un-linted repo is a standing missed opportunity, not a neutral default. _Use when_ the agent made a mistake an automated check could have caught, or the repo has no guardrail at all.
- **Coding standards**: should the **reviewer agent** be given a new rule to enforce? Should an existing rule be removed or clarified? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check, full stop: a custom rule in the repo's own linter, a new pre-commit hook, or a new CI job, whichever the repo's language and existing guardrail make cheapest. Default to building the check over writing the rule. Reserve written standards such as `CODING_STANDARDS.md` for genuine **judgement calls** (cross-file consistency, "matches the surrounding style," anything no guardrail could ever substitute for). Load `writing-for-agents` before proposing edits to agent-facing instructions. _Use when_ the reviewer agent failed to catch a mistake.
- **Steering files**: are there instructions in `AGENTS.md`/`CLAUDE.md` that should move to coding standards or automated checks instead? _Use when_ the file is particularly large, in the repo or the user's global scope.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is any custom tooling (CLIs, MCPs) particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files that don't change the agent's behavior. Distinguish a useless instruction from one the agent failed to follow. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information, such as teeing dev server logs or read-only access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

## Publishing findings

If the user wants issues, draft one per finding in the language of the conversation, in the repository that owns the change: the project for its `AGENTS.md`, checks, or scripts, or the upstream repository for a shared skill or tool. A finding whose target has no issue tracker, such as a personal global config, stays in the report.

Before publishing, search the repository's open issues for duplicates; when one already reports the problem, draft a comment on it instead of a new issue. For a public repository, redact session IDs, absolute local paths, hostnames, private project names, and unrelated conversation details. Run `2nd-pass` on the drafts. Publish only when authorized, following the repository's title and label conventions and linking the session's PR when one exists, then read each issue back and return the links.
