---
description: "Find where a skill loaded in a session was wrong or confusing enough to cost a detour, and propose one-line fixes."
---

# Retro skill usage

Post-mortem on the skills the agent loaded in this conversation.

Find where a skill was wrong, contradictory, or confusing enough to cost the agent a detour: a missing detail, a step that failed, an instruction that sent the agent in circles. Keep a finding only if:
- it would recur in another task using the same skill (skip one-offs, the agent's own mistakes, and outside failures), and
- the fix fits in one sentence or one changed line of the skill.

Report missing or broken deterministic checks through `retro-global`; reserve skill-rule fixes here for judgement calls. Include every finding that passes. If none do, say so and stop.

Cite evidence for each finding: the skill file and line (or section) the agent followed, and the step where it went wrong. If the agent can't point to it, drop it.

Draft one issue per finding for https://github.com/pascalandy/skills. Write in the language of the conversation and keep the template's headings.

**Readers.** The end user reads the visible part to understand the problem and decide. The agent that fixes it reads the collapsed details. Write the visible part so a 12-year-old could follow it, with short sentences and plain words. Call the actors "the agent" and "the end user". Keep analysis (CMO) apart from action (FMO).

**Title.** Use Conventional Commits in the form `type(skill): subject`. Use `fix` when the skill is wrong or contradictory, `docs` when it is only unclear, and `feat` when a step is missing. Write the subject as the behavior the skill should have, in plain words and the imperative, for example `fix(commit): keep a move and its pointer updates in one commit`. Do not add a trailing period.

**Body.** Follow this template. Keep the visible part under about 45 lines. Answer N/A in a section that does not apply, and add a section when the finding needs one. When the fix adds a sentence or line, replace the FMO's change block with "Add one sentence or line in `<path>`, under `<## Section>`, after:", quote the whole sentence or line it follows, then give the addition.

````md
<retro-skill-usage>

## The problem (CMO)

**Problem Statement:** <the end user's goal and the problem, restated plainly>

List the **use cases**, edge cases included

What's out of scope

REF: <#N in the issue's repository, owner/repo#N in another>

### Analogy

An everyday analogy in one or two sentences, explain like I'm 12, so the end user can tell the analysis from what is actionable.

- **What should happen:** <in the analogy's terms>
- **What happened in <PR or session>:** <what the agent did, in the analogy's terms>

Map the analogy back to the real event: the commit, file, or step, and what it broke. Say plainly how bad it was.

### Why it happened

The rule in the skill that caused it, in plain words, and the conflict or gap in it.

## The change (FMO)

Change one sentence or line in `<authoring path to the skill file>`, under `<## Section>`. It currently says:

> <exact current sentence or line>

It would say instead:

> <exact new sentence or line, in the skill's own words>

That's the whole fix.

## How we'll know it works

1. **Before the change:** <the recorded evidence from the session, or a rerun of the scenario when it is cheap>
2. **After the change:** <the same scenario and the result that proves the fix>
3. **Nothing else changes:** <a nearby case that must keep its current result>
4. `just check` passes

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

Technical details, evidence, approaches considered, blast radius, non-functional requirements, and links to related issues or PRs.

</details>

</retro-skill-usage>
````

Before publishing:

1. For each finding, search open issues (`gh issue list -R pascalandy/skills --search "<skill> in:title"`). If one already reports the problem, draft a comment on it instead of a new issue.
2. The repo is public: remove session IDs, local paths other than the skill's repository-relative authoring path, hostnames, private repo or project names, and any conversation content that isn't about the skill.
3. Run the `2nd-pass` skill on the drafts. A draft passes when the end user can say what broke and what the fix changes without opening the details.

Then publish with labels `2-type:postmortem`, `1-needs-triage`, read each issue back, and return the links.
