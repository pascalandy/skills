---
name: "pa-code-review"
description: "Use only when explicitly invoked as `pa-code-review` after implementation and before user-facing QA."
keywords: ["pa-code-review", "code-review", "review", "implementation-quality", "readiness", "diff-review", "evidence-review"]
---

# PA Code Review

Explicit entry point: `pa-code-review`.

Use PA Code Review after implementation and before user-facing QA:

```text
implementation → /pa-code-review → /pa-qa
```

## Core Contract

For each review session:

1. Resolve the review scope and implementation intent.
2. Select only the review lenses warranted by the changed surface and risk.
3. Gather enough evidence to make a readiness judgment without editing files.
4. Separate confirmed evidence, inference, assumptions, and unknowns.
5. Deduplicate findings across lenses and assign practical severity.
6. Produce a parent-owned review record with readiness, risks, fix order, and next phase.
7. Hand implementation fixes back to the selected implementation workflow and user-facing validation to `pa-qa`.

## Operating Model

- **Parent `pa-code-review`**: owns diff scope, intent, lens selection, evidence synthesis, finding dedupe, contradiction handling, and final readiness judgment.
- **Inline investigation**: use for trivial reviews or lenses the parent can inspect confidently.
- **Optional delegated investigators**: use when a non-trivial lens benefits from independent read-only evidence gathering. They do not edit, stage, apply fixes, or make the final readiness decision.
- **Delegation is optional**: the skill must remain usable in any runtime that can inspect the repo and produce the parent review output.

## Review Lenses

Always-on lenses:

| Lens | Focus |
|---|---|
| `Correctness` | Behavior matches intent, edge cases, regression risk, logic errors |
| `Testing` | Meaningful test coverage, missing cases, brittle or misaligned tests |
| `Maintainability` | Simplicity, cohesion, readability, unnecessary complexity, local design quality |
| `ProjectStandards` | Repository conventions, style, tooling, file placement, agent/project instructions |

Conditional lenses:

| Lens | Use when the diff touches... |
|---|---|
| `Security` | auth, user input, secrets, permissions, public endpoints, unsafe IO |
| `ApiContract` | routes, schemas, exported types, CLI/API contracts, compatibility surfaces |
| `Reliability` | retries, timeouts, error handling, concurrency, background work, external systems |
| `CliReadiness` | commands, flags, help text, exit codes, stdout/stderr, agent-friendly output |

Do not add deferred lenses such as Performance or DataMigration until repeated review runs show a real need.

## Review Discipline

Apply these rules while judging readiness:

- **Simplicity first:** call out over-engineering, speculative abstractions, scope creep, and unnecessary lens expansion. Do not create findings for style preferences with no readiness impact.
- **Surgical changes:** review the approved diff and its necessary context. Do not demand broad refactors or adjacent cleanup unless the current change created the issue or cannot be correct without it.
- **Surface conflicts, don't average them:** when tests, docs, implementation, or conventions disagree, identify the stronger source or mark the conflict as unresolved. Do not split the difference in the readiness verdict.
- **Read before you judge:** inspect enough exports, callers, shared utilities, tests, and conventions before calling a change isolated, inconsistent, or safe.
- **Tests verify intent:** judge whether tests prove the acceptance intent and important failure modes, not merely that lines executed or snapshots changed.
- **Checkpoint after significant review steps:** when using multiple lenses or delegates, summarize evidence, findings, contradictions, and remaining unknowns before the final verdict.
- **Match codebase conventions:** treat project conventions as the baseline. If a convention appears harmful, record it as a risk or follow-up rather than reviewing against personal taste.
- **Fail loud:** name skipped checks, unavailable evidence, uncertain claims, uncovered `AC-*`, and any reason QA would be premature.

## Routing Rules

Use `references/ROUTER.md` for portable routing guidance when the review is not obviously trivial.

### Trivial / Inline

Answer directly without delegation only when all are true:

- the changed surface is tiny and obvious
- no shared contract, security, reliability, CLI, or cross-context risk is likely
- current context already contains enough evidence

Use compact output:

1. `Scope Reviewed`
2. `Findings`
3. `QA Readiness Verdict`
4. `Recommended Next Step`

