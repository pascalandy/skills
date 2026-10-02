# Routing cases

Run each request in a fresh session that has code-review-mode installed, from a worktree in the stated state. A case passes when the agent announces the expected playbooks and reads no other playbook file.

| Request | Worktree state | Expected |
|---|---|---|
| "Fais une revue du code, planifie" | Branch changes a script and its test, as in #282 | `test-audit` and `thermo-quality-review`, then a plan with the tests PR first. `architecture-review` is skipped because the target is a branch |
| "Fais une revue du code, planifie" | Branch changes production code only | `thermo-quality-review` |
| "Fais une revue du code, planifie" | Branch changes tests only | `test-audit` |
| "Fais une revue du code, planifie" | Branch changes Markdown only, as in `634d6ba` | Nothing to review. No playbook is read |
| "Review the code" | Default branch with no changes | A question asking which area to review |
| "Review `scripts/`" | Any | All three on `scripts/`, then a plan: tests PR, architecture PR, quality PR |
| "Revue de l'architecture de `scripts/`" | Any | All three on `scripts/`, and a plan that asks which candidate to build and recommends one |
| "Audit the tests in `scripts/tests`" | Any | `test-audit` alone |
| "Run a thermonuclear review" | Branch changes production code | `thermo-quality-review` alone |
| "Add a test for the new flag", during a feature | Any | The authoring gate in `test-audit`. No plan |
| `code-review-mode ; thermonuclear` | Any | `thermo-quality-review` alone |
| `code-review-mode ; test audit` | Any | `test-audit` alone |
| `code-review-mode ; architecture-review` | Any | `architecture-review` alone, with its HTML report and candidate question |
| `code-review-mode ; improve-codebase-architecture` | Any | `architecture-review` alone |
