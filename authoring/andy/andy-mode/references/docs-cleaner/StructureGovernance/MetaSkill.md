---
name: StructureGovernance
description: Repair and normalize documentation-system structure across code, content, workflow, or knowledge systems by fixing frontmatter, indexes, routing tables, taxonomy, navigation, category placement, and cross-reference integrity. USE WHEN the user wants metadata or navigation governance rather than a stale-doc review or deduplication sweep.
---

# StructureGovernance

## When To Use

Use this mode when the main question is whether the documentation system is structurally coherent and navigable.

Typical triggers:

- Fix frontmatter
- Repair indexes or routing tables
- Normalize taxonomy
- Repair broken cross-references or navigation

This mode should produce governance and structural repair decisions, not a stale-doc review and not a deduplication-first cleanup.

Tie-break rule: if the request mixes governance with stale-content cleanup, stay in `StructureGovernance` only when metadata, navigation, or indexing breakage is the immediate blocker. Otherwise start with `DriftRefresh` or `ConsolidationPass` and return here after the content picture is stable.

## Core Method

For a detected Wiki Map boundary, use `references/docs-cleaner/WikiMapStructure.md`. The active Wiki Map schema owns structural rules; the generic method below still applies to other documentation.

1. Define the documentation structure under review.
2. Inspect metadata, indexes, routing paths, taxonomy, and cross-reference integrity.
3. Identify structural inconsistencies, broken navigation paths, and governance violations.
4. Recommend explicit repairs and canonical placements.
5. Call out any content-level cleanup that must happen before or after the structural fix.
6. End with the next recommended step: `DriftRefresh` if content accuracy is still uncertain, `ConsolidationPass` if overlap remains after repair, otherwise finish the governance pass.

## Subject Adaptation Rules

- For code, prioritize README placement, index files, metadata consistency, doc navigation, and canonical reference structure.
- For websites or content systems, prioritize content maps, taxonomy, editorial navigation, ownership markers, and reference linking.
- For PM systems, prioritize process indexes, SOP categorization, automation reference placement, and navigation between operating docs.
- For knowledge systems, prioritize frontmatter, category placement, routing maps, backlinks, hub integrity, and navigation coherence.
- For personal workflows, prioritize dashboard structure, index notes, naming consistency, and reference discoverability.

## Workflow

1. Clarify the structural surface and what currently feels broken.
2. Inspect the highest-value metadata and navigation artifacts.
3. Identify broken or inconsistent structural patterns.
4. Recommend targeted repairs with canonical destinations.
5. Produce a governance brief that can guide the repair pass directly.

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

Within `Findings And Classifications`, prefer explicit labels such as Valid, Repair, Normalize, Reindex, Reroute, or Reclassify.

## Examples

- "Fix the frontmatter and index files in this docs area."
- "Repair the note routing and broken backlinks in this knowledge system."
- "Normalize the taxonomy and navigation for this workflow documentation set."

## Boundaries

- Stay focused on structure, metadata, routing, navigation, and governance.
- Do not turn this into a stale-doc audit when content accuracy is the first blocker.
- Do not turn this into a deduplication sweep when overlap is the first blocker.
- Do not author fresh post-change or artifact docs. If governance work reveals that a canonical doc is missing, recommend it and hand the authoring step off to the `docs` route.
- If the request is really about stale or outdated content, hand off to `DriftRefresh`.
- If the request is really about overlap, redundancy, or dead knowledge, hand off to `ConsolidationPass`.
- If the request is really about discovery, scoping, product definition, technical planning, or implementation, hand off to the adjacent SDLC phase instead of stretching this mode.
