---
description: "CU2: assemble and refine eligible Epics into a Milestone with its own checkable outcome, then deliver one combined proposal."
---

# CU2. Epics to ready Milestones

```
Milestone progress:
- [ ] 1. Scope eligible Epics
- [ ] 2. Assemble and check the Milestone
- [ ] 3. Deliver the whole proposal
```

## Process

1. **Scope eligible Epics.** When continuing from `epic`, reuse its proposed
   Epics, scope and verified evidence. When invoked directly, resolve the home
   repo and inspect open Epics without a Milestone to identify candidate groups.
   Each group needs at least two Epics serving one shared deliverable outcome.
   An Epic joins at most one Milestone; when it fits competing groups, record
   that choice as unresolved input.
   Report unrelated Epics and issues outside any Epic as outside this grouping.
   Read all Stories and current evidence for the selected Epics.
   Done when all eligible Epics and left-out items are accounted for
2. **Assemble and check.** Check each selected Epic with its Stories against the
   Grouping checks and the Definition of Ready, reusing `epic`'s results when
   their inputs are unchanged.
   If no group qualifies, explain why and deliver any refinements from `epic`.
   Number each `M<N> · <outcome>` after the highest existing or drafted M number,
   closed Milestones included.
   Use the shared Epic order, justified blockers and recorded Story tiers.
   Apply the same checks to the Milestone description and any affected Epics.
   Done when the proposed hierarchy meets the Definition of Ready or its missing input is named
3. **Deliver.** Deliver one proposal through
   [Approval, apply and readback](../SKILL.md#approval-apply-and-readback),
   including any Epic and Story changes from the same run. Report the Milestone URL
   when created, Epics by Rank for each Milestone, outcome checks, failed actions
   and left-out items.
   Done when that procedure finishes
