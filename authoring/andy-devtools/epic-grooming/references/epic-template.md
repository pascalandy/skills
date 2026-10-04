# Epic template

Step 4 writes every issue as an issue entry, and Step 5 builds each Epic from the whole template.

## Issue entry

The user reads this entry instead of the issue, so it must stand alone: a plain-words name, then what happens today and what changes after. The number goes in parentheses, for bookkeeping only. Mark the entry `text` when only prose changes and `code + tests` when the fix touches code.

```md
1. **<the problem, in plain words>** (#<number>) · <text | code + tests>
   - **Today:** <what happens now, with observed frequency and cost. State what is unknown>
   - **After:** <what changes once the fix lands>
```

Example:

```md
1. **A silent `just check`** (#430) · text
   - **Today:** when every check passes, `just check` prints nothing. The agent thinks the output got lost and reruns it three or four times. It happened twice
   - **After:** the agent recognizes silence as success and runs passing checks once
```

## Epic issue

Title: `Epic <N> · <the outcome, in plain words>`

Number the steps in work order, one issue entry per step. When a step groups several issues, give it a short `###` heading and list its entries under it. Out of this Epic names neighboring work and the Epic or issue that owns it; add below it what the next planner needs, such as a fix that quotes text that has since changed. Drop the "Before this batch" line when no Epic was kept.

````md
<epic-grooming>

## The problem (CMO)

What goes wrong today, in plain words, with observed frequency and cost.

REF: #<issue>, #<issue>

## The outcome (FMO)

What is true once the Epic is done: the rule or the result, in plain words.

## Steps

1. **<the problem, in plain words>** (#<number>) · <text | code + tests>
   - **Today:** <what happens now, with observed frequency and cost>
   - **After:** <what changes once the fix lands>
2. **<the problem, in plain words>** (#<number>) · <text | code + tests>
   - **Today:** <…>
   - **After:** <…>

## Done when

<An outcome someone can check.> Every member is closed with evidence of its fix on the default branch or a documented cleanup reason.

## Order

Batch of <YYYY-MM-DD>, Epic <position> of <count>. Work the batch in this order:

1. Epic <N> · <outcome> (#<number>)
2. **Epic <N> · <outcome> (#<number>), this Epic**

Before this batch: <the kept open Epics, by Epic number>

<One sentence: why this place.>

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

### Out of this Epic

- <Neighboring work, and the Epic or issue that owns it>

Technical details, evidence, approaches considered, blast radius, non-functional requirements, and links to related issues or PRs.

</details>

<The signature the user sets>

</epic-grooming>
````

The Order section places the Epic in its batch. Leave out how to work the Epic, such as PR order or review steps.
