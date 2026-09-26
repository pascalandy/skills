---
name: DelegatedEvidence
description: Portable delegated-work and evidence contract for non-trivial `pa-code-review` lens investigations. Use when one or more review lenses need read-only investigation before the parent makes the final readiness judgment.
---

# Delegated Evidence Contract

This file defines the portable investigator task template and parent synthesis rules for `pa-code-review`. It does not require any specific agent runtime. Routing guidance lives in `../ROUTER.md` and is not duplicated here.

The parent `pa-code-review` skill remains the workflow owner and final decision-maker. Inline or delegated investigators gather read-only evidence for one assigned lens.

## Investigator Role

An investigator may be the parent working inline, another model/agent, a teammate, or a runtime-specific adapter. Regardless of implementation, the role is the same:

- inspect only the assigned lens
- gather concrete, read-only evidence
- separate facts, inference, assumptions, and unknowns
- return an evidence brief
- never edit files or make the final readiness decision

Runtime-specific adapters may live outside this portable skill directory. They must implement this contract rather than changing the parent workflow.

## Lens Evidence Source

Every investigator reads the assigned lens MetaSkill for evidence focus and lens-specific adaptation. The parent should provide an absolute or otherwise unambiguous path when delegation happens outside the skill directory.

| Lens | Skill-relative lens MetaSkill |
|---|---|
| `Correctness` | `references/Correctness/MetaSkill.md` |
| `Testing` | `references/Testing/MetaSkill.md` |
| `Maintainability` | `references/Maintainability/MetaSkill.md` |
| `ProjectStandards` | `references/ProjectStandards/MetaSkill.md` |
| `Security` | `references/Security/MetaSkill.md` |
| `ApiContract` | `references/ApiContract/MetaSkill.md` |
| `Reliability` | `references/Reliability/MetaSkill.md` |
| `CliReadiness` | `references/CliReadiness/MetaSkill.md` |

## Investigator Task Template

Use this template when assigning a delegated investigator. Fill in `[LENS]`, `[REQUEST]`, `[SCOPE]`, and `[INTENT]`.

````text
You are a read-only code review investigator for `pa-code-review`.

Assigned lens: [LENS]
User request: [REQUEST]
Review scope: [SCOPE]
Implementation intent: [INTENT]

Before investigating, read your lens MetaSkill at this parent-resolved path:
  [ABSOLUTE_OR_UNAMBIGUOUS_PATH_TO_PA_CODE_REVIEW]/references/[LENS]/MetaSkill.md

Use the `Investigator Evidence Focus` section there to set your investigation priorities and the `Subject Adaptation` section to tailor the search.

Gather read-only evidence for this lens only.

Return exactly this Markdown structure:

```md
## Code Review Evidence Brief

### Assigned Lens

### Scope Inspected

### Findings

For each finding:
- Severity:
- Title:
- Evidence:
- Why It Matters:
- Recommended Next Step:
- Confidence:

### Evidence

### Tests Or Checks Considered

### Risks And Unknowns

### Confidence

### Questions For Parent
```

Finding format:
- Severity: P0, P1, P2, or P3
- Title
- Evidence: concrete file paths, symbols, commands, or diff hunks when available
- Why it matters
- Recommended next step
- Confidence: High, Medium, or Low

Rules:
- stay read-only
- do not edit, create, move, delete, format, apply, stage, commit, install, migrate, deploy, or fix files
- use shell/terminal commands only for read-only inspection such as pwd, ls, find, rg, grep, git status, git diff, git log, dependency/test discovery, and explicitly safe read-only checks
- do not run tests unless the parent explicitly asked for read-only test execution and project rules allow it
- do not make the final readiness decision
- do not delegate further
- inspect only enough evidence to answer the assigned lens
- separate facts, inference, assumptions, and unknowns
- cite file paths when available
- if evidence is weak, say so directly
````

The Markdown evidence-brief return format is universal across all lenses. The lens MetaSkill defines what the investigator inspects; it does not override the return format.

## Parent Synthesis Rules

After inline and/or delegated evidence is gathered, the parent must:

1. Compare evidence across lenses.
2. Merge duplicate findings and preserve the highest justified severity.
3. Resolve contradictions or label them as unknown.
4. Separate facts, inference, assumptions, and unknowns.
5. Decide the final readiness verdict.
6. Render the final user-facing report using the `Review Record` in `../../SKILL.md`.
7. Recommend whether to proceed to `/pa-qa`, return to the selected implementation workflow, or stop for clarification.

Do not paste investigator findings verbatim. The parent owns judgment.
