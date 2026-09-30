---
name: RationaleCapture
description: Capture lightweight rationale for a settled decision across code, content, workflow, or knowledge systems. USE WHEN the user wants an ADR, a decision record, tradeoff documentation, or another artifact centered on decision rationale and consequences. For postmortems, lessons learned, incident reviews, retrospectives, and durable feedback capture, hand off to `pa-postmortem`.
---

# RationaleCapture

## When To Use

Use this mode when the durable object is the reason behind a settled decision: what was chosen, why it was chosen, and what alternatives were rejected.

Typical triggers:

- ADR this
- Record this decision
- Why did we choose this?
- Capture the tradeoffs and consequences

This mode should produce rationale-rich documentation, not a release summary, generic current-state reference, postmortem, incident review, or durable lessons capture. If the durable object is a lesson from execution -- what happened, what it revealed, and what should change next time -- route to `pa-postmortem/FeedbackCapture`.

Entry condition: the decision already exists. `RationaleCapture` documents it after the fact. If the user is still deciding what to do, route to the earlier SDLC phase that owns product definition, planning, or problem-solving. If the request is about lessons, incidents, retrospectives, or completed-session feedback, route to `pa-postmortem`.

## Core Method

1. Identify the decision that needs to be preserved.
2. Gather the motivating context and constraints.
3. Capture the alternatives and tradeoffs when they matter.
4. State the actual conclusion plainly.
5. Record the consequences, risks, and follow-up implications.
6. End with the next recommended step: `ChangeCapture` if shipped-change docs are also needed, `ArtifactDocumenter` if the artifact itself now needs a current-state reference, otherwise finish the rationale capture.

## Subject Adaptation Rules

- For code, prioritize architectural decisions, technical tradeoffs, and follow-up constraints.
- For websites or content systems, prioritize content strategy decisions and UX rationale.
- For PM systems, prioritize process changes and automation decisions.
- For knowledge systems, prioritize taxonomy decisions, routing choices, and note-structure rationale; do not perform index or routing maintenance as part of this mode.
- For personal workflows, prioritize habit decisions, planning tradeoffs, and missed expectations when they explain a settled choice. Route transferable lessons from execution to `pa-postmortem/FeedbackCapture`.

## Workflow

1. Clarify whether this is a decision record, incident review, or lessons-learned capture.
2. Gather the evidence baseline before drafting: inspect the decision context, existing docs, `git status --short`, `git diff --stat`, and the relevant `git diff` when the decision is tied to repository changes; include staged diff when staged changes matter.
3. Check for an existing relevant `postmortem-*.md` artifact, especially under the resolved `sdlc-pa` export root beside related lifecycle artifacts; use it to preserve already-captured lessons, causes, consequences, and follow-ups without turning this mode into a new postmortem.
4. Run the scope gate: if the decision surface, affected artifacts, downstream impact, or canonical placement is unclear, use (and reload) `$blast-radius` first and carry its judgment into this rationale capture.
5. Separate facts from interpretation.
6. Make alternatives, causes, and consequences explicit.
7. Produce the rationale artifact in a durable, reviewable form.

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

Within `Key Content To Capture`, emphasize context, alternatives, rationale, and consequences.

## Examples

- "Record why we chose this approach over the other one."

## Boundaries

- Keep the focus on why, not on documenting every changed surface.
- Run git diff when the work is in a git workspace; if no diff exists, say so and use other explicit evidence.
- Consider existing `postmortem-*.md` artifacts as evidence when they exist; do not create or rewrite postmortems in this mode.
- Use (and reload) `$blast-radius` when the decision surface, downstream impact, validation surface, or doc placement is unclear; do not guess.
- Do not collapse into a changelog or release-note style summary.
- Do not produce generic artifact reference docs unless the user is actually asking for current-state documentation.
- Do not drift into long-term governance or documentation-system maintenance.
- Do not use this mode for postmortems, lessons learned, incident reviews, retrospectives, or durable feedback capture; hand those to `pa-postmortem`.
- Do not use this mode to make the decision, redesign the process, or run the planning work itself.
