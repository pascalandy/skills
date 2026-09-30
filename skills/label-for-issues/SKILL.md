---
name: "label-for-issues"
description: "Use when triaging GitHub issues, managing issue labels or decision comments, creating issues or PRs, or starting work on an issue."
kind: "dev"
---

# Label for issues

Help the user decide what happens next on each issue. Labels carry the assessment;
a decision comment is opt-in, as Ticket comments defines.
Apply this vocabulary to issues, not PRs. Keep one state and one priority
per open triaged issue, one type except for epic parents, at most one epic role, and
optional impediments.

## Workflow

1. **Scope.** Resolve the repository and requested issues. Reviews are read-only
   unless changes were requested. Creating issues includes labeling them; creating
   a PR includes updating its explicitly linked issues. No linked issues means no
   label work unless setup was requested. Limit changes to those issues and directly
   affected epics; include closed issues only on request. Leave issue and PR
   authoring to the caller. Do not start implementation, rewrite
   specifications, or modify other skills as a labeling side effect
   For setup-only requests, go directly to Reconcile
2. **Inspect.** Read the label catalog once per run with
   `gh label list --limit 200 --json name,color,description`, raising the limit if
   it returns 200 rows. Read each issue with
   `gh issue view <n> --json state,stateReason,body,comments,labels,parent,subIssues,blockedBy,blocking,closedByPullRequestsReferences`,
   then relevant review records and linked issue and PR states. Follow evidence that
   could change the decision; do not audit unrelated code or tickets. Prefer current
   object states over stale prose, but retain explicit human decisions unless new
   evidence warrants revisiting
3. **Assess.** Form one assessment per issue: desired labels, evidence, unresolved
   decision or input, recommendation, next actor, and start conditions. Derive label
   edits, a one-line summary naming the next actor, recommendation, and any blocker,
   and any requested comment from it. Separate facts from inference and name any
   uncertainty that could change the recommendation. Stop investigating once the
   next action is supported; if evidence is insufficient, identify the smallest
   question or check that would resolve it. Prepare a requested comment using Ticket
   comments before writing. For read-only requests, return the label diff, summaries,
   and any requested comment preview, then stop
4. **Reconcile.** For setup-only requests, first read the repository label catalog.
   For authorized writes, create missing labels from the JSON below.
   Update metadata only when existing meanings match. Report equivalent names,
   case variants, and semantic conflicts with proposed mappings and affected issues.
   Ask the user whether to migrate and agree on scope before changing legacy labels;
   reuse approval within that scope. Do not silently rename, delete, or reinterpret
   labels. Preserve custom labels; continue unambiguous changes. Missing canonical
   labels alone need no migration approval. Read-only setup returns proposed metadata
   without writes. Setup-only requests end after label metadata is verified and reported
5. **Apply and verify.** Reread the issue, labels, comments, and relationships before
   writing; revise the assessment if relevant evidence changed. Apply targeted
   label and relationship changes with `gh issue edit`, following GitHub CLI.
   Replace only canonical labels in the same family. Read back changed labels,
   review records, and relationships; check family exclusivity and epic membership.
   Publish a requested decision comment using verified results, then read it back.
   Report each issue's label changes and summary, issue and comment links, conflicts,
   and partial failures. Without a comment request, flag an existing managed comment
   that the new labels contradict as stale and leave it unedited. If a write times
   out or fails, reread before retrying and perform only missing operations. Continue
   independent issues; report triage as complete only when all requested changes
   are verified

## Ticket comments

Write or update an issue comment only when the user explicitly asks for one.
Triage, issue creation, PR links, and label changes do not imply a comment.

When preparing a requested comment, load and apply `$sparring` from the active skill
catalog once per run, including for read-only previews. If unavailable, withhold the
comment and report the missing dependency; the requested comment remains incomplete.
Use its reasoning discipline to help the human decide or act; keep the comment
proportional to the decision, without manufacturing a debate.

Keep one concise decision comment per issue. Explain verified changes, not intended
ones; a partial failure must not produce a prompt claiming prerequisites are met.
In read-only previews, describe label edits as proposed, never completed.

Mark the managed comment with `<!-- label-for-issues:decision -->` and retain its
comment ID. `gh issue comment <n> --body-file <file>` prints the new comment's URL,
which ends in `#issuecomment-<id>`; `gh issue view <n> --json comments` lists the
same URLs. Edit by that ID with
`gh api --method PATCH repos/OWNER/REPO/issues/comments/<id> -F body=@<file>`,
because `gh issue comment --edit-last` picks the account's newest comment, which can
be a human's. Edit that exact comment only when its provenance establishes it as an
agent-managed triage comment through a recorded prior write or an explicit agent
signature consistent with its triage content. A marker or shared GitHub account
alone is insufficient.
Adopt an unambiguously agent-written legacy triage comment by adding the marker.
Otherwise create one without altering human comments. If ownership is ambiguous or
multiple managed comments exist, report the conflict rather than adding another.
Recheck the selected comment before editing and preserve intervening human additions.

