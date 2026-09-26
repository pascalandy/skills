---
name: DriftRefresh
description: Review existing documentation against current reality and classify what should be kept, updated, replaced, consolidated, or removed across code, content, workflow, or knowledge systems. USE WHEN the user wants a stale-doc audit, a reality-vs-doc review, or a maintenance pass focused on drift rather than deduplication or metadata repair.
---

# DriftRefresh

## When To Use

Use this mode when the main question is whether existing documentation still matches reality.

Typical triggers:

- Refresh these stale docs
- Audit this documentation area against reality
- What should we keep, update, replace, or delete here?
- Review this knowledge area for drift

This mode should produce evidence-backed maintenance classifications, not a deduplication sweep and not a metadata-governance repair.

Tie-break rule: if the request mixes drift and duplication, start with `DriftRefresh` when the truth status of the docs is still uncertain. Only hand off to `ConsolidationPass` after the stale-vs-current picture is clear.

## Core Method

1. Define the documentation surface under review.
2. Identify the strongest evidence for current reality.
3. Compare each important document or section against that reality.
4. Classify findings using explicit actions such as Keep, Update, Replace, Consolidate, or Remove.
5. Call out the most important risks of leaving drift unaddressed.
6. End with the next recommended step: `ConsolidationPass` if overlap cleanup is now needed, `StructureGovernance` if broken metadata or navigation blocks maintenance, otherwise finish the refresh pass.

## Subject Adaptation Rules

- For code, prioritize public behavior, setup instructions, architectural claims, operational steps, and reference accuracy.
- For websites or content systems, prioritize publishing rules, content models, page ownership, editorial guidance, and live-path accuracy.
- For PM systems, prioritize workflow steps, field meanings, automation behavior, ownership, and reporting guidance.
- For knowledge systems, prioritize canonical-note accuracy, hub relevance, taxonomy claims, and navigation assumptions; do not turn this into index repair unless governance problems become the blocker.
- For personal workflows, prioritize routine validity, tracker meaning, current commitments, and sequence accuracy.

## Workflow

1. Clarify the maintenance target and the reality source.
2. Sample or inspect the strongest current evidence.
3. Compare docs to reality at the right level of granularity.
4. Assign concrete maintenance classifications.
5. Produce a refresh brief that can be applied or handed off directly.

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

Within `Findings And Classifications`, prefer explicit labels such as Keep, Update, Replace, Consolidate, or Remove.

## Examples

- "Audit this docs folder and tell me what is stale."
- "Review these process notes against how the workflow works now."
- "Refresh this knowledge area so it matches current reality."

## Boundaries

- Stay focused on reality-vs-doc alignment.
- Do not collapse into duplicate cleanup when the first problem is drift.
- Do not turn this into frontmatter or index repair unless governance breakage blocks the maintenance job.
- Do not create fresh documentation for a new change. If maintenance reveals that a stale artifact should be replaced outright, make that recommendation and hand the authoring step off to `pa-doc-update`.
- If the request is really about cleanup of duplication or dead weight once canonical truth is already clear, hand off to `ConsolidationPass`.
- If the request is really about frontmatter, indexes, routing, taxonomy, or navigation, hand off to `StructureGovernance`.
- If the request is really about discovery, scoping, product definition, technical planning, or implementation, hand off to the adjacent SDLC phase instead of stretching this mode.
