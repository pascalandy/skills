# Issue template: retro-skill-usage

````md
<retro-skill-usage>
## CMO: The problem

### Problem Statement

The problem that the user is facing, from the user's perspective.

REF: #<PR or issue>

### Analogy

<An everyday analogy in one or two sentences.>

- **What should happen:** <in the analogy's terms>
- **What happened in #<PR>:** <what the agent did, in the analogy's terms>

<Map the analogy back to the real event: the commit, file, or step, and what it broke. Say plainly how bad it was.>

### Why it happened

<The rule in the skill that caused it, in plain words, and the conflict or gap in it.>

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

### <The evidence, such as the conflicting rules>

File and line numbers, and the real commits, steps, or output that show the failure.

### Acceptance cases

1. case → expected result; mark the one that is the bug

### Edge cases

- edge case → how the fix handles it

### Approaches considered

- **A. <approach>:** <why not>
- **B. <approach> (recommended):** <why>
- **C. Ignore it:** <the cost of leaving the skill as it is>

### Out of scope

What this fix leaves alone.

</details>

</retro-skill-usage>
````
