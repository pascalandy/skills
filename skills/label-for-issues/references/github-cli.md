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
