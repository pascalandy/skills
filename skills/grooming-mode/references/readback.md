# Approved plan readback

Use this format when phase 2 writes `approved-plan.json` in the run's own folder. Record its absolute path.
Include each issue whose parent, native order, labels, blockers, or state the approved actions preserve or change, including affected Epics.
When an issue's parent changes, include its previous and new parents, also when they are outside the proposed hierarchy.
Before any phase 2 GitHub write, record each existing included issue's parent, complete native sub-issue order, labels, blockers, and state as the keys below describe.
Take changed values from the approved proposal and other preserved values from that phase 1 recheck.
A read made after a write supplies actual values only, except approved new issue numbers resolved after creation.
New issue expectations come entirely from the approved proposal.

If a failed creation leaves a row's issue number or relation reference unresolved,
keep its draft expectations and dependent actions in the failed-action report.
Omit that row from the plan file and explicitly report its comparisons as not
run; do not invent IDs or substitute observed values or `null` for an unresolved
parent. Write the plan file for independently resolvable rows. If none remain, do not
write an empty plan or run the script: report all its comparisons as not run.
A partial plan file's success covers only its included rows; unresolved actions remain
failed and their affected hierarchies unready. If creation later succeeds, resolve
the original approved rows into the same plan file before rerunning it.

```json
{
  "issues": [
    {
      "repo": "pascalandy/skills",
      "number": 969,
      "parent": null,
      "stories": ["pascalandy/skills#335"],
      "labels": ["4-epic", "1-ready-for-agent", "3-pty:p2"],
      "blocked_by": [],
      "state": "OPEN"
    },
    {
      "repo": "pascalandy/skills",
      "number": 335,
      "parent": "pascalandy/skills#969",
      "stories": [],
      "labels": ["2-type:feature", "1-ready-for-agent", "3-pty:p2"],
      "blocked_by": ["other/project#7"],
      "state": "OPEN"
    }
  ]
}
```

The example shows the format, not current GitHub values. The file has only the
`issues` array, which is nonempty. Each row has exactly these seven required keys:

- `repo` uses GitHub's canonical `OWNER/REPO` spelling, and `number` is a positive integer
- `parent` is a canonical `OWNER/REPO#N` reference or `null` for no parent
- `stories` contains all native sub-issue references in order, including closed
  issues. For an Epic these are Stories; for another issue these are its Sub-tasks.
  Use `[]` when it has none
- `labels` contains all final label names, including labels the actions preserve
- `blocked_by` contains all native blocker references, including closed blockers
- `state` is `OPEN` or `CLOSED`

Use canonical references for all relations, also within the same repository.
Repeated JSON keys, issues, or entries in an array are invalid.
Labels and blockers compare as sets. Native order compares as a list.
An issue with `4-epic` in either its expected or actual labels also gets a body
comparison, including closed Epics. Under its single `## Stories` heading, GitHub's
rendered body may be empty to represent `[]`; otherwise, it must hold one ordered
list and nothing else. Each direct entry has
exactly one parenthesized `(#N)` or `(OWNER/REPO#N)` reference, in native order.
Nested Today and After details add no Stories and may hold code blocks or quotes.
Missing or unreadable sections, ambiguous references or link targets, multiple
lists, and code blocks or quotes outside nested details fail.
GitHub renders Markdown, comments, and fences. The script does not reinterpret them.
Preserve closed Epic bodies. Report their discrepancies as failed comparisons;
a discrepancy does not authorize a body edit.

From the skill folder, run:

```bash
uv run scripts/readback.py /absolute/run-folder/approved-plan.json
```

Run `uv run scripts/readback.py --help` for input and timeout options.
The script uses authenticated `gh api graphql` queries against github.com.
It pages labels, native sub-issues, and blockers until their counts and pagination
metadata agree. A missing node, changed count, failed page, or incomplete response fails the readback.

A full match prints `{"ok":true}` on stdout. A comparison failure leaves stdout
empty and ends stderr with an object such as:

```json
{"ok":false,"errors":["GitHub issue fields or Epic body order differ; correct only approved actions and rerun readback"],"differences":[{"issue":"pascalandy/skills#335","field":"parent","expected":"pascalandy/skills#969","actual":null}]}
```

Each difference has `issue`, `field`, `expected`, and `actual`. Expected values come from the plan file except for `body_stories`:
it compares the body against the current native list, so its `expected` value is that native order.
An `actual: null` body list could not be read. If native order differs from the plan file,
correct the approved native writes and rerun before correcting the body; do not copy an incorrect native order into an approved body.
Read failures also fail, with their cause in `errors`. Within approval, fix the GitHub discrepancy and rerun the same plan file.
If the expected action needs approval, return that action to refinement.

The script covers these issue fields only. Continue the phase 3 comparison for other approved actions,
including bodies beyond the Stories list, Milestones, comments, and left-out dispositions.
