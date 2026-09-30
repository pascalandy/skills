---
name: ChangeCapture
description: Capture what changed while context is fresh across code, content, workflow, or knowledge systems. USE WHEN the user wants post-change documentation such as release notes, changelog updates, solved-problem writeups, shipped-change summaries, or documentation synchronized to a concrete delivered change.
---

# ChangeCapture

## When To Use

Use this mode when the user wants documentation tied to a concrete recent change.

Typical triggers:

- Update the docs for this change
- Capture this fix
- Write release notes
- Update the changelog
- Sync docs with what shipped

This mode should produce change-grounded documentation, not a decision record and not a generic artifact reference.

Tie-break rule: if the request is about what changed recently, stay in `ChangeCapture` even when one artifact is central. Only hand off to `ArtifactDocumenter` when the user actually needs durable current-state documentation for that artifact.

## Core Method

1. Restate the concrete change in neutral terms.
2. Identify the strongest evidence for what changed.
3. Determine which documentation target should carry that change.
4. Extract the key behavior, interface, workflow, or operational updates worth preserving.
5. Call out any important omissions, caveats, or follow-up documentation gaps.
6. End with the next recommended step: `RationaleCapture` if the why must also be preserved, `ArtifactDocumenter` if one changed artifact needs deeper current-state docs, otherwise finish the change capture.

## Subject Adaptation Rules

- For code, prioritize shipped behavior, public interfaces, configs, tests, migration notes, and solved-problem context.
- For websites or content systems, prioritize page changes, template updates, content model changes, publishing behavior, and editorial guidance.
- For PM systems, prioritize workflow changes, automation changes, field semantics, ownership changes, and reporting impact.
- For knowledge systems, prioritize canonical note updates, new reference material, changed navigation expectations, and newly captured learnings that already happened; do not turn this into index repair or governance maintenance.
- For personal workflows, prioritize updated routines, trackers, commitments, or reflection notes tied to the concrete change.

## Workflow

1. Clarify what changed and why this documentation is needed now.
2. Gather the evidence baseline before drafting: inspect the changed artifact, existing docs, `git status --short`, `git diff --stat`, and the relevant `git diff`; include staged diff when staged changes matter.
3. Check for an existing relevant `postmortem-*.md` artifact, especially under the resolved `sdlc-pa` export root beside related lifecycle artifacts; use it to preserve lessons, risks, follow-ups, and cross-references without turning this mode into a new postmortem.
4. Run the scope gate: if affected surfaces, blast radius, validation needs, or canonical doc placement are unclear, use (and reload) `$blast-radius` first and carry its judgment into this change capture.
5. Identify the most appropriate canonical target.
6. Capture only the meaningful change, not every surrounding detail.
7. Produce the update in a form that can be applied or handed off directly.

## Output Format

Produce these sections:

1. `Documentation Objective`
2. `Primary Target`
3. `Evidence Used`
4. `Key Content To Capture`
5. `Canonical Placement Or Output Shape`
6. `Cross-References And Dependencies`
7. `Risks And Unknowns`
8. `Recommended Next Step`

When useful, represent `Key Content To Capture`, `Canonical Placement Or Output Shape`, and `Cross-References And Dependencies` as tables.

## Examples

- "Capture what changed after this bug fix."
- "Write the post-ship documentation for this release."
- "Update the docs to match the workflow we just changed."

## Boundaries

- Stay tied to a concrete recent change.
- Run git diff when the work is in a git workspace; if no diff exists, say so and use other explicit evidence.
- Consider existing `postmortem-*.md` artifacts as evidence when they exist; do not create or rewrite postmortems in this mode.
- Use (and reload) `$blast-radius` when the touched surface, downstream impact, validation surface, or doc placement is unclear; do not guess.
- Do not turn this into a full rationale artifact unless the why is the main job.
- Do not turn this into a current-state reference for one artifact unless that deeper artifact documentation is actually needed.
- Do not drift into cleanup, deduplication, or documentation-system maintenance.
