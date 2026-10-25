---
name: "grooming-mode"
description: "Use only when explicitly invoked as `grooming-mode`, with an optional route after `;`. Recognize dictated spellings such as `grooming mode`. Assemble and refine GitHub Stories, Epics and Milestones until ready."
kind: "dev"
---

# Grooming mode

Assemble and refine Story → Epic → Milestone with Rank and Blocked by.
Grooming writes the plan only; Brigade executes a ready target when execution
is requested.
Write in the conversation's language; keep the glossary terms in English.

## Pick the starting point

Compare names with case, spaces, hyphens, and underscores ignored. Recognize
voice-to-text spellings that sound like grooming-mode, including "grooming mode".
Bare `grooming-mode` selects `epic`. An explicit name selects the starting point,
with or without `;`, such as `grooming mode refine`.
An unknown name, including `sprint`, shows this table and runs nothing.
`epic` continues into `milestone` when its grouping condition holds.

| Route | Use when |
|---|---|
| [epic](playbooks/epic.md) | Default: assemble and refine Epics, then a Milestone when useful |
| [milestone](playbooks/milestone.md) | Assemble and refine a Milestone from eligible Epics |
| [refine](playbooks/refine.md) | Refine an existing Epic or Milestone, including its Stories |

Read the selected playbook after this file. Before drafting an Epic body,
read the [Epic template](references/epic-template.md). Before drafting
a Milestone description, read the
[Milestone template](references/milestone-template.md).
Use [routing cases](references/routing-cases.md) when changing routing.

## Under a workflow

This skill defines the WORK and its checks. The caller's workflow decides who
scouts, drafts, asks and reviews, and when.

- The WORK is the complete proposal; the plan is its candidate hierarchy
- Every agent that drafts or reviews the WORK loads this skill
- The WORK is done when each target meets the Definition of Ready or names its
  missing input
- Ask the route's scope questions with the goal, before reading the scope
- Every run delivers its proposal instead of handing unfinished refinement to a
  new session; GitHub writes wait for approval

## Glossary

| Term | Definition | On GitHub | Trap |
|---|---|---|---|
| Issue | Any issue; it stays in the backlog until groomed | issue | |
| Backlog | Open issues outside any Epic, excluding Sub-tasks | `no:parent-issue -label:4-epic` | Inspect native parents |
| Story | An issue grooming placed in an Epic, ranked against its other Stories | native sub-issue of an Epic | A level, unlike Jira's type; `2-type:*` keeps its nature |
| Sub-task | A sub-issue of a non-Epic issue; it follows its parent | native sub-issue | It is not a Story |
| Epic | Stories aiming at one outcome, possibly across repositories | `4-epic` issue in the home repo | |
| Milestone | Epics serving one shared, checkable outcome | Milestone in the home repo | A shared file or the number of Epics alone does not justify one |
| Rank | Work order: a Story within its Epic, an Epic within its Milestone | native sub-issue order; Milestone description's numbered list is the sole persistent Epic Rank | Priority is a separate tier |
| Blocked by | B must wait for A under label-for-issues' Dependencies rule | native Blocked by / Blocking dependency | Membership imposes no order |
| Parallel | No blocked-by path connects two elements in either direction | absence of a dependency path | A → B → C makes A and C dependent |
| Home repo | The repository the Product Manager names | home of Epics and Milestones | A Milestone exists only in its own repo |
| Grooming | Assembling and refining the backlog until ready | | Scrum calls it backlog refinement |
| Brigade | Executor; its Head Chef forms batches, one dish per batch with one or more PRs, and serves by Rank | | Grooming creates no batch |

Sprint means a fixed period; Wave duplicates Blocked by. Use neither as a level.

## Shared scope and evidence

