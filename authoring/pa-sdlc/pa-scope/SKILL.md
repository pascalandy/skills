---
name: "pa-scope"
description: "Use only when explicitly invoked as `pa-scope`."
kind: "general"
keywords: ["pa-scope", "scope", "scoping", "change-surface", "touch-surface", "blast-radius", "impact", "affected-areas", "validation-surfaces", "bounded-context"]
---

# Scope

Explicit entry point: `pa-scope`.

Use Scope before planning or implementation to answer:

> What is actually in play for this requested change?

## Core Contract

For each scoping request:

1. Restate the requested change or artifact question in user-facing terms.
2. Select only the scope lens or lenses needed for the judgment.
3. Inspect enough evidence to identify the primary surface, adjacent impact, validation surface, risks, and unknowns.
4. Separate confirmed facts, inference, assumptions, and unresolved questions.
5. Produce a bounded scope judgment that names what is in scope, what is adjacent, and what is intentionally not resolved here.
6. Recommend the next `pa-sdlc` phase without turning scope work into planning, implementation, documentation cleanup, or domain modeling.

## Routing

Load `references/ROUTER.md` to choose scope lens. Resolve `references/...` paths relative to this skill directory; do not hardcode agent-specific install roots.

Choose one primary lens for simple reqs. Use multiple lenses only when concerns combine or risk needs broader judgment. Choose the smallest lens set that can answer the scope question; add another lens only when it can change the next `pa-sdlc` move.

## Workflow

`pa-scope` owns scope judgment:

1. Restate the request.
2. Classify the scope question.
3. Select scope lenses.
4. Choose inline or delegated investigation.
5. Gather evidence per lens.
6. Compare evidence across lenses.
7. Separate facts, inference, assumptions, and unknowns.
8. Write the scope judgment.
9. Recommend the next phase.

### Depth Budget

Stop scoping when the primary surface, adjacent risks, validation surfaces, and confidence are sufficient to recommend the next `pa-sdlc` move.

Do not continue mapping the repository for completeness. If more certainty is required, name the missing evidence and route to the next appropriate skill instead of expanding discovery.

### Scoping Discipline

Apply these rules while mapping the change surface:

- **Simplicity first:** select the smallest lens set and evidence pass that can support the next SDLC move.
- **Surgical changes:** scope only the requested change and necessary adjacent surfaces. Do not turn scoping into cleanup, refactoring, or repository mapping.
- **Surface conflicts, don't average them:** when docs, code, tests, or user reports disagree, report the conflict and identify the strongest evidence or the owner decision needed.
- **Read before judging scope:** inspect source-of-truth artifacts, exports, callers, shared utilities, tests, docs, and conventions relevant to the claimed surface before labeling impact as confirmed.
- **Validation verifies intent:** recommend checks that prove the scoped behavior, contract, or risk that matters, not generic test commands unrelated to the surface.
- **Checkpoint after significant evidence:** before recommending the next phase, restate confirmed scope, inferred scope, unknowns, validation surfaces, and confidence.
- **Match project conventions:** use the repository's naming, architecture, documentation, and workflow boundaries when describing touch surfaces.
- **Fail loud:** explicitly name uncertain impact, missing evidence, unavailable checks, and scope questions that cannot be answered from the repo.

### Optional Delegation

Use delegated investigators only when they help. `pa-scope` still owns final scope judgment.

When delegated by a parent workflow, follow its assignment scope and handoff contract. Do not launch nested subagents unless the parent explicitly authorizes them.

## Scope Lenses

| Lens | Use when | Trigger phrases |
|---|---|---|
| `ChangeSurface` | User asks what is in play, what needs touching, or which files/artifacts/workflows are affected | scope this change, what is in play, what do I need to touch, affected areas, likely files, relevant artifacts |
| `ImpactTrace` | User starts from known artifact and asks blast radius, deps, upstream/downstream impact, or breakage | blast radius, what depends on this, upstream/downstream, dependency chain, propagation path, what else breaks, what else moves |
| `ArtifactClarifier` | User asks whether one file, page, workflow, note, board, or artifact belongs in scope | does this artifact matter, explain this before changing it, is this file/page/workflow/note in scope, clarify this artifact |
| `ValidationAndRisk` | User asks what to validate, where risks live, what checks matter, or what could fail | what should we validate, tests/checks/QA, risks, what could fail, operational checks, review checkpoints |

