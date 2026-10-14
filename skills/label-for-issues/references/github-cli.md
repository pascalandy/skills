# GitHub CLI

`gh` 2.94 and later manages issue relationships. On an older version, report it
and use `gh api` for relationships. Set them with `gh issue create --parent`,
`--blocked-by`, or `--blocking`, and with `gh issue edit --parent`, `--remove-parent`,
`--add-sub-issue`, `--remove-sub-issue`, `--add-blocked-by`, `--remove-blocked-by`,
`--add-blocking`, or `--remove-blocking`, using URLs for issues in other
repositories. Keep `gh api` for what `gh` lacks, such as editing a comment by ID or
reading timeline events.

- `--parent` and `--add-sub-issue` silently replace an existing parent. Read
  `parent` first; moving an issue to another epic detaches it from the old one
- Search qualifiers need full references, as in `parent-issue:OWNER/REPO#N` and
  `blocked-by:OWNER/REPO#N`; a bare number matches nothing. `has:blocked-by` also
  matches issues whose blockers are closed. To drop issues with an open blocker, add
  `--json number,title,blockedBy --jq '[.[] | select(.blockedBy.totalCount == (.blockedBy.nodes | length)) | select(all(.blockedBy.nodes[]; .state == "CLOSED"))]'`
  This excludes incomplete blocker lists; page those before assessing readiness

## Issue-list filters

Pass `--repo OWNER/REPO --search '<filter>' --limit 1000` to `gh issue list`.
If the result reaches the limit, partition the search and account for every issue.
Searches for closed issues also need `--state all`.

- Backlog: `is:issue is:open no:parent-issue -label:4-epic`
- Epics: `is:issue is:open label:4-epic`
- Epics without a Milestone: `is:issue is:open label:4-epic no:milestone`
- One Epic's Stories, open or closed: `is:issue parent-issue:OWNER/REPO#N`
- Children with a parent: `is:issue is:open has:parent-issue`; read each
  native parent's labels to distinguish Stories from Sub-tasks. Count open
  Stories even when their Epic is closed. A Sub-task stays with its non-Epic parent
- Agent candidates: `is:issue is:open label:1-ready-for-agent -label:0-impediment`,
  then apply the blocker filter above and check prerequisites in issue content
- Agent WIP: `is:issue is:open label:1-wip-by-agent`

GitHub ignores `has:sub-issues`; use the Epic label to identify containers.
There is no Story label. Membership is the native parent relationship.

## Rank and relation pagination

Attach Stories one at a time in approved Rank order with
`gh issue edit <epic> --repo OWNER/REPO --add-sub-issue <story-url>`.
An attachment appends to the native order. For an attached Story, obtain its
numeric REST `id`, then reorder it with
`gh api --method PATCH repos/OWNER/REPO/issues/EPIC/sub_issues/priority -F sub_issue_id=ID -F before_id=OTHER_ID`,
or `after_id`. Read back native order and compare it with the Epic body.

`gh issue view` relationship nodes can be truncated. Compare their length
with `totalCount`, then page incomplete lists with `gh api --paginate`:

- Stories: `repos/OWNER/REPO/issues/N/sub_issues?per_page=100`
- Blockers: `repos/OWNER/REPO/issues/N/dependencies/blocked_by?per_page=100`
- Blocking: `repos/OWNER/REPO/issues/N/dependencies/blocking?per_page=100`

Keep each related issue's repository from its URL. Re-read its labels and state;
relationship nodes alone do not establish Story membership or readiness.

## Milestones

A Milestone belongs to one repository. Assign it only to Epics in the home repo;
Stories remain in their own repositories without a Milestone.

- List, with pagination: `gh api --paginate 'repos/OWNER/REPO/milestones?state=all&per_page=100'`
- Read: `gh api repos/OWNER/REPO/milestones/N`
- Create: `gh api --method POST repos/OWNER/REPO/milestones -f title='M<N> · <outcome>' -f description='<outcome and Epics by Rank>'`
- Update: `gh api --method PATCH repos/OWNER/REPO/milestones/N -f description='<approved description>'`
- Attach an Epic: `gh issue edit <epic> --repo OWNER/REPO --milestone '<title>'`
- Detach: `gh issue edit <epic> --repo OWNER/REPO --remove-milestone`
- Read membership: `gh issue list --repo OWNER/REPO --state all --search 'is:issue milestone:"<title>"' --limit 1000 --json number,title,state,labels,milestone`

The description's numbered Epic list owns Epic Rank; each entry carries its
issue number. Apply Step 4's migration approval before renaming an existing
Milestone or changing legacy labels.
