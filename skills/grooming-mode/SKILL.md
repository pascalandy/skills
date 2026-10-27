---
name: "grooming-mode"
description: "Use only when explicitly invoked as `grooming-mode`, with an optional route after `;`. Recognize dictated spellings such as `grooming mode`. Assemble and refine GitHub Stories, Epics and Milestones until ready."
kind: "dev"
---

# Grooming mode

Prepare a plan for GitHub work. The Glossary defines the levels and terms in this plan.

## Glossary

| Term | Definition | On GitHub | Trap |
|---|---|---|---|
| Issue | Any issue. An issue stays in the backlog until groomed. | issue | |
| Backlog | Open issues outside any Epic, excluding Sub-tasks | `no:parent-issue -label:4-epic` | Inspect native parents. |
| Story | An issue that grooming placed in an Epic and ranked against the other Stories in that Epic | native sub-issue of an Epic | Story is a level, unlike Jira's type. The `2-type:*` label keeps the issue's nature. |
| Sub-task | A sub-issue of a non-Epic issue. A Sub-task follows its parent. | native sub-issue | A Sub-task is not a Story. |
| Epic | Stories that aim at one outcome, possibly across repositories | `4-epic` issue in the home repo | |
| Milestone | Epics that serve one shared outcome that a check can verify | Milestone in the home repo | A shared file alone does not justify a Milestone. The number of Epics alone does not justify a Milestone. |
| Rank | Work order for a Story within its Epic, or an Epic within its Milestone | native sub-issue order for Stories. The numbered list in the Milestone description is the only persistent Rank for Epics. | Priority is a separate tier. |
| Blocked by | B must wait for A under the Dependencies rule of label-for-issues, the skill for GitHub labels and relationships. | native Blocked by or Blocking dependency | Membership imposes no order. |
| Parallel | No blocked-by path connects two elements in either direction | absence of a dependency path | If A blocks B and B blocks C, A and C are dependent. |
| Home repo | The repository that the Product Manager names | home of Epics and Milestones | A Milestone exists only in its own repo. |
| Grooming | Assembly and refinement of the backlog until ready | | Scrum calls Grooming backlog refinement. |
| Brigade | The skill that executes ready work. Its Head Chef is the Brigade thread that the user talks to. Batches are parts of the plan. The Head Chef forms batches, one dish per batch with one or more PRs, and serves by Rank. | | Grooming creates no batch. |

Sprint means a fixed period. Wave duplicates Blocked by. Use neither as a level.

Assemble and refine Stories into Epics. Assemble and refine eligible Epics into Milestones.
Use Rank and Blocked by to specify work order and dependencies.
Grooming writes the plan only. When execution is requested, Brigade executes a ready target.
Talk with the user in the conversation's language. Keep explanations in the Proposal in the conversation's language.
Keep the glossary terms in English.

Before you draft text for GitHub, load `asd-ste100`, the skill for Simplified Technical English, or STE.
With its Write branch, draft each text for GitHub in English.
This rule covers titles, Story and Epic bodies, Milestone descriptions, and comments.
Keep required title forms, such as `Epic N · <outcome>` and the type prefix of a Story title.
If you edit an existing issue body in another language, rewrite the full body in English.
Preserve every fact and decision of that body. Use only English in the rewritten body.

## Pick the starting point

1. When you compare names, ignore case, spaces, hyphens, and underscores.
2. Recognize voice-to-text spellings that sound like grooming-mode, including "grooming mode".
3. Select the starting point from the request.
   Bare `grooming-mode` selects `epic`.
   An explicit name selects the starting point, with or without `;`, such as `grooming mode refine`.
   When its grouping condition holds, `epic` continues into `milestone`.
4. If the name is unknown, including `sprint`, use these steps:
   1. Show this table.
   2. Run nothing.

| Route | Use when |
|---|---|
| [epic](playbooks/epic.md) | Default. Assemble and refine Epics, then a Milestone when useful. |
| [milestone](playbooks/milestone.md) | Assemble and refine a Milestone from eligible Epics. |
| [refine](playbooks/refine.md) | Refine an existing Epic or Milestone, including its Stories. |

