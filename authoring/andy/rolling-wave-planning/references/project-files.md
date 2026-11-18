# Project files

Read this file before you write `01-project.md` or `decisions.md`.

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
- QA machine: Mac Mini

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
