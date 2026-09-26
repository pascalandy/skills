---
name: pa-scope
description: Universal scoping meta-skill for mapping actual scope before planning or implementation. USE WHEN pa-scope, scope, scoping, change surface, touch surface, blast radius, impact, affected areas, relevant artifacts, validation surfaces, bounded context, scope this change, what is in play, what do I need to touch, what depends on this, what else breaks, does this artifact matter, is this in scope, what should we validate, risks, what could fail.
---

# Scope Router

## Routing

| Request Pattern | Route To |
|---|---|
| scope this change, what is in play, what do I need to touch, affected areas, likely files, relevant artifacts, touch surface, change surface | `ChangeSurface/MetaSkill.md` |
| blast radius, what depends on this, upstream, downstream, dependency chain, propagation path, what else breaks, what else moves, shared contract | `ImpactTrace/MetaSkill.md` |
| does this artifact matter, explain this before changing it, is this file in scope, is this page in scope, is this workflow in scope, is this note in scope, clarify this artifact | `ArtifactClarifier/MetaSkill.md` |
| what should we validate, tests, checks, QA, risks, what could fail, failure modes, operational checks, review checkpoints, validation surfaces | `ValidationAndRisk/MetaSkill.md` |

## Routing Notes

- Apply most specific row first: `ArtifactClarifier`, `ImpactTrace`, `ValidationAndRisk`, then default to `ChangeSurface`
- For compound asks, use every relevant lens; synthesize in parent `pa-scope` response
- `DelegatedEvidence/MetaSkill.md` is internal support (not routable). Load it when a lens needs read-only delegated investigation before parent judgment
- Keep dispatch portable; require no specific assistant runtime, agent home, or subagent implementation
