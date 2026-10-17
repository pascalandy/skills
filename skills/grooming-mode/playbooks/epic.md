---
description: "CU1: verify backlog issues, assemble and refine Epics, then a Milestone when useful, before one final approval."
---

# CU1. Backlog to a ready hierarchy

```
Epic progress:
- [ ] 1. Scope
- [ ] 2. Verify and prioritize
- [ ] 3. Assemble Epics
- [ ] 4. Refine and delegate Epic reviews, then assess a Milestone
- [ ] 5. Deliver the whole proposal
```

## Process

1. **Scope.** Resolve the home repo and scoped repos. Reuse the Product Manager's
   choice for existing open Epics, or ask whether to keep or restart them:

   - Keep: place a Story in a kept Epic when its outcome covers it; otherwise
     propose a new Epic
   - Restart: record the exact Epics. Close a complete one as completed. Detach an
     incomplete one's open Stories, close it as not planned, preserve its body,
     and comment where each detached Story goes

   Default scope is each repo's backlog, open Stories whose Epic is closed,
   and open Epics with all their Stories, open or closed. For another requested
   set such as a label, use that set plus open Epics and their Stories.
   Inspect native parents so closed-Epic Stories remain visible and Sub-tasks
   follow their non-Epic parent's placement. Read affected existing Milestones
   and their members before proposing changes to their outcomes or Rank.
   Done when every candidate and affected container is read and counted
2. **Verify and prioritize.** Apply the shared verdicts against current code and
   merged changes. Flag complete open Epics and wrongly completed issues.
   Identify the files each actionable Story touches, including cross-repo paths.
   Weigh observed recurrence and cost against estimated effort; state uncertainty.
   Include recurring findings and recent PRs that leave the problem unresolved.
   Tier actionable issues under Labels and bodies. Group duplicates or issues one
   change fixes and list cleanup.
   Done when every issue has an evidenced verdict, tier or precise left-out reason
3. **Assemble Epics.** Place every actionable issue into exactly one Epic by outcome.
   A one-Story Epic is allowed only when no other Epic can take it.
   Apply label-for-issues' Dependencies rule within and between Epics, including
   source-file conflicts. Use the shared Epic order to direct conflict links.
   Ground other waits in acceptance criteria or current code prerequisites.
   A possible future rewrite does not justify a wait for work that can ship now.
   Check Parallel against the full graph. Draft native Story Rank and matching
   Epic body order, including closed Stories.
   Note candidate Milestones now. Ask about unclear product intent before it
   changes grouping or criteria; keep independent work moving.
   Done when every candidate has a proposed placement or disposition
4. **Refine and group.** Run steps 1–4 of the shared refinement loop on these
   Stories, Epics and affected existing Milestones. Reuse current evidence.
   If at least two scoped open Epics without a Milestone support one shared
   deliverable outcome, continue with the `milestone` playbook in this conversation.
   Otherwise state why no new Milestone is needed.
   Done when the hierarchy meets the Definition of Ready or its missing input is named
5. **Deliver.** Complete step 5 of the shared loop once for the whole hierarchy.
   If `milestone` handled delivery, return its result. Report URLs, membership, readiness evidence,
   cleanup, failed actions and left-out issues.
   Done when shared delivery finishes
