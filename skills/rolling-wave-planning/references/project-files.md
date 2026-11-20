# Project files

Read this file before you write `01-project.md`, `decisions.md` or `qa.md`.

## `01-project.md`

```markdown
# ACME: Project

## Summary
- Objective: …
- Stakeholders: …
- Success criteria: SC1 …, SC2 …
- Constraints: …
- Out of scope: …
- Source: [Business case](00-business-case.md) · Agent file: [CLAUDE.md](../CLAUDE.md)
- QA machine: dedicated QA host

## Open questions
1. … → spike E01-T01 | asked to PM | resolved D002

## Limits
- Task: one module or ≤ 8 files, ≤ ~400 changed lines, ≤ 5 acceptance items.
- QA: intermediate QA when an epic has > 5 tasks or spans > 2 batches; ≤ 8 QA scenarios per QA task.
- Recalibrated: W01 review

Next IDs: E06, D004

## Waves
| ID | Name | Goal | Status | File |
|---|---|---|---|---|
| W01 | walking-skeleton | … | done | [W01](waves/W01-walking-skeleton.md) |
| W01B | auth-foundation | … | done | [W01B](waves/W01B-auth-foundation.md) |
| W02 | user-onboarding | … | active | [W02](waves/W02-user-onboarding.md) |
| W03 | billing | … | planned | [W03](waves/W03-billing.md) |
| W04 | reporting | … | proposed | [W04](waves/W04-reporting.md) |
| W05 | admin-console | … | dropped (D004) | [W05](waves/W05-admin-console.md) |
```

## `decisions.md`

```markdown
## D003: Insert W01B (auth foundation) before W02
- Date: YYYY-MM-DD
- Trigger: W01 review | E04-T02 needs-replan | technical choice | QA waiver (PM)
- Decision: …
- Why: …
- Affects: W01B (new), W02 (amended)
```

## `qa.md`

The QA playbook. The planner writes the requirements in Procedure A and updates the file at each wave review, from the QA reports. The `After` column makes the steps a dependency graph. When a verification skill exists, the steps follow its order: launch, doctor, drive, evidence and cleanup.

```markdown
# ACME: QA playbook

Verification skill: `verify-acme` (or none)

## Requirements
| ID | Requirement | Source |
|---|---|---|
| FR-03 | A new user signs up and lands on the dashboard | [BC §4](00-business-case.md#4-onboarding), SC2 |
| NFR-01 | The dashboard loads in less than 2 s on the QA machine | [BC §7](00-business-case.md#7-constraints) |

## Environments
| Name | Machine | Access | Tools |
|---|---|---|---|
| qa | Dedicated QA host | `ssh qa-host` | `pnpm`, `playwright` |

## Steps
| Step | After | Command or tool | Machine | Expected result |
|---|---|---|---|---|
| prepare | — | `git pull && pnpm install` | qa | exit 0 |
| doctor | prepare | `just doctor` | qa | each check passes |
| start | doctor | `just dev` | qa | `curl -s localhost:3000/health` returns 200 |
| seed | start | `just seed` | qa | 3 test accounts exist |
| FR-03 | seed | `playwright test signup` | qa | the dashboard shows |
| NFR-01 | seed | `hyperfine 'curl -s localhost:3000/dashboard'` | qa | mean < 2 s |
| cleanup | FR-03, NFR-01 | `just stop && just reset-db` | qa | no process on port 3000 |
```
