---
name: "grooming-mode"
description: "Use only when explicitly invoked as `grooming-mode`, with an optional route after `;`. Recognize dictated spellings such as `grooming mode`. Organize GitHub Stories into Epics and Milestones or refine their readiness."
kind: "dev"
---

# Grooming mode

Organize the backlog into Story → Epic → Milestone. The dependency graph is
(Rank, Blocked by). Brigade executes the plan and forms its own batches.
Write in the conversation's language; keep the glossary terms in English.

## Pick one route

Compare names with case, spaces, hyphens, and underscores ignored. Recognize
voice-to-text spellings that sound like grooming-mode, including "grooming mode".
Bare `grooming-mode` selects `epic`. An explicit name selects only that route.
An unknown name, including `sprint`, shows this table and runs nothing.
Routes never chain automatically.

| Route | Use when |
|---|---|
| [epic](playbooks/epic.md) | CU1, default: place backlog issues into Epics with Story Rank and blocked-by links |
| [milestone](playbooks/milestone.md) | CU2: group Epics without a Milestone and set their Rank and blocked-by links |
| [refine](playbooks/refine.md) | CU3: reverify an Epic or Milestone and refine it until grooming Done when holds |

Read the selected playbook after this file. Before proposing Epic bodies in CU1
or CU3, read the [Epic template](references/epic-template.md). Before proposing
a Milestone description in CU2 or CU3, read the
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
| Rank | Work order: a Story within its Epic, an Epic within its Milestone | native sub-issue order; numbered list in Milestone description | Priority is a separate tier |
| Blocked by | B must wait for A, for a logical prerequisite or a conflict in the same files | native Blocked by / Blocking dependency | Membership imposes no order |
| Parallel | Two elements with no blocked-by link between them | absence of a dependency | |
| Home repo | The repository the Product Manager names | home of Epics and Milestones | A Milestone exists only in its own repo |
| Grooming | Organizing the backlog | | Scrum calls it backlog refinement |
| Brigade | Executor; its Head Chef forms batches, one dish per batch with one or more PRs, and serves by Rank | | Grooming creates no batch |

Sprint means a fixed period; Wave duplicates Blocked by. Use neither as a level.

## Shared scope and evidence

Requires `gh` ([install](https://cli.github.com/)); confirm `gh --version`
and `gh auth status` before GitHub reads. Load `label-for-issues` and its
GitHub CLI reference before scoping. It owns labels, Ready, native operations,
filters and pagination.

Record the home repo and each scoped repo. Ask for the home repo if absent,
before proposing a container there. An issue stays in its repository; Epics and
Milestones live in the home repo. Cite another repo's Story as `OWNER/REPO#N`
throughout proposals, dependencies, cleanup, comments and readback.
Read every scoped issue's body, comments, labels, native parent, relationships,
state and closing reason. Count every relationship against its `totalCount`
and paginate incomplete lists with label-for-issues.

When CU1 regroups existing open Epics, obtain the Product Manager's choice:

- Keep: place a Story in a kept Epic when that outcome covers it, otherwise
  propose a new Epic
- Restart: record the exact Epics concerned. Close a complete one as completed.
  Detach an incomplete one's open Stories, close it as not planned, keep its
  body intact, and comment where every detached Story goes

Reuse an explicit choice already given. A Sub-task stays attached to its
non-Epic parent and follows that parent's placement; never promote it separately.
An Epic's closure does not remove its open Stories from scope.

For CU1 verification and CU3 reverification, use the current default branch and
merged PRs, including each Story's own repo. Fetch a local checkout when available,
or read current files and commits with `gh api`. Give each issue a verdict:

| Verdict | Evidence required |
|---|---|
| Holds | The problem or requested outcome still needs work in current files |
| Fixed | A merged PR or default-branch commit solves it; cite that change |
| Gone | The problem no longer occurs or never did, without a fix to cite; show why |
| Stale fix | The problem holds, but the proposed fix quotes changed text |

Insufficient evidence goes on the left-out list with the precise missing proof.
Missing goal or acceptance criteria is a readiness gap: when evidence supports
the outcome fit, place the Story provisionally and keep it unready.
For duplicates, name the covering issue and show the proposed closure comment.

An Epic is complete only when its outcome holds and every Story has a documented
disposition. Closed Stories or a merged PR alone do not prove completion.
For a closed-completed issue, distinguish code work from non-code work:

- Landed work or a comment proving the non-code acceptance criterion keeps completed
- Required work never landed and the problem Holds or Stale fix: propose reopening
  and placement
- Gone without landed work: propose reopening, then closing as not planned, with proof

Show these corrections and all closure/reopening comments in the proposal.
Close Fixed as completed; close Gone as not planned; name the covering issue
for a duplicate. Issue closure reasons and comments follow the host's supported
operations; a duplicate's comment supplies its covering reference.

## Labels and bodies

An approved grooming sets each Story's `3-pty:p1`, `p2` or `p3` from its
P1/P2/P3 tier. Each Epic takes its highest-priority Story's priority, has
`4-epic` and no type. Determine each Story's and Epic's state with
label-for-issues' Ready rule. An unclear Story gets or keeps `1-needs-triage`;
its Epic also stays unready until its readiness gaps are resolved.
Left-out issues keep their labels. A `2-type:postmortem` Story takes bug for a
`fix` title prefix, feature for `feat`, and task for every other prefix.

Only CU3 edits Story bodies, after approval. CU1 and CU2 propose placement,
labels, Rank and dependencies while preserving Story bodies. They report each
Epic's gap to Done when and finish with a new-conversation CU3 prompt.

Number new Epics after the highest `Epic N` title, closed ones included.
`Epic N · <outcome>` is a stable identifier; never renumber existing Epics.
Create all approved Epics before resolving references between them; every cited
Epic then carries its issue number. Without a Milestone, CU1 creates Epics in
the proposed order, their initial Rank. Only a Milestone description persists
Epic Rank. Epic bodies hold their own Stories in native Rank order, with Today
and After entries, never a replicated Order section.

## Approval, apply and readback

Every route stops at a complete proposal before any GitHub write, including
labels, comments and relationships. Approval covers the listed issues, exact
actions, bodies the route may edit, comments and evidence, not future arrivals.
For a read-only request, return the proposal and stop.

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
   Done when the unchanged approved actions and excluded actions are explicit
2. Apply those actions using label-for-issues' reconciliation and native commands.
   Report native failures; text never replaces a failed relationship. On a timeout,
   reread before retrying only missing operations. Any new action needs a new
   proposal. Done when each approved action is applied or reported as failed
3. Read back with label-for-issues' filters and paginated relations. Compare
   Story native order with Epic body order, blocked-by links, Milestone membership
   and Epic Rank, labels, and every issue's disposition. Each scoped issue must
   be placed, closed, or left out with its reason. Correct discrepancies within
   approval and reread until every applied action matches; report anything
   needing another approval. Done when every write is verified or reported failed

## Done when

- Each Story has a clear goal and acceptance criteria
- An Epic is ready when each Story is ready and ranked, its blocked-by links are set, and its Done when is checkable with no open decision
- A Milestone is ready when each Epic is ready and ranked

Only CU3 runs until these conditions hold. CU1 and CU2 hand off their remaining
gaps. End their report with this prompt, substituting real references:

```text
grooming-mode ; refine
Home repo: OWNER/REPO
Target: <Epic issue URL or Milestone URL>
Reverify every Story, propose refinements and readiness labels, and apply after approval.
Continue until grooming Done when holds.
```
