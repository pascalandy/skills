---
description: "CU1: before one final approval, verify backlog issues, then assemble and refine Epics and, when useful, a Milestone."
---

# CU1. Backlog to a ready hierarchy

CU1 is the route from backlog issues to ready Epics and, when useful, a Milestone.

```
Epic progress:
- [ ] 1. Scope
- [ ] 2. Verify and prioritize
- [ ] 3. Assemble Epics
- [ ] 4. Check the hierarchy, then assess a Milestone
- [ ] 5. Deliver the whole proposal
```

## Process

### 1. Scope

1. Resolve the home repo and scoped repos.
2. For existing open Epics, reuse the Product Manager's choice to keep or restart them.
   If no choice exists, ask whether to keep or restart those Epics.

If the choice is Keep, use these steps:

1. When a kept Epic's outcome covers a Story, place the Story in that Epic.
2. Otherwise, propose a new Epic.

If the choice is Restart, use these steps:

1. Record the exact Epics.
2. Close a complete Epic as completed.
3. For an incomplete Epic, detach its open Stories.
4. Close that incomplete Epic as not planned.
   Preserve its body.
5. Comment where each detached Story goes.

The default scope contains these items from each repo:

- The backlog
- Open Stories whose Epic is closed
- Open Epics and all their Stories, open or closed

For another requested set, such as a label, use that set plus open Epics and their Stories.

1. To keep Stories of closed Epics visible and to place Sub-tasks with their non-Epic parent, inspect native parents.
2. Before you propose changes to Milestone outcomes or Rank, read affected existing Milestones and their members.

Done when every candidate and affected container is read and counted

### 2. Verify and prioritize

1. Apply the shared verdicts against current code and merged changes.
2. Flag complete open Epics and wrongly completed issues.
3. Identify the files that each actionable Story touches, including cross-repo paths.
4. Weigh observed recurrence and cost against estimated effort.
   State uncertainty.
5. Include recurring findings and recent PRs that leave the problem unresolved.
6. Under Labels and bodies, assign tiers to actionable issues.
7. Group duplicates or issues that one change fixes.
8. List cleanup.

Done when every issue has a verdict from evidence, a tier, or a precise left-out reason

### 3. Assemble Epics

1. By outcome, place every actionable issue into exactly one Epic.
   A one-Story Epic is allowed only when no other Epic can take the Story.
2. Apply the Dependencies rule of label-for-issues within and between Epics, including conflicts in source files.
3. To direct conflict links, use the shared Epic order.
4. Base other waits on acceptance criteria or prerequisites in current code.
   A possible future rewrite does not justify a wait for work that can ship now.
5. Check Parallel against the full dependency graph.
6. Draft native Story Rank and matching order in the Epic body, including closed Stories.
7. Record candidate Milestones now.
8. If unclear product intent could change grouping or criteria, record that intent as unresolved input.
   Include the affected items.

Done when every candidate has a proposed placement or disposition

### 4. Check and group

1. Apply the Grouping checks and the Definition of Ready to these Stories, Epics, and affected existing Milestones.
   Reuse current evidence.
2. If at least two scoped open Epics without a Milestone share one deliverable outcome, continue with `milestone` in this conversation.
   Otherwise, state why no new Milestone is needed.

Done when the hierarchy meets the Definition of Ready or its missing input is named

### 5. Deliver

1. Through [Approval, apply and readback](../SKILL.md#approval-apply-and-readback), deliver one proposal for the whole hierarchy.
2. If `milestone` handled delivery, return its result.
3. Report these details:
   - URLs and membership
   - Readiness evidence
   - Cleanup
   - Failed actions and left-out issues

Done when that procedure finishes
