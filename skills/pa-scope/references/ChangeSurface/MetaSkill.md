---
name: ChangeSurface
description: Build bounded scope map for requested change. USE WHEN user asks what is in play, which artifacts may need updates, which validation surfaces matter, or where main risks live.
---

# ChangeSurface

ChangeSurface is the default `pa-scope` lens.

Use it to map likely touch surface. Produce bounded scope brief, not full dependency graph or implementation plan.

## Evidence Focus

Investigator, inline or delegated, follows these priorities. Delegated evidence returns 6-section format from `../DelegatedEvidence/MetaSkill.md`.

1. Restate the requested change neutrally.
2. Identify the primary artifacts most likely to bear the change.
3. Identify apparent owning context, capability, domain, or responsibility area.
4. Mark same-context or cross-context.
5. Expand one level to likely adjacent impact.
6. Identify validation surfaces: tests, QA paths, review checkpoints, ops checks, publishing checks, workflow checks.
7. Surface main risks and unknowns.
8. State confidence and what would raise it.

## Subject Adaptation

- Code: feature files, deps, tests, configs, migrations, public interfaces, reference patterns
- Websites/content: pages, templates, models, publishing rules, assets, QA paths
- PM/workflow: boards, statuses, automations, templates, reports, ownership boundaries
- Knowledge: indexes, canonical notes, backlinks, naming conventions, routing docs, source-of-truth conflicts

## Parent Synthesis Format

Parent brief sections. Omit only no-signal sections.

1. `Requested Change`
2. `Primary Scope`
3. `Bounded-Context Fit`
4. `Adjacent Or Potentially Affected Areas`
5. `Relationship Paths`
6. `Validation Surfaces`
7. `Risks And Unknowns`
8. `Confidence`
9. `Recommended Next Step`

Closing trio (`Risks And Unknowns`, `Confidence`, `Recommended Next Step`) required in this order.

## Boundaries

- Stay bounded; avoid full repo/workspace tour
- Prefer likely impact plus evidence over speculative completeness
- Do not write technical plan or implementation sequence
- If evidence is missing, ask parent to deepen investigation or delegate focused evidence gathering