When asked to update it, refresh that comment when the evidence, options, or
recommendation changes, even if the labels stay the same. Leave it untouched when
both labels and reasoning remain current; recover missing comments after partial
failures.

End every comment you create or update with `Updated by [AGENT NAME]`, replacing
the placeholder with your actual agent name. On edits, replace the existing agent
signature with your own instead of accumulating signatures.

Format comments in this order, omitting sections with no applicable action:

1. Start with one H2 combining issue number, next actor, and action:
   `## #52 · Waiting on Pascal to choose the test environment` or
   `## #57 · Agent can audit specification compliance`
   Do not repeat the issue title, status, or owner in another heading or bold banner
   If no action is needed, say so rather than inventing a decision or task
2. Give brief evidence explaining the current state and successful label changes.
   Link the decisive source, such as a comment, PR, or verification result. Distinguish
   a reported claim from something verified; do not infer completion from labels
   For `1-needs-info`, name missing inputs, why they matter, who supplies them,
   and what they unblock. When removing a blocker, explain what resolved it
3. For a human decision, offer meaningful A/B/C choices with consequences.
   For new choices, put the evidence-backed recommendation first, formatted like
   `- **A · Use an existing test environment. (recommended)** Provide node access`
   Format B and C likewise without the recommendation marker. When updating, preserve
   existing option letters and their meanings; move the recommendation marker instead
   of reassigning letters. Interpret replies against the choices the person answered.
   Give the benefit and
   main cost or risk of each real alternative. If evidence cannot support a choice,
   recommend the smallest information-gathering step instead of guessing. Use fewer
   choices when no meaningful alternative exists. Do not reopen a settled decision
   without new evidence, or repeat “choose one” beneath a
   heading already naming the decision, or invent approval gates for authorized work
4. For agent-executable work, add an H3 stating when its prompt applies, such as
   `### Agent prompt after choosing A`, followed by a fenced text prompt.
   Include repository/issue references, concrete task, required inputs, scope,
   verification, deliverable, and stopping conditions. State whether work can start
   now or depends on a decision/access. Separate human decisions from agent execution;
   do not assign technical work to a human merely because access is missing.
   Reuse issue requirements by reference instead of copying entire specifications.
   Provide a prompt only for the recommended or already chosen path; add alternatives
   only when they need different handoffs. A prompt does not itself authorize
   execution, closure, merge, or publication

Keep comments proportional: brief context, bold option labels only, no duplicate
recommendation paragraph, no periods at bullet ends. Before posting, check that
readers can identify who acts next, choose an option, and hand agent work off
without reconstructing the investigation. Read-only requests produce previews only.

## Classification rules

- **State.** Use one state label per open triaged issue. Upstream triage names
  such as `ready-for-agent` map to their `1-` names here. Use needs-triage for scope
  or approach decisions, needs-info for specific missing information, and wontfix
  for work that will not be actioned. An exploratory idea is not automatically
  missing information. Pair wontfix with closure only when explicitly authorized
- **Ready.** Validate scope, acceptance criteria, dependencies, and open decisions.
  Reuse a current review or record reviewer, date, scope, conclusion, and blockers.
  Choose ready-for-agent for autonomous implementation or ready-for-human when
  implementation requires a human. Neither authorizes starting work. Check unresolved
  prerequisites and impediments before execution. Reassess when scope changes
- **Agent work.** When authorized work begins, including investigation, replace
  `1-ready-for-agent` with `1-wip-by-agent`. Reading or triaging alone does not count.
  On handback, reassess readiness. On authorized closure, remove WIP
- **Epics.** Optional for outcomes spanning independently useful issues; keep small
  features standalone. Use `4-epic:parent` with boundaries, completion criteria,
  and member links; it needs no type label. Members retain their bug, feature, or
  task type plus `4-epic:member`. Features contain their own specification
- **Membership.** Require a parent relationship to an issue labeled
  `4-epic:parent` or explicitly designated as an epic, not just any parent or mention.
  Prefer GitHub's native relationship; otherwise use reciprocal links and report
  the fallback. Remove membership on detachment, not when the parent closes.
  A merged PR alone proves neither issue nor epic completion
- **Dependencies.** Record prerequisites through native relationships or issue/epic
  content, not labels. Membership does not imply execution order
