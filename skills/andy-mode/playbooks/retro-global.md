---
description: "Review a coding session for changes to the agent's environment, such as checks, steering files, or tools, that would help the next run."
---

# Retro global

Review the coding agent's **environment** so future runs go better. This is not an incident postmortem or a review limited to the skills loaded in the session.

## Procedure

1. Read the primary sources for the session the user names: conversation, tool results, relevant diffs, and checks. Default to the current session. If the relevant history is inaccessible, identify what is missing and ask for it rather than reconstructing events.
2. Look for candidates for improvement in the categories below. Treat them as prompts, not a requirement to produce a finding in each category. Inspect the existing mechanism before proposing a replacement.
3. Keep a finding only when you can cite a specific session observation and explain how the proposed change would help a future run. Rank by likely impact and recurrence, taking implementation cost into account. Separate facts from inference.
4. Present the findings to the user. A finding is easier to act on when it covers what happened and the evidence, what exists today, the smallest change, and how to check it worked; tradeoffs and blast radius help when material. If none pass the evidence bar, say so and stop. Suggest changes; do not edit the environment as part of the retrospective.

## Where to look

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer**, such as a "Read on demand" line in the repo's `AGENTS.md`, make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: could a check have caught a mistake the agent made? Read the repo's `justfile` (usually `just check`) and `lefthook.yml` first, so a check that exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no `just check`, or no lefthook hook running it) is itself a finding. _Use when_ the agent made a mistake a check could have caught, or the repo has no guardrail.
- **Coding standards**: standards live in skills (`coding-language`, `coding-standard`, the `principle-*` skills). Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check in `just check`, reported under the Automated checks area. A **judgement call** no check can replace belongs to the skill that states it: report it with `retro-skill-usage`. _Use when_ a review missed a mistake, or the agent broke a rule a skill states.
- **Steering files**: should always-loaded instructions move behind a pointer, into a skill, or into a check? These load every turn: the global `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, and `~/.config/opencode/AGENTS.md`, the repo's `AGENTS.md`, the agent's memory index (`MEMORY.md`), and every skill description. Load `writing-for-agents` before proposing an edit to one. _Use when_ one of them is large, or a skill fired when it should not have, or failed to fire.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is any custom tooling (a CLI, an MCP server, a `just` recipe) particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files or skills that don't change the agent's behavior. Distinguish a useless instruction from one the agent failed to follow. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information, such as teeing dev server logs or read-only access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

## Publishing findings

Draft one issue per finding in the repository that owns the change: the project for its `AGENTS.md`, `justfile`, or hooks, `pascalandy/skills` for a skill, and `pascalandy/dotfiles` for global config it tracks. A finding with no owning repository, or whose repository sits outside `pascalandy`, stays in the report. Write in the language of the conversation. Compress with the `concise` skill.

**Titles.** Use Conventional Commits in the form `type(scope): subject`, where the scope names the area to change, for example `feat(lefthook): run just check before push`. Use `fix` when an instruction or check is wrong, `docs` when an instruction is only unclear or a pointer is missing, and `feat` when a check, step, or tool is missing. Keep the subject short and imperative, naming the change. Name a real symbol when one carries the change, such as a recipe, file, or flag. Do not add a trailing period.

**Body.** Follow this template. The end user reads the visible part to decide; the agent that fixes it reads the collapsed details. Answer N/A in a section that does not apply, and add a section when the finding needs one.

````md
<retro-global>
## The problem (CMO)

**Area:** <Navigation, Automated checks, Steering files, Tool economy, No-ops, or Information access>

**Problem Statement:** As an agent working in `<repo>`, I want <…>, so that <…>

REF: #<PR or issue>

### Analogy

An everyday analogy in one or two sentences, explain like I'm 12, so the end user can tell the analysis from what is actionable.

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

### What we saw

What the agent was doing and what it ran into: a failure, a detour, or a missing piece. Say plainly what it cost: time, tokens, or a wrong result.

### What exists today

The check, file, or tool already in place, if any, and why it fell short: missing, unwired, or silently broken.

## Start, Stop, Continue (FMO)

- **Start:** <what the agent or its environment starts doing>
- **Stop:** <what it stops doing>
- **Continue:** <what already works and must keep working>

## How we'll know it works

1. **Today:** <how to see the problem or the gap now>
2. **After the change:** <the same check and the result that proves it>
3. **Nothing else changes:** <the Continue case keeps its current result>

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

Technical details, evidence, approaches considered, blast radius, non-functional requirements, and links to related issues or PRs.

</details>

</retro-global>
````

Before publishing:

1. For each finding, search the target repository's open issues. If one already reports the problem, draft a comment on it instead of a new issue.
2. If the repository is public, remove session IDs, absolute local paths, hostnames, private repo or project names, and any conversation content that isn't about the finding.
3. Run the `2nd-pass` skill on the drafts.

Then publish with labels `1-needs-triage` and `2-type:postmortem` (or `2-type:task` where the repository lacks it), read each issue back, and return the links. Each issue links the session's PR when one exists, except when a public issue would link a private repository.
