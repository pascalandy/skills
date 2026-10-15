---
name: "grooming-mode"
description: "Use only when explicitly invoked as `grooming-mode`, with an optional route after `;`. Recognize dictated spellings such as `grooming mode`. Organize GitHub Stories into Epics and Milestones or refine their readiness."
kind: "dev"
---

# Grooming mode

Organize the backlog into Story → Epic → Milestone with (Rank, Blocked by).
Write in the conversation's language; keep the glossary terms in English.

## Pick one route

Compare names with case, spaces, hyphens, and underscores ignored. Recognize
voice-to-text spellings that sound like grooming-mode, including "grooming mode".
Bare `grooming-mode` selects `epic`. An explicit name selects only that route,
with or without `;`, such as `grooming mode refine`.
An unknown name, including `sprint`, shows this table and runs nothing.
Routes never chain automatically.

| Route | Use when |
|---|---|
| [epic](playbooks/epic.md) | Default: place backlog issues into Epics with Story Rank and blocked-by links |
| [milestone](playbooks/milestone.md) | Group Epics without a Milestone and set their Rank and blocked-by links |
| [refine](playbooks/refine.md) | Reverify an Epic or Milestone and refine it until the Definition of Ready holds |

Read the selected playbook after this file. Before proposing Epic bodies in `epic`
or `refine`, read the [Epic template](references/epic-template.md). Before proposing
a Milestone description in `milestone` or `refine`, read the
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
| Milestone | A group of Epics | Milestone in the home repo | In project management, a milestone is a date |
| Rank | Work order: a Story within its Epic, an Epic within its Milestone | native sub-issue order; Milestone description's numbered list is the sole persistent Epic Rank | Priority is a separate tier |
| Blocked by | B must wait for A under label-for-issues' Dependencies rule | native Blocked by / Blocking dependency | Membership imposes no order |
| Parallel | No blocked-by path connects two elements in either direction | absence of a dependency path | A → B → C makes A and C dependent |
| Home repo | The repository the Product Manager names | home of Epics and Milestones | A Milestone exists only in its own repo |
| Grooming | Organizing the backlog | | Scrum calls it backlog refinement |
| Brigade | Executor; its Head Chef forms batches, one dish per batch with one or more PRs, and serves by Rank | | Grooming creates no batch |

Sprint means a fixed period; Wave duplicates Blocked by. Use neither as a level.

## Shared scope and evidence

