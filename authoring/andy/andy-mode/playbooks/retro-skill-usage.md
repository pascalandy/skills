# Retro skill usage

Post-mortem on the skills the agent loaded in this conversation.

Find where a skill was wrong, contradictory, or confusing enough to cost the agent a detour: a missing detail, a step that failed, an instruction that sent the agent in circles. Keep a finding only if:
- it would recur in another task using the same skill (skip one-offs, the agent's own mistakes, and outside failures), and
- the fix fits in one sentence or one changed line of the skill.

Include every finding that passes. If none do, say so and stop.

Cite evidence for each finding: the skill file and line (or section) the agent followed, and the step where it went wrong. If the agent can't point to it, drop it.

Draft one issue per finding for https://github.com/pascalandy/skills. Write in the language of the conversation and keep the template's headings.

**Readers.** The end user reads the visible part to understand the problem and decide. The agent that fixes it reads the collapsed details. Write the visible part so a 12-year-old could follow it: an everyday analogy, short sentences, plain words. Call the actors "the agent" and "the end user". Keep analysis (CMO) apart from action (FMO, Decision).

**Title.** Use Conventional Commits in the form `type(skill): subject`. Use `fix` when the skill is wrong or contradictory, `docs` when it is only unclear, and `feat` when a step is missing. Write the subject as the behavior the skill should have, in plain words and the imperative, for example `fix(commit): keep a move and its pointer updates in one commit`. Do not add a trailing period.

**Body.** Follow this template. [#216](https://github.com/pascalandy/skills/issues/216) is a real example. Keep the visible part under about 45 lines, and drop a details subsection that has nothing to say. Letter the Decision options as in Approaches considered, so the end user can answer with one letter. When the fix adds a line, replace the FMO's change block with "Add one line in `<path>`, under `<## Section>`, after this line:", quote the whole sentence or line it follows, then give the new line.

````md
## CMO: The problem, simply

<An everyday analogy in one or two sentences.>

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

<Map the analogy back to the real event: the commit, file, or step, and what it broke. Say plainly how bad it was.>

REF: #<PR or issue>

### Why it happened

<The rule in the skill that caused it, in plain words, and the conflict or gap in it.>

## FMO (future Mode of operation)

Change one line in `<authoring path to the skill file>`, under `<## Section>`. It currently says:

> <exact current line>

It would say instead:

> <exact new line, in the skill's own words>

That's the whole fix: one line.

## How we'll know it works

1. **Before the change:** <rerun the failing scenario with the current skill, in three fresh sessions when the result depends on the agent's choices>. If <it never fails>, the problem doesn't repeat: choose <ignore letter>
2. **After the change:** <the same scenario and the result that proves the fix>
3. **Nothing else changes:** <a nearby case that must keep its current result>
4. `just check` passes

## Decision

- **<letter>) Fix it (recommended):** <why it matters beyond this one case>
- **<letter>) Ignore it:** <the honest case for doing nothing>

Test 1 settles it: <which result means ignore>.

<details>
<summary>Details for the agent</summary>

### <The evidence, such as the conflicting rules>

<File and line numbers, and the real commits, steps, or output that show the failure.>

### Acceptance cases

1. <case → expected result; mark the one that is the bug>

### Edge cases

- <edge case → how the fix handles it>

### Approaches considered

- **A. <approach>:** <why not>
- **B. <approach> (recommended):** <why>
- **C. Ignore it:** <the cost of leaving the skill as it is>

### Out of scope

<What this fix leaves alone.>

</details>
````

Before publishing:

1. For each finding, search open issues (`gh issue list -R pascalandy/skills --search "<skill> in:title"`). If one already reports the problem, draft a comment on it instead of a new issue.
2. The repo is public: remove session IDs, local paths, hostnames, private repo or project names, and any conversation content that isn't about the skill.
3. Run the `2nd-pass` skill on the drafts. A draft passes when the end user can say what broke and what the fix changes without opening the details.

Then publish with labels `2-type:postmortem`, `1-needs-triage`, read each issue back, and return the links.
