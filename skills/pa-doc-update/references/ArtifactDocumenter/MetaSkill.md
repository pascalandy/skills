---
name: ArtifactDocumenter
description: Create or refresh current-state documentation for one concrete artifact across code, content, workflow, or knowledge systems. USE WHEN the user wants a module, component, page, workflow, board, process, note set, or other specific artifact documented as it exists now, not a repo-wide maintenance sweep.
---

# ArtifactDocumenter

## When To Use

Use this mode when one concrete thing needs documentation as it exists now.

Typical triggers:

- Document this module
- Document this workflow as it works today
- Document this page or board
- Create reference docs for this component

This mode should produce current-state artifact documentation, not a release summary and not a rationale-first record.

Tie-break rule: if the request is primarily about a recent change or shipped update, route to `ChangeCapture` first. Use `ArtifactDocumenter` when the user needs a stable current-state explanation of one bounded artifact.

## Core Method

1. Identify the artifact boundary and intended audience.
2. Determine whether the job is create or refresh.
3. Gather evidence for what the artifact currently is, does, depends on, and exposes.
4. Capture interfaces, structure, responsibilities, usage, constraints, and quality-relevant details.
5. Make assumptions and gaps explicit instead of inventing behavior.
6. End with the next recommended step: `ChangeCapture` if this artifact also needs a recent-change summary, `RationaleCapture` if the key missing value is why it was shaped this way, otherwise finish the artifact documentation.

## Subject Adaptation Rules

- For code, prioritize purpose, boundaries, interfaces, dependencies, usage patterns, lifecycle, and operational constraints.
- For websites or content systems, prioritize page purpose, structure, content model, publishing rules, ownership, and update flows.
- For PM systems, prioritize workflow steps, states, fields, automations, ownership, and reporting touchpoints.
- For knowledge systems, prioritize note purpose, canonical status, structure, links, routing role, and usage patterns for the bounded artifact; do not turn this into a governance or index-maintenance sweep.
- For personal workflows, prioritize routine purpose, sequence, triggers, supporting artifacts, and expectations.

## Workflow

1. Clarify the artifact and the documentation target.
2. Determine whether an existing doc should be updated or a new one should be created.
3. Gather the evidence baseline before drafting: inspect the artifact, directly related docs, `git status --short`, `git diff --stat`, and the relevant `git diff` when repository changes affect the artifact; include staged diff when staged changes matter.
4. Check for an existing relevant `postmortem-*.md` artifact, especially under the resolved `sdlc-pa` export root beside related lifecycle artifacts; use it to capture stable lessons, constraints, caveats, and cross-references without turning this mode into a new postmortem.
5. Run the scope gate: if artifact boundaries, dependencies, downstream impact, validation needs, or doc placement are unclear, use (and reload) `$pa-scope` first and carry its judgment into this artifact documentation.
6. Capture the most stable and useful current-state details.
7. Produce the documentation in a grounded, reference-friendly form.

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

When useful, represent responsibilities, dependencies, interfaces, or workflow steps as tables.

## Examples

- "Document this component for future maintainers."
- "Document this board automation as it works today."
- "Write current-state documentation for this publishing workflow."

## Boundaries

- Stay focused on one concrete artifact or tightly related artifact set.
- Run git diff when the work is in a git workspace; if no diff exists, say so and use other explicit evidence.
- Consider existing `postmortem-*.md` artifacts as evidence when they exist; do not create or rewrite postmortems in this mode.
- Use (and reload) `$pa-scope` when artifact boundaries, dependencies, downstream impact, validation surface, or doc placement are unclear; do not guess.
- Do not broaden into whole-system discovery.
- Do not turn this into a release-note summary unless the request is really about a recent change.
- Do not turn this into a rationale artifact unless the why is the real missing piece.
- Do not drift into documentation cleanup, deduplication, or governance work.
- Do not interpret "refresh" as a stale-doc audit or a multi-artifact maintenance pass.
