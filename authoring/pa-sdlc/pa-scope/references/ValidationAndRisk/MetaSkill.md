---
name: ValidationAndRisk
description: Identify validation surfaces, checks, failure modes, and risky unknowns. USE WHEN user asks what to validate, where risk lives, what could fail, or which tests/checks/review paths matter.
---

# ValidationAndRisk

ValidationAndRisk is the verification and failure-mode lens inside `pa-scope`.

Use when question is less "what changes?" and more "how do we know this is safe?"

## Evidence Focus

Investigator, inline or delegated, follows these priorities. Delegated evidence returns 6-section format from `../DelegatedEvidence/MetaSkill.md`.

1. Restate the requested change neutrally.
2. Identify behavior, contracts, workflows, or artifacts that must stay true.
3. Find validation surfaces: tests, QA paths, review checkpoints, ops checks, publishing checks, workflow checks, or monitoring signals.
4. Identify likely failure modes.
5. Separate must-check surfaces from nice-to-check surfaces.
6. State evidence quality.
7. State confidence and what would raise it.

## Subject Adaptation

- Code: existing tests, missing test seams, public interfaces, configs, migrations, APIs, jobs, integration points
- Websites/content: preview paths, publishing checks, templates, content models, navigation, assets, accessibility, regression-prone pages
- PM/workflow: status transitions, automations, reports, handoffs, permission boundaries, recurring process checks
- Knowledge: canonical sources, indexes, backlinks, redirects, duplicate sources, naming conventions, retrieval paths

## Parent Synthesis Format

Parent validation-first brief sections. Omit only no-signal sections.

1. `Requested Change`
2. `Must-Validate Surfaces`
3. `Useful Secondary Checks`
4. `Likely Failure Modes`
5. `Evidence`
6. `Risks And Unknowns`
7. `Confidence`
8. `Recommended Next Step`

Closing trio (`Risks And Unknowns`, `Confidence`, `Recommended Next Step`) required in this order.

## Boundaries

- Do not write implementation plan
- Do not run fixes or mutate files
- Do not invent checks; label speculative checks as assumptions
- Do not require exhaustive validation when focused check answers scope question
