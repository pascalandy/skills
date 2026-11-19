# GitHub sync

Read this file before you write the plan to GitHub or read issue states from GitHub.

## Prerequisites

- `gh` 2.94.0 or later. Check with `gh --version`. If the version is earlier, stop and ask the PM to upgrade ([install](https://github.com/cli/cli#installation))
- The `label-for-issues` skill. This file uses its `4-epic`, `2-type:*` and `1-ready-for-*` labels. Before the first issue write, load that skill and do its Step 4 for these labels only

## Ownership

- The markdown owns the definition: scope, briefs, order and decisions. Only the planner changes it
- GitHub owns the execution state in the active wave: open or closed, assignee, checked subtasks, verdicts and PR links
- The planner reads the GitHub states into the markdown at the wave review
- If the two disagree on a definition, the wave file is correct. Correct the markdown first, then write the issue body again

## Mapping

| Plan item | GitHub |
|---|---|
| Project, decisions, `proposed` waves | Nothing (markdown only) |
| Wave (`planned` or `active`) | Label `wave:W02` |
| Epic (`planned` and `active` waves) | Issue `[E03] <outcome>`, label `4-epic` |
| Task (`active` wave only) | Sub-issue of its epic, `[E03-T02] <name>`, with the label of its `Kind` |
| `Kind` of a task | `feature` gives `2-type:feature`. `fix` gives `2-type:bug`. `spike` and `chore` give `2-type:task` |
| QA task | Sub-issue of its epic, `[E03-QA1] QA: <epic name>`, labels `2-type:task` and `qa` |
| Task or QA task that obeys the Ready rule of `label-for-issues` | Label `1-ready-for-agent`, or `1-ready-for-human` when the brief has `Executor: human`. The plan checks are the review that the Ready rule records. An open blocker does not prevent the label |
| QA verdict | Label `qa:accepted`, `qa:accepted-with-findings` or `qa:rejected` on the QA issue |
| Finding | Sub-issue of the epic, `Finding (E03-QA1): <title>`, label `qa-finding` |
| Subtask | Checklist in the body of the task issue |
| Dependency | Native `blocked by` |
| Discovery in a wave | Labels `discovery`, `needs-replan` |

## Rules

1. Each epic, task, QA, finding and discovery issue has one `wave:` label
2. The body of an epic issue is the epic entry, word for word, without its briefs. For a continued epic, use the entry in the wave file where the epic started. The body of a task issue or QA issue is the brief. Each body ends with a link to the wave file
3. Write the issue number into the wave file: `#### E03-T02: <title> → #57`
4. Before you create an issue, find its exact title prefix. If the issue exists, update it:
   `gh issue list --state all --limit 500 --json number,title --jq '.[] | select(.title | startswith("[E03-T02] "))'`
5. Create the issues in batch order, so that each blocker exists before the issues that depend on it
6. A closed issue keeps the label of the wave in which it closed. A carried epic and its open tasks get the label of the receiving wave
7. Close the issue of a dropped task as not planned, with the reason in a comment
8. After each sync, read each issue that the sync wrote or closed
9. Compare the title, body, labels, parent, `blocked by`, state and close reason with the changes that the sync intended. Keep the execution state that GitHub owns
10. Correct each difference. Then do rules 8 and 9 again for the corrected issues

## Commands

```bash
for l in qa qa:accepted qa:accepted-with-findings qa:rejected qa-finding discovery needs-replan; do
  gh label create "$l" --force
done
gh label create "wave:W02" --color 0E8A16 --force
gh issue create --title "[E03] Users sign in with a password" --label 4-epic --label "wave:W02" --body-file body.md
gh issue create --title "[E03-T02] Login endpoint" --label 2-type:feature --label 1-ready-for-agent --label "wave:W02" \
  --parent 41 --blocked-by 56 --body-file body.md
gh issue create --title "[E03-QA1] QA: Users sign in with a password" --label 2-type:task --label qa --label 1-ready-for-agent --label "wave:W02" \
  --parent 41 --blocked-by 57 --body-file body.md
gh issue edit 57 --remove-label "wave:W01" --add-label "wave:W02"      # carried over
gh issue close 57 --reason "not planned" --comment "Dropped: <reason>"  # dropped
```

`gh issue create --help` gives the syntax for more than one `--blocked-by` value.
`gh issue edit --help` gives the parent and dependency flags for an edit. Their names are different from the names on create.
