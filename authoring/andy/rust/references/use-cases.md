# Use cases

Prompts that get the most out of this skill, grouped by branch. Show the user the rows that fit when they ask how to use the skill or what it can do, and adapt the names to their project.

## Start or adopt

| Prompt | What the agent does | What the user gets |
|---|---|---|
| "Start a new Rust CLI called `ledger` with the rust guardrails" | [A. Set up](../SKILL.md#a-set-up): `cargo new`, `init`, `just check`, then asks to commit the setup | A crate where the shortcuts below fail the build from the first commit |
| "Add the rust guardrails to this project without a big-bang cleanup" | [B. Audit](../SKILL.md#b-audit): `audit --violations`, then a proposal of the lints already at zero | Stricter lints today, with the lint debt left in place. The rest of the gate, such as `-D warnings`, `cargo deny`, and `cargo shear`, may still need fixes before `just check` passes |
| "Which profile lints could we turn on now? Turn on the ones at zero" | `audit --violations` again, after the debt shrank | The next ratchet step, backed by counts |
| "Set up the guardrails for `src-tauri/` in this repo" | `init` in the nested crate, plus the lefthook lines for the repository root | Guardrails for one crate inside a larger repository |
| "Add a crate `billing` to the workspace" | Creates the member with `[lints] workspace = true`; `just check` covers it | A new member that cannot escape the profile |

## Daily work

| Prompt | What the agent does | What the user gets |
|---|---|---|
| "Implement `parse_invoice`; run the gate before you say done" | [C. Work](../SKILL.md#c-work), ending on a quoted `just check` result | A change that passed fmt, Clippy, tests, `cargo deny`, `cargo shear`, and the guard |
| "This fails with E0382. Fix it without adding `clone`" | Reads `references/shortcuts.md` and fixes who owns the value | An ownership fix instead of a hidden copy |
| "Clippy flags `cast_possible_truncation` in `encode.rs`. Fix it properly" | Replaces the `as` cast with `TryFrom` and handles the error | No silent data loss, no `#[expect]` |
| "Approved: `#[expect(clippy::expect_used)]` on `load_schema`, reason: the schema is embedded at build time" | [Exceptions](../SKILL.md#exceptions) steps 2 to 4: writes the reason, commits, lists it for the PR | An exception that is visible, explained, and fails once stale |
| "This FFI call needs `unsafe`. Propose the change and wait for my OK" | Explains why the design needs it, then waits; after approval, `deny` plus `#[expect(unsafe_code)]` and `// SAFETY:` | `unsafe` only where a human said yes |

## Review

| Prompt | What the agent does | What the user gets |
|---|---|---|
| "Review this branch with the rust skill" | [D. Review](../SKILL.md#d-review): `diff --base origin/main --report`, then the review column of `references/shortcuts.md` | Each exception the guard detects, checked against an approval |
| "Did the agent cheat on the tests in this PR?" | Looks for removed, ignored, or disabled tests and weakened assertions; runs `cargo mutants --in-diff` | The removed, ignored, or disabled tests the guard detects, and the missed mutants to judge |
| "Run cargo mutants on my diff and add tests for the misses that matter" | Reads each missed mutant and adds the cases a caller would notice | Stronger tests on the code that changed |
| "Why did the pre-commit hook or `just check` stop me?" | Reads the `diff` answer and names each exception and its fix | A clear next step: fix the code, or approve the exception |

## Phrasing that helps

- Name the outcome and say "run the gate": the agent then cannot claim done on a red build
- Approve one exception at a time, with its reason: "Approved: `<attribute>` on `<item>`, reason: `<why>`". A vague "do what you need" approves nothing
- Ask for the design question behind an error ("who should own this?") rather than the quickest fix that compiles