- **Impediments.** Use `0-impediment` for a concrete obstacle preventing progress;
  explain it in the issue and remove the label when resolved. Preserve the state.
  Planned dependencies, missing details, and deliberate deferral do not automatically
  warrant this label. Label an epic only when its own progress is impeded
- **Priority.** Preserve established priorities; default new issues to p2.
  Change priority from user direction or concrete urgency. Security work is not
  automatically p0. Members and parents do not inherit each other's priority

## Labels

Use lowercase names. Prefixes sort impediment, state, type, priority, then epic role.
Colors: gray for context, amber for attention, green for ready, blue for active work,
orange for high priority, red for impediments or emergencies.
This JSON owns exact names, colors, and descriptions.

```json
[
  {"name": "0-impediment", "color": "d95757", "description": "A concrete obstacle prevents progress; details are recorded in the issue"},
  {"name": "1-needs-info", "color": "d4a72c", "description": "Specific information is missing from the issue"},
  {"name": "1-needs-triage", "color": "d4a72c", "description": "Scope, approach, or direction needs evaluation"},
  {"name": "1-ready-for-agent", "color": "3da66d", "description": "Validated work, sufficiently specified for an autonomous agent"},
  {"name": "1-ready-for-human", "color": "3da66d", "description": "Validated work requiring human implementation"},
  {"name": "1-wip-by-agent", "color": "1d76db", "description": "An agent has started work on this issue"},
  {"name": "1-wontfix", "color": "8b949e", "description": "Will not be actioned"},
  {"name": "2-type:bug", "color": "8b949e", "description": "Existing behavior is broken"},
  {"name": "2-type:feature", "color": "8b949e", "description": "New or improved functionality; specification lives in the issue"},
  {"name": "2-type:task", "color": "8b949e", "description": "Supporting work such as maintenance, documentation, refactoring, or verification"},
  {"name": "3-pty:p0", "color": "d95757", "description": "Emergency requiring immediate attention, such as active exploitation or a major outage"},
  {"name": "3-pty:p1", "color": "db8b40", "description": "High priority; takes precedence over ordinary planned work"},
  {"name": "3-pty:p2", "color": "8b949e", "description": "Normal planned work; default when no priority is established"},
  {"name": "3-pty:p3", "color": "8b949e", "description": "Low-priority work that can wait"},
  {"name": "4-epic:member", "color": "8b949e", "description": "Belongs to an epic identified by the parent relationship"},
  {"name": "4-epic:parent", "color": "8b949e", "description": "Groups linked member issues around a shared outcome"}
]
```

## GitHub CLI

`gh` 2.94 and later manages issue relationships. On an older version, report it
and use `gh api` for relationships. Set them with `gh issue create --parent`,
`--blocked-by`, or `--blocking`, and with `gh issue edit --parent`, `--remove-parent`,
`--add-sub-issue`, `--remove-sub-issue`, `--add-blocked-by`, `--remove-blocked-by`,
`--add-blocking`, or `--remove-blocking`, using URLs for issues in other
repositories. Keep `gh api` for what `gh` lacks, such as editing a comment by ID or
reading timeline events.

- `--parent` and `--add-sub-issue` silently replace an existing parent. Read
  `parent` first; moving an issue to another epic detaches it from the old one
- `subIssues`, `blockedBy`, and `blocking` are objects: iterate `.nodes[]` and count
  `.totalCount`. Nodes carry number, state, title, and URL, not labels. They stop at
  100, 50, and 50 nodes; page the rest with `gh api --paginate` when `totalCount` is
  higher
- Search qualifiers need full references, as in `parent-issue:OWNER/REPO#N` and
  `blocked-by:OWNER/REPO#N`; a bare number matches nothing. `has:blocked-by` also
  matches issues whose blockers are closed. To drop issues with an open blocker, add
  `--json number,title,blockedBy --jq '[.[] | select(all(.blockedBy.nodes[]; .state == "CLOSED"))]'`
- `gh issue list` and `gh label list` return 30 rows unless given `--limit`

## Issue-list filters

- Overview: `is:issue is:open -label:4-epic:member`
- Epics: `is:issue is:open label:4-epic:parent`
- Members: `is:issue is:open label:4-epic:member`
- One epic's members: `is:issue parent-issue:OWNER/REPO#N`
- Members missing a parent: `is:issue is:open label:4-epic:member -has:parent-issue`
- Agent candidates: `is:issue is:open label:1-ready-for-agent -label:0-impediment`,
  then drop open blockers as GitHub CLI shows and check prerequisites in issue content
- Agent WIP: `is:issue is:open label:1-wip-by-agent`
