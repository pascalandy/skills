---
name: "pa-retro"
description: "Use only when explicitly invoked as `pa-retro`."
---

Post-mortem on the skills you loaded in this conversation.

Find where a skill was wrong, contradictory, or confusing enough to cost you a detour: a missing detail, a step that failed, an instruction that sent you in circles. Keep a finding only if:
- it would recur in another task using the same skill (skip one-offs, your own mistakes, and outside failures), and
- the fix fits in one sentence or one changed line of the skill.

Include every finding that passes. If none do, say so and stop.

Cite evidence for each finding: the skill file and line (or section) you followed, and the step where it went wrong. If you can't point to it, drop it.

Draft one issue per finding for https://github.com/pascalandy/skills. Write in the language of the conversation. Compress with the `concise` skill.

**Titles.** Use Conventional Commits in the form `type(skill): subject`, for example `fix(commit): document non-interactive hunk staging`. Use `fix` when the skill is wrong or contradictory, `docs` when it is only unclear, and `feat` when a step is missing. Keep the subject short and imperative, naming the change the skill needs. Name a real symbol when one carries the change, such as a section, script, or flag. Do not add a trailing period.

**Body.** The issue is a briefing for whoever triages and fixes it. Keep it under about 40 lines. Use these sections in order. Drop a section when it has nothing to say.

- `## Why`. Open with the user story: "As an agent using `<skill>`, I want …, so that …". Then, in one or two short paragraphs, say what you were trying to do, what went wrong and the evidence, how you worked around it, and the change you propose.
- `## Scope`. Use bullets to list the skill files, lines or sections, and symbols to change. Name both sides of a rename or retarget. State what is in and out only when the boundary matters.
- `## Tradeoffs`. Name only alternative fixes a reviewer would otherwise ask about.
- `## Blast Radius`. In one to three sentences, name which agents or workflows load this skill, why the fix is safe or risky, and the continuing cost if the skill stays as it is.
- `## Verification`. Name the scenario that failed and the outcome that proves the fix, so whoever fixes it can rerun it.

Before publishing:

1. For each finding, search open issues (`gh issue list -R pascalandy/skills --search "<skill> in:title"`). If one already reports the problem, draft a comment on it instead of a new issue.
2. The repo is public: remove session IDs, local paths, hostnames, private repo or project names, and any conversation content that isn't about the skill.
3. Run the `2nd-pass` skill on the drafts.

Then publish with labels `2-type:postmortem`, `1-needs-triage`, read each issue back, and return the links.
