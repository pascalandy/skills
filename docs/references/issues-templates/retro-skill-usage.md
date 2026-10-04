# Issue template: retro-skill-usage

````md
<retro-skill-usage>
## The problem (CMO)

**Problem Statement:** <the end user's goal and the problem, restated plainly>

List the **use cases**, edge cases included

What's out of scope

REF: #<PR or issue>

### Analogy

An everyday analogy in one or two sentences, explain like I'm 12, so the end user can tell the analysis from what is actionable.

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

Map the analogy back to the real event: the commit, file, or step, and what it broke. Say plainly how bad it was.

### Why it happened

The rule in the skill that caused it, in plain words, and the conflict or gap in it.

## The change (FMO)

Change one line in `<authoring path to the skill file>`, under `<## Section>`. It currently says:

> <exact current line>

It would say instead:

> <exact new line, in the skill's own words>

That's the whole fix: one line.

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