5. After this file, read the selected playbook.
6. Before you draft an Epic body, read the [Epic template](references/epic-template.md).
7. Before you draft a Milestone description, read the [Milestone template](references/milestone-template.md).

When you change routing, use [routing cases](references/routing-cases.md).

## Under a workflow

This skill defines the WORK and its checks. The WORK is the complete proposal.
The plan is the candidate hierarchy in that proposal.
The caller's workflow decides who scouts, drafts, asks, and reviews, and when.
The Definition of Ready below states when work is ready.
The WORK is done when each target meets the Definition of Ready or names its missing input.
Every agent that drafts or reviews the WORK loads this skill.

Under the caller's workflow, use these rules:

- Before you read the scope, ask the route's scope questions with the goal
- In every run, deliver the proposal instead of transferring unfinished refinement to a new session
- Before GitHub writes, wait for approval

## Shared scope and evidence

Use `gh`, the GitHub CLI. The [installation instructions](https://cli.github.com/) explain how to install `gh`.

The skill label-for-issues owns labels, Ready, native operations, filters, and pagination.
Ready is the label state that identifies work ready for execution.
Step 4 of label-for-issues has a `4-epic` migration.
That migration is the only write allowed before scope filters, even in read-only grooming.
This exception exists because the Epic filters need that label.

Issues stay in their repositories. Epics and Milestones, the containers for this plan, live in the home repo.

1. Before GitHub reads, confirm `gh --version` and `gh auth status`.
2. Before you scope the work, load `label-for-issues` and its GitHub CLI reference.
3. Before scope filters, run Step 4 of label-for-issues.
4. If another label migration is pending, use these steps:
   1. Propose that migration.
   2. Stop until that migration is resolved.
5. Record the home repo and scoped repos.
6. If the home repo is absent, ask for the home repo.
7. For every cross-repo Story reference, use `OWNER/REPO#N`, also in bodies, tables, comments, dependencies, and handoffs.
8. Read these fields for every scoped issue:
   - Body and comments
   - Labels and native parent
   - Relationships
   - State and closing reason
9. Count every relationship against its `totalCount`.
10. For incomplete lists, paginate with label-for-issues.
11. Follow linked reports, reproductions, and Product Manager decisions that affect the outcome.
12. Check container summaries against those sources.
13. For completion evidence and corrections to closing reasons, read closed issues that the scoped set references.
    For `epic`, include closed Stories of its open Epics.

For every route, verify each Story against its default branch.
If a local checkout exists, use these steps:

1. Run `git fetch origin`.
2. Resolve `origin/HEAD`.
3. At that ref, read files and commits with `git show` and `git log`.

Without a local checkout, use these steps:

1. With `gh api`, resolve the default branch.
2. With `gh api`, read its current files and commits.

For either source, use these steps:

1. Record the commit and issue evidence used.
2. While its inputs stay unchanged, reuse that evidence within the run.
3. When code, scope, or decisions change, reverify the affected items.

Assign one of these verdicts from the evidence:

| Verdict | Evidence required | Disposition |
|---|---|---|
| Holds | The problem or requested outcome still needs work in current files | Place the issue. |
| Fixed | A merged PR or a default-branch commit solves the issue. Cite that change. | Close the issue as completed. Cite the change. |
| Gone | The problem no longer occurs or never did, without a fix to cite. The evidence shows why. | Close the issue as not planned. Cite the proof. |
| Stale fix | The problem still needs work, but the proposed fix quotes text that changed | Place the issue. Refine the stale text against current evidence. |

If you cannot establish outcome fit or required verification, put the issue on the left-out list.
Name the precise missing proof. Assess readiness gaps under Labels and bodies separately from verification.
For duplicates, propose `gh issue close --duplicate-of <covering issue>`.

An Epic is complete only when its outcome holds and every Story has a documented disposition.
For a closed-completed issue, distinguish code work from non-code work:

- If work landed, keep the completed state
- If a comment proves the non-code acceptance criterion, keep the completed state
- If required work never landed and the verdict is Holds or Stale fix, propose reopening and placement
- If the verdict is Gone without landed work, propose reopening, then closing as not planned, with proof

## Labels and bodies

An approved grooming sets each Story's `3-pty:p1`, `p2`, or `p3` label from its P1, P2, or P3 tier.
Each Epic takes the priority of its highest-priority Story.
The tier replaces established priority, including `p0`.
Left-out issues keep their labels.

Use these rules for labels:

- Limit P1 to three Stories per proposal
- Only when this skill's Definition of Ready holds, propose a Ready label
- To select the Ready state, use label-for-issues

For issues with missing criteria, use these steps:

1. If their sources establish outcome fit, place the issues provisionally.
2. For provisionally placed issues, resolve their gaps or name the missing input in the proposal.

A `2-type:postmortem` Story takes its type from the title prefix:

- `fix` gives bug
- `feat` gives feature
- Every other prefix gives task

In every route, you may propose Story body edits.
Preserve supported content and explicit product decisions. Draft only the changes that are necessary to resolve a gap.

1. Number new Epics after the highest `Epic N` title, including closed Epics.
   `Epic N · <outcome>` is a stable identifier. Never renumber existing Epics.
2. Order Epics by prerequisites, then highest Story priority, then lowest issue number.
3. To direct file-conflict links, use that order.
4. Until creation, use `Epic N` for new Epics.

## Grouping checks

1. Test each parent with this question: if every child were completed, would the parent's outcome hold?
2. Then check for these conditions:
   - Missing integration work
   - Overlapping scope
   - Contradictory criteria
   - Dependencies across Epics
3. Check the full dependency graph for cycles and unjustified waits.
4. If a Story is missing, propose that Story explicitly.
   Do not hide the Story's work in a container summary.

After a product answer or correction, use these steps:

1. Update the affected items:
   - Story bodies and membership
   - Parent outcomes
   - Rank and dependencies
   - Priorities
2. Then recheck only what changed.

## Definition of Ready

Readiness means that the work is specified and checked. Completion requires outcome evidence after delivery.
A check is a named command, observable behavior, or artifact.
A scheduled prerequisite can remain open if its effect on execution order is explicit.

A Story is ready when all these conditions hold:

- The Story satisfies the Ready rule of label-for-issues
- The Story's own body contains its goal, acceptance rules, examples that distinguish success from failure, and a check for them
- For each element, the proposal cites its source or the Product Manager decision

An Epic is ready when all these conditions hold:

- Open Stories are ready
- Every closed Story has a documented disposition
- Story Rank and justified blockers agree with the Epic body
- The Stories cover the Epic's outcome, boundaries, and checkable Done when
- No decision remains unresolved

A Milestone is ready when all these conditions hold:

- Each Epic is ready or proven complete
- Epic Rank and justified blockers agree with the Milestone description
- The Epics cover the Milestone's shared outcome, its own checkable Done when, and its boundaries
- No decision remains unresolved

## Approval, apply and readback

Before GitHub writes, obtain one final approval of the complete refined proposal.
The `4-epic` migration before scope filters is the only exception.
GitHub writes include labels, comments, and relationships.
Earlier product answers settle decisions. Those answers do not give permission to write.
Approval covers the listed issues, exact actions, bodies, comments, and evidence. Approval does not cover future arrivals.
If explicit approval covers those actions, reuse that approval.
For a read-only request, return the proposal and stop.

### Proposal

Use this form. Mark empty sections `None`.
Until creation, use `Epic N · <outcome>` and stable draft names for Stories.
Approval includes substitution of their issue numbers.

- **Stories:** Make one table per Epic. Include these fields:
  - Story reference and Rank
  - Verdict, disposition, and evidence
  - Today and After
  - P1, P2, or P3 tier
  - Final canonical labels, including unchanged labels
  - Blocked-by references and their reasons
- **Epics:** Include these details:
  - Outcome and final canonical labels
  - Blocked-by references and their reasons
  - Definition of Ready gaps and exact body previews
  Use the Epic template for the body previews.
  Whenever the proposal creates or changes a Milestone, include these details:
  - A table of these Epics by Rank, with their references, reasons for their places, and priorities
  - The Milestone description preview and membership
- **Cleanup:** List exact moves, detachments, closures, reopenings, and duplicate targets
- **Left out:** Name the issue or action and the precise missing proof or changed input
- **Comments:** Give the exact text and target of every proposed comment
- **Body edits and new Stories:** Include these details:
  - Story reference and exact text before and after each edit
  - Title, body, labels, and placement of each proposed new Story
- **Readiness:** Include these details:
  - Outcome checks
  - For each proposed Ready label, the review record that the Ready rule of label-for-issues requires
  - Unresolved input and affected items
  - For each text for GitHub, its asd-ste100 result, with these parts:
    - The `STE: Pass:` line
    - Each kept finding and its reason
  - The asd-ste100 scope line, once for all results

Keep asd-ste100 results in Readiness only. The text on GitHub does not include these results.

After approval, follow these three phases.

### 1. Recheck the approved actions

1. Rerun scope filters.
2. Reread each touched object's body, labels, state, evidence, and membership.
   Before any phase 2 GitHub write, record the preserved values of every issue the
   [readback format](references/readback.md) includes.
3. If an action's scope, evidence, or membership changed, put that action on the left-out list.
4. Put dependent actions on the left-out list too.
   These actions include parent Ready labels and outcomes that rely on the changed item.
5. Return that scope to refinement.
6. Put issues that arrive after approval on the left-out list for the next grooming with the reason "arrived after approval".

Done when the unchanged approved actions and left-out actions are explicit

### 2. Apply the approved actions

Requires `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/));
confirm `uv --version` before writing the plan for readback.

1. Apply those actions with the reconciliation and native commands of label-for-issues.
   New actions need a new proposal.
2. Create approved Stories and Epics.
   Epics follow the shared order.
   Without a Milestone, creation order is the initial Epic Rank.
3. Then resolve the draft references of those Stories and Epics.
4. Create or update approved Milestones and bodies.
   Preserve retired and already closed Epic bodies.
5. Reconcile membership, native Story Rank, dependencies, labels, and cleanup.
6. Attach a Milestone only to its approved home-repo Epics.
7. If a write fails, suspend actions that depend on that write.
8. Only after supporting body and relationship writes pass a direct reread, apply Ready labels.
   Otherwise, report the affected hierarchy as unready and report any unsupported existing Ready label.
9. On a timeout, reread before a retry.
10. After that reread, retry only missing operations.
11. Write the plan file in this run's own working folder as the
    [readback format](references/readback.md) describes, and record its absolute path.

Done when each approved action is applied or reported as failed, and the plan file
exists unless no row could be resolved

### 3. Verify the writes

1. If the plan file exists, from this skill's folder run
   `uv run scripts/readback.py <absolute-plan-path>` and read its verdict.
   Otherwise, report the script's comparisons as not run.
   For its input and failure format, use the
   [readback format](references/readback.md).
2. With the filters and paginated relations of label-for-issues, compare the
   remaining fields and actions in Proposal with GitHub.
   Each scoped issue must be placed, closed, or left out with its reason.
3. Within approval, correct discrepancies.
   Phase 2 step 8 still governs Ready labels.
4. Resolve any newly created issue numbers as the readback format describes,
   rerun the script once the plan file exists, and reread other corrected actions.
5. Repeat steps 3 and 4 until every applied action matches or needs approval.
6. Report each action that needs approval.
   Report affected hierarchies as unready and identify unsupported Ready labels.

Done when the script confirms the issue fields and every other write is verified,
or each failed or unperformed comparison or read is explicitly reported
