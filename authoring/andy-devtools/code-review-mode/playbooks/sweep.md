---
description: "Sweep code that no diff touches for bugs, hard-coded values that should vary, and unfinished code, and draft one issue per finding."
---

# Sweep

A branch review reads only the branch's changes, so code that no branch changes goes unreviewed. A sweep reads that code with fresh eyes and drafts an issue for each problem it proves. It changes no code.

The method restates two prompts by Jeffrey Emanuel: [random exploration](https://x.com/doodlestein/status/2007588870662107197) and [constants and unfinished code](https://x.com/doodlestein/status/2036623384235200883).

Copy this checklist and track your progress:

```
Sweep progress:
- [ ] Step 1: Learn the project
- [ ] Step 2: Trace flows
- [ ] Step 3: Hunt hard-coded values
- [ ] Step 4: Hunt unfinished code
- [ ] Step 5: Prove each finding
- [ ] Step 6: Draft the issues
```

**Step 1: Learn the project.** Read `AGENTS.md`, `README.md`, and the docs they name for the target. Done when you can state in one sentence what the target is for.

**Step 2: Trace flows.** Pick files at random across the target. Follow each into the files it imports and the files that import it, until you can say which workflow it serves. Then read that workflow for bugs: wrong conditions, swallowed errors, and callers that break a callee's contract. Done when traced flows cover every top-level folder of the target.

**Step 3: Hunt hard-coded values.** Find literals that must change for the code to stay correct: paths, hosts, limits, dates, versions, and copies of a value that lives elsewhere. Done when you have judged each literal you found as a finding or as fine.

**Step 4: Hunt unfinished code.** Find `TODO` and `FIXME` markers, comments that promise later behavior such as "will" or "for now", stubs that return a placeholder, and mocks or fakes that production code can reach. When the `mock-code-finder` skill is installed, run it on the target for this step. Done when you have judged each match as a finding or as fine.

**Step 5: Prove each finding.** Back each finding with what you observed: a call path, a command and its output, a failing test, or the line that contradicts the docs. Drop each finding you cannot prove. Done when every finding left carries its proof.

**Step 6: Draft the issues.** Write one issue per fix that can land alone, in this shape:

```
### <imperative title>
- Where: `path/to/file.py:42`
- Proof: <what you observed>
- Fix: <one line>
- Severity: high | medium | low
```

Order the issues by severity. The drafts are the deliverable. File them only when the request asks. Done when every proven finding sits in exactly one issue.
