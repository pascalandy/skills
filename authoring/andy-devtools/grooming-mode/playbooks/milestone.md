---
description: "CU2: assemble and refine eligible Epics into a Milestone that has its own checkable outcome, then deliver one combined proposal."
---

# CU2. Epics to ready Milestones

CU2 is the route from eligible Epics to ready Milestones.

```
Milestone progress:
- [ ] 1. Scope eligible Epics
- [ ] 2. Assemble and check the Milestone
- [ ] 3. Deliver the whole proposal
```

## Process

### 1. Scope eligible Epics

Each candidate group for a Milestone needs at least two Epics that serve one shared deliverable outcome.
An Epic joins at most one Milestone.

1. When you continue from `epic`, reuse its proposed Epics, scope, and verified evidence.
2. When this route starts directly, use these steps:
   1. Resolve the home repo.
   2. Inspect open Epics without a Milestone to identify candidate groups.
3. When an Epic fits competing groups, record that choice as unresolved input.
4. Report unrelated Epics and issues outside any Epic as outside this grouping.
5. Read all Stories and current evidence for the selected Epics.

Done when all eligible Epics and left-out items are accounted for

### 2. Assemble and check

1. Check each selected Epic and its Stories against the Grouping checks and the Definition of Ready.
   When their inputs are unchanged, reuse the results from `epic`.
2. If no group qualifies, use these steps:
   1. Explain why.
   2. Deliver any refinements from `epic`.
3. Number each `M<N> · <outcome>` after the highest existing or drafted M number, including closed Milestones.
4. Use the shared Epic order, justified blockers, and recorded Story tiers.
5. Apply the same checks to the Milestone description and any affected Epics.

Done when the proposed hierarchy meets the Definition of Ready or its missing input is named

### 3. Deliver

1. Through [Approval, apply and readback](../SKILL.md#approval-apply-and-readback), deliver one proposal.
   Include any Epic and Story changes from the same run.
2. Report these details:
   - The Milestone URL when created
   - Epics by Rank for each Milestone
   - Outcome checks
   - Failed actions and left-out items

Done when that procedure finishes