### Standard

For normal code review, use the always-on set:

1. `Correctness`
2. `Testing`
3. `Maintainability`
4. `ProjectStandards`

### Conditional

Add conditional lenses conservatively when the diff or user request clearly triggers them:

- `Security`
- `ApiContract`
- `Reliability`
- `CliReadiness`

### Deep

For broad, risky, public, or release-critical changes, use always-on lenses plus every triggered conditional lens. Do not run every lens by default if the diff is small.

## Core Workflow

1. Resolve the review scope from user arguments, explicit `base:<ref>`, current diff, branch, or recent commits.
2. Infer implementation intent from the user request, branch name, recent commits, nearby plan/vision artifacts, or conversation context.
3. Classify the review as inline, standard, conditional, or deep.
4. Select review lenses using `references/ROUTER.md` when useful.
5. For each selected lens, read `references/<Lens>/MetaSkill.md` and gather evidence inline or request an optional delegated investigator.
6. When delegating, use `references/DelegatedEvidence/MetaSkill.md` as the portable evidence contract and give the investigator an absolute or otherwise unambiguous path to the assigned lens MetaSkill.
7. Compare evidence across lenses.
8. Deduplicate overlapping issues and resolve contradictions or mark them unknown.
9. Separate confirmed evidence, inference, assumptions, and unknowns.
10. Produce the final parent-owned review record.

## Review Record

For non-trivial review, synthesize into:

1. `Scope Reviewed`
2. `Implementation Intent`
3. `Review Lenses Used`
4. `Readiness Verdict` — `Ready`, `Ready With Nits`, `Needs Fixes`, or `Blocked`
5. `QA Readiness Verdict`
   - `Ready for pa-qa: yes/no`
   - `Reason: <one concise sentence>`
   - `Blocking issues: <none or bullets>`
   - `Non-blocking follow-ups: <none or bullets>`
6. `Findings` — each with severity `P0`-`P3`, lens, confidence, evidence, and recommended next step
7. `Tests / Checks Considered`
8. `Risks And Unknowns`
9. `Recommended Fix Order`
10. `Next Phase`

Severity guide:

- `P0`: unsafe to proceed; data loss, security break, severe regression, or unusable core path.
- `P1`: must fix before QA/release; likely bug, broken contract, missing critical validation.
- `P2`: should fix soon; maintainability, coverage, reliability, or edge-case risk.
- `P3`: nit or optional cleanup; does not block readiness.

QA readiness rule:

- `Ready for pa-qa: yes` means no known issue would make user-facing QA misleading, useless, or premature. P2/P3 follow-ups may remain if they do not block meaningful validation.
- `Ready for pa-qa: no` means at least one P0/P1 or unresolved blocker should return to implementation before user-facing validation.
- Do not use `maybe` or `partial`; choose `yes` with explicit non-blocking risks or `no` with explicit blocking issues.

Do not paste raw investigator output. The parent owns judgment.

## Boundaries

- Report-only/read-only by default.
- Do not apply fixes from this skill.
- Route fixes to a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook, or back to another selected implementation loop.
- Do not turn this into user-facing QA; `/pa-qa` validates behavior from the user's perspective.
- The parent may run read-only checks/tests when explicitly useful and safe under project rules. Delegated investigators remain read-only evidence gatherers.

## Anti-Patterns

Do not:

- apply fixes, stage files, or mutate the codebase from this skill
- treat delegated investigator output as the final review judgment
- run every lens by default when the diff is small or low-risk
- inflate nits into blockers without user-facing, correctness, safety, or maintainability impact
- bury readiness behind a list of observations without a clear verdict
- report implementation guesses as confirmed findings
- duplicate the same issue under multiple lenses instead of consolidating it
- turn code review into user-facing QA; route behavior validation to `pa-qa`
- turn code review into repair execution; route fixes to the selected implementation workflow

## Session Loop

After each review record, continue with the user's next selected action: clarify scope, inspect another diff, route fixes to the selected implementation workflow, proceed to `pa-qa`, export the review, or stop.

## Export

Default to answering in chat. Export only if the user explicitly asks for a reusable review artifact.
