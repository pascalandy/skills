# Issue template: epic-grooming

Title: `Epic <N> · <the outcome, in plain words>`

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
