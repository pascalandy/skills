---
name: "grooming-mode"
description: "Use only when explicitly invoked as `grooming-mode`, with an optional route after `;`. Recognize dictated spellings such as `grooming mode`. Assemble and refine GitHub Stories, Epics and Milestones until ready."
kind: "dev"
---

# Grooming mode

Assemble and refine Story → Epic → Milestone with Rank and Blocked by.
Own the refinement at every level in the same conversation.
Write in the conversation's language; keep the glossary terms in English.

## Pick the starting point

Compare names with case, spaces, hyphens, and underscores ignored. Recognize
voice-to-text spellings that sound like grooming-mode, including "grooming mode".
Bare `grooming-mode` selects `epic`. An explicit name selects the starting point,
with or without `;`, such as `grooming mode refine`.
An unknown name, including `sprint`, shows this table and runs nothing.
Every route uses the shared refinement loop and one final approval for the
whole proposal. `epic` continues into `milestone` when its grouping condition holds.

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
and `gh auth status` before GitHub reads. Confirm delegation is available for
the review checkpoints; report a missing capability before refining.
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
outcome fit, then resolve their gaps through the shared loop.
Left-out issues keep their labels. A `2-type:postmortem` Story takes bug for a
`fix` title prefix, feature for `feat`, and task for every other prefix.

Every route may propose Story body edits. Preserve supported content and explicit
product decisions; draft only the changes needed to resolve a gap.

Number new Epics after the highest `Epic N` title, closed ones included.
`Epic N · <outcome>` is a stable identifier; never renumber existing Epics.
Order Epics by prerequisites, then highest Story priority, then lowest issue number.
Use that order to direct file-conflict links; use `Epic N` for new Epics until creation.

## Refine the hierarchy

Run this loop on the proposed hierarchy before seeking approval to write it.

```
Refinement progress:
- [ ] 1. Draft from evidence
- [ ] 2. Challenge the grouping
- [ ] 3. Resolve and propagate
- [ ] 4. Delegate Epic reviews, then Milestone reviews
- [ ] 5. Deliver the whole proposal
```

1. **Draft from evidence.** For each open Story, establish the goal, acceptance
   rules and concrete examples that distinguish success from failure. Cite their
   source or the Product Manager's decision. Refine each Epic's outcome, boundaries
   and Done when. For a Milestone, define its shared outcome and its own Done when.
   Name the command, observable behavior or artifact that will check each outcome.
   Done when every level has a proposed check or a precise unresolved input
2. **Challenge the grouping.** If every child were completed, would its parent's
   outcome hold? Check missing integration work, overlapping scope, contradictory
   criteria and dependencies across Epics. Propose missing Stories explicitly;
   do not hide their work in a container summary. Check the full dependency graph
   for cycles and unjustified waits.
   Done when each finding has evidence and a disposition
3. **Resolve and propagate.** Investigate facts, delegating bounded scouting when
   useful. Ask the Product
   Manager as soon as a missing decision could change scope, acceptance, grouping
   or delivery order. Give the recommendation, alternatives and affected items.
   Decide routine, reversible implementation details yourself. A missing answer
   stays open; continue independent work without marking the affected hierarchy
   ready. After an answer or correction, update affected Story bodies, membership,
   parent outcomes, Rank, dependencies and priorities. Recheck only what changed.
   Done when the content is reviewable or the required input is named
4. **Delegate the reviews.** Delegate one review per refined Epic with all its
   Stories once no pending decision can change its membership or criteria.
   Review independent Epics meanwhile. Resolve findings before finalizing their
   Milestone grouping. Then delegate a separate review of each refined Milestone's
   joint outcome, coverage, boundaries, Rank and cross-Epic dependencies.
   Give each reviewer the draft, original issue evidence, current code references,
   relevant neighboring scope and the Definition of Ready. Request a verdict with
   evidenced blockers, separating optional suggestions.

   In T3 Code, load `t3-runtime`, discover available models and use `delegate_task`
   for these child tasks. Prefer another model family when available.
   Keep each task ID and read its completed result. In
   another host, use its native delegation. If delegation is unavailable, report
   that missing prerequisite and keep the affected target unready.

   Check findings against sources; fix valid blockers and justify rejections.
   Verify accepted corrections against their requested results; that review stays
   current for the corrected scope. Other changes to membership, outcomes, criteria,
   Rank or dependencies invalidate reviews covering those inputs. Re-review only
   stale scopes, including affected parents, with prior findings and responses.
   Keep product decisions with the Product Manager and GitHub writes with the owner.
   Done when required reviews are current and supported blockers resolved, or
   the missing capability or product input is reported with the target unready
5. **Deliver.** Present the complete hierarchy and all proposed writes together.
   Apply the shared approval and readback procedure once for that proposal.
   Report readiness separately from application failures and missing inputs.
   Hand a ready target and its evidence to Brigade only when execution is requested.
   A refusal returns to this loop on the same target; resolve its supported gaps
   without asking the Product Manager to launch another refinement session.
   If the skill caused the gap, propose a retrospective issue with the failing
   instruction and evidence; create it only when issue creation is authorized.
   Done when the result is verified, delivered read-only, or blocked on named input

## Definition of Ready

Readiness means the work is specified and checked; completion requires the outcome
evidence after delivery. A scheduled prerequisite can remain open if its effect
on execution order is explicit. An Epic and its Stories need their current delegated
review; a Milestone also needs its separate review.

- **Story:** satisfies label-for-issues' Ready rule, with acceptance examples and
  a named way to check them in its own body
- **Epic:** open Stories are ready; every closed Story has a documented disposition;
  Story Rank and justified blockers agree with its body; its boundaries and
  checkable Done when are covered by those Stories, with no unresolved decision
- **Milestone:** each Epic is ready or proven complete; Epic Rank and justified
  blockers agree with its description; its own checkable Done when and boundaries
  are covered by those Epics, with no unresolved decision

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
- **Readiness:** outcome checks; each review's task ID, model, date, scope, verdict
  and findings' dispositions; unresolved input and affected items

After approval:

1. Rerun scope filters and reread each touched object's body, labels, state,
   evidence and membership.
   Put an action whose scope, evidence or membership changed on the left-out list.
   Leave out dependent actions too, including parent Ready labels and outcomes
   that rely on the changed item. Return that scope to refinement and review.
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
