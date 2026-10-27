# Approved plan readback

Use this format when phase 2 writes `approved-plan.json`. Include each issue whose
parent, native order, labels, blockers, or state the approved actions preserve or
change, including affected Epics. Resolve new issue numbers before writing the file.
Keep expectations from the approved proposal. A GitHub response is evidence to
compare, not the source of the expected values.

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

- `repo` and positive integer `number` identify the issue
- `parent` is a canonical `OWNER/REPO#N` reference or `null` for no parent
- `stories` contains all native sub-issue references in order, including closed
  issues. For an Epic these are Stories; for another issue these are its Sub-tasks.
  Use `[]` when it has none
- `labels` contains all final label names, including labels the actions preserve
- `blocked_by` contains all native blocker references, including closed blockers
- `state` is `OPEN` or `CLOSED`

Use canonical references for all relations, also within the same repository.
Repeated issues or repeated entries in an array are invalid.
Labels and blockers compare as sets. Native order compares as a list.
An issue with `4-epic` in either its expected or actual labels also gets a body
comparison. Its single `## Stories` section must use the numbered entries of the
Epic template, with `(#N)` for its own repository or `(OWNER/REPO#N)` for another.
The body references must equal the native order. A missing or unreadable section
fails, including when the expected list is empty.

From the skill folder, run:

```bash
uv run scripts/readback.py approved-plan.json
```

Run `uv run scripts/readback.py --help` for input and timeout options.
The script uses authenticated `gh api graphql` queries against github.com.
It pages labels, native sub-issues, and blockers until their counts and pagination
metadata agree. A missing node, changed count, failed page, or incomplete response
fails the readback. A missing parent is the value `null`.

A full match prints `{"ok":true}` on stdout. A comparison failure leaves stdout
empty and ends stderr with an object such as:

```json
{"ok":false,"errors":["GitHub differs from the approved plan; correct only approved actions and rerun readback"],"differences":[{"issue":"pascalandy/skills#335","field":"parent","expected":"pascalandy/skills#969","actual":null}]}
```

Each difference has `issue`, `field`, `expected`, and `actual`.
The `body_stories` field compares the body with the native list; `actual: null`
means the body list could not be read. Read failures also fail, with their cause in
`errors`. Within approval, fix the GitHub discrepancy and rerun the same plan.
If the expected action needs approval, return that action to refinement.

The script covers these issue fields only. Continue the phase 3 comparison for
other approved actions, including bodies beyond the Stories list, Milestones,
comments, and left-out dispositions.