Requires `gh` ([install](https://cli.github.com/)); confirm `gh --version`
and `gh auth status` before GitHub reads.
Load `label-for-issues` and its
GitHub CLI reference before scoping. It owns labels, Ready, native operations,
filters and pagination. Run its Step 4 before scope filters. Its `4-epic`
migration is the only write allowed there, even in a read-only grooming, since
the Epic filters need that label. If another label migration is pending, propose
it and stop until it is resolved.

Record the home repo and scoped repos; ask if the home repo is absent.
Issues stay in their repositories; containers live in the home repo.
Use `OWNER/REPO#N` for every cross-repo Story reference, including bodies,
tables, comments, dependencies and handoffs.
Read every scoped issue's body, comments, labels, native parent, relationships,
state and closing reason. Count every relationship against its `totalCount`
and paginate incomplete lists with label-for-issues.
Follow linked reports, reproductions and Product Manager decisions that bear on
the outcome. Check container summaries against these sources.
Read closed issues the scoped set references for completion evidence and
closing-reason corrections, including closed Stories of `epic`'s open Epics.

For every route, read each Story's default branch after `git fetch origin`:
resolve `origin/HEAD`, then read files and commits
at that ref with `git show` and `git log`. Without a local checkout, resolve the
default branch and read its current files and commits with `gh api`.
Record the commit and issue evidence used. Reuse it within the run while its
inputs hold; reverify affected items when code, scope or decisions change.

| Verdict | Evidence required | Disposition |
|---|---|---|
| Holds | The problem or requested outcome still needs work in current files | Place |
| Fixed | A merged PR or default-branch commit solves it; cite that change | Close as completed, citing the change |
| Gone | The problem no longer occurs or never did, without a fix to cite; show why | Close as not planned, citing the proof |
| Stale fix | The problem holds, but the proposed fix quotes changed text | Place; refine the stale text against current evidence |

Put an issue on the left-out list when its outcome fit or required verification
cannot be established, naming the precise missing proof. Assess readiness gaps
under Labels and bodies separately from verification.
For duplicates, propose `gh issue close --duplicate-of <covering issue>`.

An Epic is complete only when its outcome holds and every Story has a documented disposition.
For a closed-completed issue, distinguish code work from non-code work:

- Landed work or a comment proving the non-code acceptance criterion keeps completed
- Required work never landed and the problem Holds or Stale fix: propose reopening
  and placement
- Gone without landed work: propose reopening, then closing as not planned, with proof

## Labels and bodies

An approved grooming sets each Story's `3-pty:p1`, `p2` or `p3` from its
P1/P2/P3 tier. Each Epic takes its highest-priority Story's priority.
The tier replaces established priority, including `p0`.
Limit P1 to three Stories per proposal. Propose a Ready label only when this
skill's Definition of Ready holds; use label-for-issues to select the state.
Place issues with missing criteria provisionally when their sources establish
outcome fit, then resolve their gaps or name the missing input in the proposal.
Left-out issues keep their labels. A `2-type:postmortem` Story takes bug for a
`fix` title prefix, feature for `feat`, and task for every other prefix.

Every route may propose Story body edits. Preserve supported content and explicit
product decisions; draft only the changes needed to resolve a gap.

Number new Epics after the highest `Epic N` title, closed ones included.
`Epic N · <outcome>` is a stable identifier; never renumber existing Epics.
Order Epics by prerequisites, then highest Story priority, then lowest issue number.
Use that order to direct file-conflict links; use `Epic N` for new Epics until creation.

## Grouping checks

Test each parent with one question: if every child were completed, would its
outcome hold? Then look for missing integration work, overlapping scope,
contradictory criteria and dependencies across Epics, and check the full
dependency graph for cycles and unjustified waits. Propose a missing Story
explicitly instead of hiding its work in a container summary.

After a product answer or correction, update the affected Story bodies,
membership, parent outcomes, Rank, dependencies and priorities, then recheck
only what changed.

## Definition of Ready

Readiness means the work is specified and checked; completion requires the outcome
evidence after delivery. A check is a named command, observable behavior or
artifact. A scheduled prerequisite can remain open if its effect on execution
order is explicit.

- **Story:** satisfies label-for-issues' Ready rule, with its goal, acceptance
  rules, examples that distinguish success from failure and a check for them in
  its own body; the proposal cites the source or Product Manager decision behind each
- **Epic:** open Stories are ready; every closed Story has a documented disposition;
  Story Rank and justified blockers agree with its body; its outcome, boundaries
  and checkable Done when are covered by those Stories, with no unresolved decision
- **Milestone:** each Epic is ready or proven complete; Epic Rank and justified
  blockers agree with its description; its shared outcome, own checkable Done when
  and boundaries are covered by those Epics, with no unresolved decision

## Approval, apply and readback

Apart from the `4-epic` migration before scope filters, obtain one final approval
of the complete refined proposal before GitHub writes, including labels, comments
and relationships. Earlier product answers settle decisions, not permission to
write. Approval covers the listed issues, exact actions, bodies, comments and
evidence, not future arrivals. Reuse explicit approval covering those actions.
For a read-only request, return the proposal and stop.

### Proposal

Use this form; mark empty sections `None`. Use `Epic N · <outcome>` and stable
Story draft names until creation. Approval includes substituting their issue numbers.

- **Stories:** one table per Epic: Story reference, Rank, verdict, disposition,
  evidence, Today, After, P1/P2/P3 tier, final canonical labels including unchanged
  labels, and blocked-by references with reasons
- **Epics:** outcome, final canonical labels, blocked-by references with reasons,
  Definition of Ready gaps and exact body previews using the Epic template.
  Whenever a proposal creates or changes a Milestone, show these Epics in a table
  by Rank with their references, reasons for their places and priorities; include
  the Milestone description preview and membership
- **Cleanup:** exact moves, detachments, closures, reopenings and duplicate targets
- **Left out:** issue or action, and the precise missing proof or changed input
- **Comments:** exact text and target of every proposed comment
- **Body edits and new Stories:** Story reference and exact before/after text per
  edit; title, body, labels and placement of each proposed new Story
- **Readiness:** outcome checks; for each proposed Ready label, the review record
  label-for-issues' Ready rule asks for; unresolved input and affected items

After approval:

1. Rerun scope filters and reread each touched object's body, labels, state,
   evidence and membership.
   Put an action whose scope, evidence or membership changed on the left-out list.
   Leave out dependent actions too, including parent Ready labels and outcomes
   that rely on the changed item. Return that scope to refinement.
   Leave issues arriving after approval out for the next grooming, with the reason
   that they arrived after approval.
   Done when the unchanged approved actions and left-out actions are explicit
2. Apply those actions using label-for-issues' reconciliation and native commands.
   Create approved Stories and Epics, with Epics in the shared order, then resolve
   their draft references. Create or update approved Milestones and bodies.
   Reconcile membership, native Story Rank, dependencies, labels and cleanup.
   Attach a Milestone only to its approved home-repo Epics. Preserve retired and
   already closed Epic bodies. Without a Milestone, creation order is the initial
   Epic Rank.
   Suspend actions dependent on a failed write. Apply Ready labels only after
   supporting body and relationship writes pass readback; otherwise report the
   affected hierarchy as unready and any unsupported existing Ready label.
   On a timeout, reread before retrying only missing operations. New actions need a
   new proposal. Done when each approved action is applied or reported as failed
3. Read back with label-for-issues' filters and paginated relations. Compare every
   field and action in Proposal with GitHub, including native/body Rank agreement.
   Each scoped issue must be placed, closed, or left out with its reason. Correct
   discrepancies within approval and reread until every applied action matches;
   report anything needing approval. Done when every write is verified or reported failed
