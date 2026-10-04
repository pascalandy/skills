# Issue template: retro-skill-usage

````md
<retro-skill-usage>
## CMO: The problem

**Problem Statement:** Restate my goal and the problem in your own words

List the **use cases**, edge cases included

What's out of scope

REF: #<PR or issue>

### Analogy

Assume the user find your answer hard to parse, and he can't tell which parts of the problem you're actually solving. So I'm not sure what is the part of it that is the analysis and *what is the part that is actionable* that can help to take decisions.

Please give me a simpler, easy-to-digest, "explain like I'm 12y/o" description of how you plan to fix these problems?

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

Map the analogy back to the real event: the commit, file, or step, and what it broke. Say plainly how bad it was.

### Why it happened

The rule in the skill that caused it, in plain words, and the conflict or gap in it.

## FMO (future Mode of operation)

Change one line in `<authoring path to the skill file>`, under `<## Section>`. It currently says:

> <exact current line>

It would say instead:

> <exact new line, in the skill's own words>

That's the whole fix: one line.

## How we'll know it works

1. **Before the change:** <rerun the failing scenario with the current skill, in three fresh sessions when the result depends on the agent's choices>. If <it never fails>, the problem doesn't repeat
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
