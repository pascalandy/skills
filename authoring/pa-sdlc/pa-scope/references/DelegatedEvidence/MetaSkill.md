---
name: DelegatedEvidence
description: Delegated evidence format for `pa-scope`. USE WHEN scope lenses need read-only investigation before parent scope judgment.
---

# Delegated Evidence

Defines evidence format and parent synthesis rules for delegated `pa-scope` investigation. Dispatch lives in `../../SKILL.md`; canonical routing table lives in `../ROUTER.md`.

Parent `pa-scope` orchestrates and decides. Delegated investigators gather read-only evidence for one lens.

## Principle

Delegation is optional. Use any available safe delegation mechanism only when it improves speed, coverage, or confidence.

Do not delegate trivial scope questions. Stay inline when scope is narrow, evidence is easy, or coordination costs more than it helps.

When delegating, use read-only scope-evidence role, not a runtime-specific role.

## Lens Evidence Source

Each delegated investigator reads assigned lens MetaSkill for evidence focus and subject adaptation. Parent passes absolute or unambiguous path because delegated work may start outside `pa-scope` skill dir. Lens MetaSkill is source of truth for inspection.

| Lens | Skill-relative lens MetaSkill |
|---|---|
| `ChangeSurface` | `references/ChangeSurface/MetaSkill.md` |
| `ImpactTrace` | `references/ImpactTrace/MetaSkill.md` |
| `ArtifactClarifier` | `references/ArtifactClarifier/MetaSkill.md` |
| `ValidationAndRisk` | `references/ValidationAndRisk/MetaSkill.md` |

## Delegated Task Template

Use template for lens-specific evidence gathering. Fill `[LENS]` and `[REQUEST]`.

```text
You are a read-only scope-evidence investigator for `pa-scope`.

Assigned lens: [LENS]
Requested change/question: [REQUEST]

Before investigating, read your lens MetaSkill at this parent-resolved path:
  [ABSOLUTE_OR_UNAMBIGUOUS_PATH_TO_PA_SCOPE]/references/[LENS]/MetaSkill.md

Use the `Evidence Focus` section there to set your investigation
priorities and the `Subject Adaptation` section to tailor the search.

Gather read-only evidence for this lens only.

Return exactly this structure (universal evidence return format):

1. Assigned Lens
2. Findings
3. Evidence
4. Risks And Unknowns
5. Confidence
6. Questions For Parent

Rules:
- stay read-only
- do not edit, create, move, delete, or stage files
- do not run tests, migrations, deploys, or installers
- do not plan implementation
- do not make final product, architecture, implementation, or scope decisions
- do not delegate further
- inspect only enough evidence to answer the assigned lens
- separate facts, inference, assumptions, and unknowns
- cite file/artifact paths when available
- if evidence is weak, say so directly
```

6-section return format applies to all lenses. Lens MetaSkill defines what investigator inspects and how parent synthesizes brief; it does not override return format.

## Parent Synthesis Rules

After delegated evidence returns, parent must:

1. Compare evidence across lenses.
2. Resolve contradictions or label them as unknown.
3. Decide the final scope judgment.
4. Render the final user-facing brief using each lens MetaSkill's `Parent Synthesis Format` section, or the consolidated `Default Parent Output` in `../../SKILL.md` when multiple lenses ran.
5. Recommend the next phase.

Do not paste delegated findings verbatim. Parent owns judgment.
