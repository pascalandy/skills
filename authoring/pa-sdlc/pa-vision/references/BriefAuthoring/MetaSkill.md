---
name: BriefAuthoring
description: Convert settled Vision decisions into a durable brief, PRD, charter, or requirements document across software, content, workflow, knowledge, or personal domains. USE WHEN the direction is already defined well enough that the main need is packaging it into a reusable artifact for planning, review, or handoff.
---

# BriefAuthoring

## When To Use

Use this mode when the direction is clear enough that the main remaining job is to write the artifact.

Typical triggers:

- Turn this into a PRD.
- Write the feature brief.
- Formalize this direction.
- Create the requirements document.
- Package this into a charter.

This mode should write the right-sized durable artifact, not re-open every strategic decision from scratch.

## Core Method

1. Determine from the current context whether the direction is settled enough to document; if not, state the uncertainty in the artifact rather than asking first.
2. Choose the right artifact weight and shape for the request.
3. Organize the Vision decisions into a durable structure.
4. Make goals, non-goals, success criteria, and open risks explicit.
5. Preserve domain-specific language without assuming everything is software.
6. End with the next recommended phase, usually `architect`.

## Subject Adaptation Rules

- For software, favor feature briefs or PRDs with user stories, acceptance criteria, and constraints.
- For websites or content systems, favor briefs that describe audience, target experience, publishing constraints, and editorial boundaries.
- For PM systems, favor operating briefs that define workflow goals, role expectations, and process success criteria.
- For knowledge systems, favor restructuring briefs that define target information architecture, navigation goals, and governance expectations.
- For personal contexts, favor concise decision briefs or charters with goals, non-goals, constraints, and success signals.

## Workflow

1. Infer the right artifact type from the current conversation and requested outcome; do not interview the user.
2. Reuse the aligned direction and visible evidence instead of re-inventing it.
3. Write the artifact at the smallest weight that still supports planning or handoff.
4. Make measurable criteria and explicit boundaries visible.
5. Highlight remaining open questions instead of smuggling them in as fake certainty.
6. Produce the final brief.

## Output Format

Produce a durable artifact using the smallest structure that fits the request. Most outputs should include:

1. `Overview`
2. `Problem Or Opportunity`
3. `Target Audience Or Stakeholders`
4. `Desired Outcome`
5. `Scope And Non-Goals`
6. `Key Decisions`
7. `Success Criteria`
8. `Risks And Open Questions`
9. `Recommended Next Phase`

When the user explicitly asks for a PRD, include domain-appropriate equivalents of personas, scenarios, requirements, acceptance criteria, and non-goals.

## Examples

- "Turn this alignment into a feature PRD."
- "Write the brief for this website direction so planning can start."
- "Create a one-page charter for this workflow change."

## Boundaries

- Do not use document weight as a substitute for unclear thinking.
- Do not introduce detailed implementation sequencing or file-level plans.
- Do not assume PRD is always the right format; pick the lightest durable artifact that supports the next phase.
- Export the brief artifact before recommending `architect` or any other next phase.
- If the direction itself is still weak or disputed, hand back to `DirectionCheck` or `AlignmentDraft` first.
