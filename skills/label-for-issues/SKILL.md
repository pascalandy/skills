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
   For authorized writes, create missing labels from the JSON below before any
   issue write names them. GitHub creates an unknown label on the fly, without
   its color or description, so when no available tool can create a label, leave
   it off and report it as missing.
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

Read [references/ticket-comments.md](references/ticket-comments.md) before you prepare a requested comment.

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

Read [references/github-cli.md](references/github-cli.md) before you set a relationship, search by relationship, or filter an issue list.