Requires `gh` ([install](https://cli.github.com/)); confirm `gh --version`
and `gh auth status` before GitHub reads. Load `label-for-issues` and its
GitHub CLI reference before scoping. It owns labels, Ready, native operations,
filters and pagination. Run its Step 4 read-only before scope filters. If a label
migration is pending, propose it and stop until it is resolved.

Record the home repo and each scoped repo. Ask for the home repo if absent,
before proposing a container there. An issue stays in its repository; Epics and
Milestones live in the home repo. Before presenting a proposal, comments or
readback, scan every table, body preview, dependency, cleanup entry, readiness
gap and handoff prompt. Expand each cross-repo Story reference to `OWNER/REPO#N`,
including shortened repository aliases.
Read every scoped issue's body, comments, labels, native parent, relationships,
state and closing reason. Count every relationship against its `totalCount`
and paginate incomplete lists with label-for-issues.
Read closed issues the scoped set references for completion evidence and
closing-reason corrections, including closed Stories of `epic`'s open Epics.

For `epic` verification and `refine` reverification, read each Story's default
branch after `git fetch origin`: resolve `origin/HEAD`, then read files and commits
at that ref with `git show` and `git log`. Without a local checkout, resolve the
default branch and read its current files and commits with `gh api`.

| Verdict | Evidence required | Disposition |
|---|---|---|
| Holds | The problem or requested outcome still needs work in current files | Place |
| Fixed | A merged PR or default-branch commit solves it; cite that change | Close as completed, citing the change |
| Gone | The problem no longer occurs or never did, without a fix to cite; show why | Close as not planned, citing the proof |
| Stale fix | The problem holds, but the proposed fix quotes changed text | Place; list stale text as a gap for `refine` |

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
P1/P2/P3 tier. Each Epic takes its highest-priority Story's priority, has
`4-epic` and no type. The tier replaces established priority, including `p0`.
Limit P1 to three Stories per proposal. Determine each Story's and Epic's state with
label-for-issues' Ready rule. Missing goals or acceptance criteria alone are
readiness gaps, not grounds for leaving an issue out. Establish outcome fit from
its title, body, domain and current files, then place it provisionally with that
outcome. Preserve its unresolved goal and criteria, and list those gaps for `refine`.
Its Epic stays unready until the gaps are resolved.
Left-out issues keep their labels. A `2-type:postmortem` Story takes bug for a
`fix` title prefix, feature for `feat`, and task for every other prefix.

Only `refine` edits Story bodies, after approval. `epic` and `milestone` preserve them.

Number new Epics after the highest `Epic N` title, closed ones included.
`Epic N · <outcome>` is a stable identifier; never renumber existing Epics.
Order Epics by prerequisites, then highest Story priority, then lowest issue number.
Use that order to direct file-conflict links; use `Epic N` for new Epics until creation.

## Approval, apply and readback

Every route stops at a complete proposal before any GitHub write, including
labels, comments and relationships. Approval covers the listed issues, exact
actions, bodies the route may edit, comments and evidence, not future arrivals.
For a read-only request, return the proposal and stop.

### Proposal

Use this form for every route; mark sections with no actions as `None`.
Refer to a new Epic by `Epic N · <outcome>` until creation. Approval includes
substituting its issue number in approved bodies, links, comments and prompts.

- **Stories:** one table per Epic: Story reference, Rank, verdict, disposition,
  evidence, Today, After, P1/P2/P3 tier, final canonical labels including unchanged
  labels, and blocked-by references with reasons
- **Epics:** outcome, final canonical labels, Definition of Ready gaps and exact
  body previews using the Epic template. For `milestone`, use an Epic table by
  Rank: Epic reference, reason for its place, priority, final canonical labels,
  blocked-by references with reasons, and Definition of Ready gaps; include the
  Milestone description preview and membership
- **Cleanup:** exact moves, detachments, closures, reopenings and duplicate targets
- **Left out:** issue or action, and the precise missing proof or changed input
- **Comments:** exact text and target of every proposed comment
- **Body edits:** for `refine`, Story reference and exact before/after text per edit
- **Gaps for refine:** missing goals, acceptance criteria, evidence and decisions
  against the Definition of Ready, per Epic

After approval, follow this checklist:

```
Approved grooming:
- [ ] Reread every touched object and rerun the scope filters
- [ ] Leave changed actions and new arrivals out with their reasons
- [ ] Apply only the approved actions through label-for-issues
- [ ] Compare GitHub with the approved proposal
- [ ] Correct approved discrepancies and reread
- [ ] Report applied, failed and left-out actions
```

1. Reread bodies, labels, state, evidence and membership of every touched object.
   Put an action whose scope, evidence or membership changed on the left-out list.
   Put issues arriving after approval aside for the next grooming.
   Done when the unchanged approved actions and left-out actions are explicit
2. Apply those actions using label-for-issues' reconciliation and native commands.
   On a timeout, reread before retrying only missing operations. New actions need a
   new proposal. Done when each approved action is applied or reported as failed
3. Read back with label-for-issues' filters and paginated relations. Compare every
   field and action in Proposal with GitHub, including native/body Rank agreement.
   Each scoped issue must be placed, closed, or left out with its reason. Correct
   discrepancies within approval and reread until every applied action matches;
   report anything needing approval. Done when every write is verified or reported failed

## Definition of Ready

- Each Story has a clear goal and acceptance criteria
- An Epic is ready when each Story is ready and ranked, its blocked-by links are set, and its Done when is checkable with no open decision
- A Milestone is ready when each Epic is ready and ranked

Only `refine` runs until these conditions hold. For a new `refine` conversation,
use this prompt with the actual target, adding any remaining gaps or refusal:

```text
grooming-mode ; refine
Home repo: OWNER/REPO
Target: <Epic issue URL or Milestone URL>
Reverify every Story, propose refinements and readiness labels, and apply after approval.
Continue until the Definition of Ready holds.
```
