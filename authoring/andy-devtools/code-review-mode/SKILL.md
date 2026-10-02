---
name: "code-review-mode"
description: "Use for a code review of a branch or code area, an architecture review, a test audit, or a thermonuclear review, and whenever writing or changing tests."
kind: "dev"
---

# Code review mode

Code-review-mode reviews code with one playbook per object under review. A request describes the review in plain words; the mode picks the playbooks.

| Playbook | Aliases | Reviews |
|---|---|---|
| [`test-audit`](playbooks/test-audit.md) | | Tests, and production code that exists only for tests |
| [`thermo-quality-review`](playbooks/thermo-quality-review.md) | `thermonuclear`, `thermo-nuclear-code-quality-review` | Production code: structure, file size, branching, types, and layering |
| [`architecture-review`](playbooks/architecture-review.md) | `improve-codebase-architecture` | Module shape across an area: depth, seams, and locality |

## Pick the route

Take the first rule that fits, and say which playbooks run and why:

1. **A test is being written or changed outside a review.** Apply the authoring gate in `test-audit`, then stop.
2. **A name follows the mode**, as in `code-review-mode ; test-audit`. Run that playbook alone, through its own procedure and report. Compare names with case, spaces, hyphens, and underscores ignored; an alias counts as its playbook's name.
3. **The request limits the review to tests or to code quality.** A test audit or sweep runs `test-audit` alone, and a thermonuclear review runs `thermo-quality-review` alone, each through its own procedure and report.
4. **Any other review** follows the steps below.

Every review works on the request's target and reports before it edits. The target replaces any default scope a playbook names, such as the current branch. Change files only when the request asks for changes.

## 1. Find the target

- **A branch:** its changes since it left the default branch, plus uncommitted changes.
- **An area the request names**, such as a directory or a module: the code in that area.
- **An architecture review of a branch:** the modules the branch touches.
- **No changes and no area:** ask which area to review, and wait for the answer.

## 2. Pick the playbooks

Choose one playbook per object present in the target:

- `test-audit` for tests and test support
- `thermo-quality-review` for production code
- `architecture-review` when the target is an area or the request names architecture; a module refactor needs the test net before it and the polish after, so the other two review the same area

A target with only documentation or configuration has nothing to review: say so and stop.

Announce the choice before running it: each playbook chosen, each one skipped, and why.

## 3. Run the reviews

Give each chosen playbook its own subagent, with the playbook's path, the target, and the instruction to report findings without editing. `architecture-review` returns its candidates as text; its HTML report and its candidate question belong to a run of that playbook alone. Without subagents, run the playbooks one after another. The step is complete when every chosen playbook has returned its findings.

## 4. Return one plan

Order the plan's PRs as they must be implemented, each with its reason:

1. `test-audit` first: a refactor is proven only by tests it leaves untouched.
2. `architecture-review` second: the chosen candidate reshapes the modules on that test net.
3. `thermo-quality-review` last: polish spent on code the architecture PR removes is wasted.

Each PR lists the findings it applies and the check that proves it. When `architecture-review` returns candidates, the plan asks which one to build and recommends one. A finding in code that a candidate would remove is marked as depending on that candidate. Before the quality PR, rerun `thermo-quality-review` on the code the architecture PR leaves. When the target has almost no tests, the first PR adds behavior tests at the outer boundary, under the authoring gate.

The plan is the deliverable. When the request asks for changes, build one PR at a time in the plan's order.

Use [routing cases](references/routing-cases.md) when changing a playbook name, an alias, or these rules.
