# Routing cases

Run each request in a fresh session that has code-review-mode installed, from a worktree in the stated state. A case passes when the agent announces the expected playbooks, reads no other playbook file, and changes no file unless the request asks for changes.

| Request | Worktree state | Expected |
|---|---|---|
| "Fais une revue du code, planifie" | Branch changes a script and its test, as in #282 | `test-audit` and `thermo-quality-review`, then a plan with the tests PR first |
| "Fais une revue du code, planifie" | Branch changes production code only | `thermo-quality-review` |
| "Fais une revue du code, planifie" | Branch changes tests only | `test-audit` |
| "Fais une revue du code, planifie" | Branch changes Markdown only, as in `634d6ba` | Nothing to review. No playbook is read |
| "Review the code" | Default branch with no changes | A question asking which area to review |
| "Review `scripts/`" | Any | `test-audit` and `thermo-quality-review` on `scripts/` |
| "Audit the tests in `scripts/tests`" | Any | `test-audit` alone. It reports candidates and edits nothing |
| "Run a thermonuclear review" | Branch changes production code | `thermo-quality-review` alone |
| "Run a thermonuclear review of `scripts/`" | Branch changes files outside `scripts/` | `thermo-quality-review` alone on `scripts/`, not on the branch |
| "Add a test for the new flag", during a feature | Any | The authoring gate in `test-audit`. No plan |
| `code-review-mode ; thermonuclear` | Any | `thermo-quality-review` alone |
| `code-review-mode ; thermo-nuclear-code-quality-review` | Any | `thermo-quality-review` alone |
| `code-review-mode ; test audit` | Any | `test-audit` alone |
