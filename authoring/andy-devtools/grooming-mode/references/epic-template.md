# Epic template

Every Story entry stands alone. Keep the same order as native sub-issue Rank.
Cross-repo references use `OWNER/REPO#N`.

Title: `Epic <N> · <outcome in plain words>`

````md
<grooming-mode>

## The problem (CMO)

<What goes wrong today, with observed frequency and cost; state what is unknown>

REF: #<issue>, OWNER/REPO#<issue>

## The outcome (FMO)

<What is true once the Epic is done>

## Stories

1. **<problem in plain words>** (#<number>) · <text | code + tests>
   - **Today:** <current behavior and evidence>
   - **After:** <result once the Story is done>
2. **<problem in plain words>** (OWNER/REPO#<number>) · <text | code + tests>
   - **Today:** <current behavior and evidence>
   - **After:** <result once the Story is done>

## Done when

<A checkable outcome with no open decision>
Every Story has a documented disposition and the outcome holds on the default branch.

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

### Out of this Epic

- <Neighboring work and its numbered Epic or issue reference>

<Technical evidence, file conflicts, native blocked-by rationale, uncertainty,
approaches considered and related PRs>

</details>

<The signature the user sets>

</grooming-mode>
````
