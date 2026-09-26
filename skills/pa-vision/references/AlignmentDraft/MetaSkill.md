---
name: AlignmentDraft
description: Create the default pre-planning alignment artifact that externalizes current state, desired end state, design decisions, and pattern choices across software, content, workflow, knowledge, or personal domains. USE WHEN the user wants to make the direction explicit before planning, review the agent's proposed patterns, or correct stale defaults before implementation is designed.
---

# AlignmentDraft

## When To Use

Use this mode for the default Vision job once the direction is plausible and the next need is alignment before planning.

Typical triggers:

- Here is where we're going.
- Write down the direction before we plan it.
- Dump your understanding of the current state and target state.
- Show me the proposed patterns before we commit.
- Make the end state explicit so I can correct it.

This mode should produce the canonical pre-planning Vision artifact. For substantial work, that artifact can be fairly rich. For smaller work, it should stay compact.

## Core Method

1. Restate the initiative or decision in neutral terms.
2. Summarize the current state from visible evidence and explicit assumptions.
3. Describe the desired end state clearly enough that planning does not need to invent the destination.
4. Surface the proposed behavior, pattern choices, and design decisions.
5. Explicitly separate patterns to follow from patterns to avoid.
6. Identify what requires human review before planning starts.
7. End with the next recommended phase, usually `architect` if alignment is accepted.

## Why This Mode Exists

This mode makes the agent externalize its understanding before planning starts. It should synthesize the current conversation and visible repository/codebase evidence, not run a clarification interview.

That creates an explicit alignment conversation by default instead of relying on hidden assumptions or magic phrasing. If the agent proposes a stale, legacy, or rejected pattern, the human can correct it here before the plan calcifies around the wrong architecture or workflow.

## Subject Adaptation Rules

- For software, prioritize current behavior, target behavior, architectural standards, integration expectations, and rejected legacy patterns.
- For websites or content systems, prioritize current experience, target experience, editorial rules, publishing implications, and content-model decisions.
- For PM systems, prioritize current workflow, target workflow, role boundaries, automation expectations, and policies to avoid.
- For knowledge systems, prioritize current structure, target structure, navigation patterns, taxonomy decisions, and anti-patterns.
- For personal contexts, prioritize current routine or decision context, target state, constraints, principles, and commitments to avoid violating.

## Workflow

1. Infer the initiative from the current conversation and already-visible evidence; do not interview the user.
2. Write a compact current-state synthesis, naming assumptions or missing evidence where needed.
3. Write the desired end state in concrete terms.
4. Surface key design decisions and pattern choices.
5. Separate approved patterns from patterns to avoid.
6. Mark the assumptions or decisions that need human confirmation.
7. Produce the alignment artifact.

## Output Format

Produce these sections:

1. `Request Or Decision`
2. `Current State`
3. `Observed Constraints`
4. `Desired End State`
5. `Proposed Interaction Or Behavior`
6. `Design Decisions`
7. `Patterns To Follow`
8. `Patterns To Avoid`
9. `Success Signals`
10. `Open Questions And Risks`
11. `What Needs Human Review`
12. `Recommended Next Phase`

When the work is substantial, this artifact may be longer and more detailed. When the work is small, compress sections aggressively rather than adding filler.

## Examples

- "Write the alignment draft for this feature before we plan it."
- "Show me your proposed target state and standards for this content-system change."
- "Brain dump where this process redesign is going so I can correct the direction."

## Boundaries

- Do not turn this into implementation sequencing, task breakdown, or rollout planning.
- Do not hide pattern choices. Surface them explicitly so the human can correct them.
- Do not generate a heavyweight PRD by default unless the user asks for a formal artifact.
- Export the alignment artifact before recommending `BriefAuthoring`, `architect`, or any other next phase.
- If the main question is still whether the direction is worth doing, hand off to `DirectionCheck`.
- If the direction is settled and the user wants a formal deliverable, hand off to `BriefAuthoring`.
