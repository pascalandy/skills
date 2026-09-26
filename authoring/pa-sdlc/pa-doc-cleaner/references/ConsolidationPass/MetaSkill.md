---
name: ConsolidationPass
description: Reduce redundancy and noise across an existing documentation surface by merging overlap, condensing repetition, and pruning dead knowledge across code, content, workflow, or knowledge systems. USE WHEN the user wants deduplication, overlap reduction, pruning, condensation, or cleanup of repeated documentation rather than a drift audit or metadata repair.
---

# ConsolidationPass

## When To Use

Use this mode when the main question is how to reduce duplication, clutter, or dead weight in an existing documentation surface.

Typical triggers:

- Deduplicate these docs
- Consolidate overlapping notes or guides
- Prune dead knowledge from this section
- Condense repeated documentation

This mode should produce cleanup and merge decisions, not a stale-doc audit and not a structural-governance repair.

Tie-break rule: if the request mixes duplication and staleness, route to `DriftRefresh` first when you still do not know which version is current. Use `ConsolidationPass` once the canonical knowledge is clear enough to merge safely.

## Core Method

1. Define the documentation surface and identify likely canonical sources.
2. Group overlapping documents, sections, or repeated statements.
3. Evaluate each group for unique value versus duplication.
4. Recommend explicit actions such as Keep, Merge, Condense, Archive, or Delete.
5. Call out any structural side effects, such as links or indexes that will need updating.
6. End with the next recommended step: `StructureGovernance` if structural repair is now required, `DriftRefresh` if canonical truth is still uncertain, otherwise finish the consolidation pass.

## Subject Adaptation Rules

- For code, prioritize duplicate setup docs, overlapping architecture notes, repeated runbooks, and redundant reference fragments.
- For websites or content systems, prioritize duplicated editorial guidance, repeated content instructions, and overlapping template references.
- For PM systems, prioritize repeated SOPs, duplicate workflow instructions, and low-signal process artifacts.
- For knowledge systems, prioritize repeated notes, parallel hubs, oversized hub notes, and stale fragments copied across the graph; do not turn this into routing repair unless structure becomes the blocker.
- For personal workflows, prioritize repeated routine notes, duplicate trackers, and fragmented planning references.

## Workflow

1. Clarify the maintenance boundary and the likely canonical centers.
2. Identify overlap clusters.
3. Compare clusters for true uniqueness versus repetition.
4. Recommend merge, condense, archive, or delete actions explicitly.
5. Produce a cleanup brief with before-and-after simplification logic.

## Output Format

Produce these sections:

1. `Maintenance Objective`
2. `Primary Documentation Surface`
3. `Evidence Reviewed`
4. `Findings And Classifications`
5. `Recommended Actions`
6. `Structural Or Cross-Reference Effects`
7. `Risks And Unknowns`
8. `Recommended Next Step`

Within `Findings And Classifications`, prefer explicit labels such as Keep, Merge, Condense, Archive, or Delete.

## Examples

- "Consolidate these overlapping architecture docs."
- "Clean up repeated workflow notes and keep the best version."
- "Prune dead documentation from this knowledge area."

## Boundaries

- Stay focused on duplication, redundancy, and low-signal material.
- Do not decide canonical truth by guesswork when reality is unclear; hand off to `DriftRefresh` first.
- Do not turn this into metadata, index, or routing repair unless structural issues block consolidation.
- Do not expand into repo-wide discovery or fresh documentation authoring.
- If the request is really about frontmatter, indexes, routing, taxonomy, or navigation, hand off to `StructureGovernance`.
- If the request is really about documenting a concrete change, decision, incident, or artifact, hand off to `pa-doc-update`.
- If the request is really about discovery, scoping, product definition, technical planning, or implementation, hand off to the adjacent SDLC phase instead of stretching this mode.