For combined patterns, investigate each required lens inline or delegate one read-only investigator per lens when delegation is authorized. Parent synthesizes.

## Use This When

- Find likely touch surface for a requested change
- Identify artifacts, files, workflows, pages, notes, or validation surfaces in play
- Trace upstream/downstream impact or blast radius from known artifact
- Decide whether one artifact belongs in scope
- Gather bounded current-state evidence before planning

## Do Not Use This When

| If the real need is... | Use instead |
|---|---|
| deciding whether the direction is right | `pa-vision` |
| designing execution, sequencing, or architecture | `architect` or `figure-it-out` |
| building the change or debugging a failure | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |
| documenting a concrete outcome or artifact | `pa-doc-update` |
| refreshing, deduplicating, or repairing existing docs | `pa-doc-cleaner` |
| resolving a domain, vocabulary, or ownership boundary | `pa-glossary` |

## Dispatch Policy

`references/ROUTER.md` is canonical for lens selection. This section covers orchestration depth only.

### Trivial / Inline

Answer directly when all are true:

- no repo, workspace, or artifact inspection needed
- scope is obvious from current context
- no likely shared contract, ownership boundary, cross-context impact, or validation uncertainty

Use compact output:

1. `Requested Change`
2. `Likely Scope`
3. `Validation`
4. `Unknowns`
5. `Recommended Next Step`

### Standard

One lens via ROUTER. Default inline. Delegate only when evidence is non-trivial and read-only investigation helps.

### Multi-Lens

Combined concerns use multiple lenses. Investigate inline or delegate independent lenses in parallel when delegation is authorized.

Examples:

- "scope this change and tell me blast radius" -> `ChangeSurface` + `ImpactTrace`
- "does this file matter, and what else would it affect?" -> `ArtifactClarifier` + `ImpactTrace`
- "what is in play and how should we validate it?" -> `ChangeSurface` + `ValidationAndRisk`

### Deep

Default deep set for high-risk, cross-context, uncertain, or explicitly deep scoping:

1. `ChangeSurface`
2. `ImpactTrace`
3. `ValidationAndRisk`

Add `ArtifactClarifier` only for a named ambiguous artifact.

## Default Parent Output

For multi-lens or delegated scope:

1. `Requested Change`
2. `Scope Lenses Used`
3. `Primary Scope`
4. `Adjacent / Downstream Impact`
5. `Validation Surfaces`
6. `Risks And Unknowns`
7. `Confidence`
8. `Evidence`
9. `Recommended Next Step`

Add only when useful:

- `Bounded-Context Fit`
- `Relationship Paths`
- `Scope Judgment`
- `Questions / Assumptions`

Do not paste raw delegated output. Parent owns judgment.

## Bounded-Context Check

Include bounded-context analysis only with evidence of domain, ownership, public interface, shared contract, handoff, schema, workflow boundary, or cross-context impact.

Scope may flag boundary, vocabulary, or ownership problems, but does not resolve them. If needed, recommend `pa-glossary`, `architect`, or dedicated domain modeling.

## Anti-Patterns

Do not:

- turn bounded scoping into broad discovery or repository mapping
- keep mapping the repository after enough evidence exists for the next SDLC move
- select every lens when one primary lens is enough
- delegate investigation when inline evidence is sufficient
- paste raw delegated findings instead of synthesizing a parent-owned judgment
- present inferred blast radius as confirmed impact without evidence
- confuse likely touch surface with an implementation plan or task list
- resolve product direction, architecture, ownership, or terminology decisions inside `pa-scope`
- recommend validation checks that are unrelated to the scoped surface
- omit uncertainty when the affected surface, dependencies, or validation path are not yet known
- export a durable artifact unless the user asks for a reusable scope map or blast-radius artifact

## Export

Default to chat. Export only when user asks for reusable scope map or blast-radius artifact. Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-scope` export profile.

## Non-Goals

Scope does not own product direction, architecture, sequencing, implementation, debugging, doc maintenance, or onboarding. Discovery only supports bounded scope judgment.
