# Epic template

Every Story entry stands alone. Keep the same order as native sub-issue Rank.
For cross-repo references, use `OWNER/REPO#N`.
The Stories section holds only its ordered list, without other elements alongside it.
Keep code blocks and quotes within nested Today and After details.

Title: `Epic <N> · <outcome in plain words>`

Keep the headings "The problem (CMO)" and "The outcome (FMO)". Do not explain CMO or FMO in the body.

````md
<grooming-mode>

## The problem (CMO)

<Describe what goes wrong today. State its observed frequency and cost. State what remains unknown.>

REF: #<issue>, OWNER/REPO#<issue>

## The outcome (FMO)

<Describe what is true once the Epic is done.>

## Stories

1. **<State the problem in plain words.>** (#<number>) · <text | code + tests>
   - **Today:** <Describe current behavior and evidence.>
   - **After:** <Describe the result once the Story is done.>
2. **<State the problem in plain words.>** (OWNER/REPO#<number>) · <text | code + tests>
   - **Today:** <Describe current behavior and evidence.>
   - **After:** <Describe the result once the Story is done.>

## Done when

<State the observable result. Name the command, scenario, or artifact that checks the result.
Name the Stories that cover the result. Name any joint check that the individual Story checks miss.>
Every Story has a documented disposition. The outcome has delivery evidence.

## 👨🏻‍🍳 For the agent

<details>
<summary>👨🏻‍🍳 Details</summary>

### Out of this Epic

- <Name neighboring work and its numbered Epic or issue reference.>

<Give these details:
- Technical evidence
- File conflicts
- Reasons for native blocked-by relationships
- Uncertainty
- Approaches considered and related PRs>

</details>

<Use the signature that the user sets.>

</grooming-mode>
````
