---
name: FeedbackCapture
description: Capture durable lessons and feedback from completed work, fixes, and decision outcomes. USE WHEN capture lessons from this fix, what should we remember, capture feedback, what should the agent remember, what should the user remember, lessons from completed work, lessons from execution, what should change next time.
---

# FeedbackCapture

Capture the minimum durable feedback that should influence future work.

Use this mode when the durable object is a lesson from execution: what happened, what it revealed, and what should change next time. If the durable object is the reason behind a decision -- what was chosen, why it was chosen, and what alternatives were rejected -- route to `pa-doc-update/RationaleCapture`.

## Core Principles

1. Keep the feedback specific and reusable.
2. Prefer lessons tied to an actual event, fix, or decision outcome.
3. Separate agent feedback from user feedback when both exist.
4. Remove repetition and soft language.
5. Keep only what should change future behavior.

## Workflow Routing

| Trigger | Workflow |
|---|---|
| Completed work, wrap-up, general lessons | `references/workflows/CaptureFromCompletedWork.md` |
| Fix, bug repair, debugging outcome | `references/workflows/CaptureFromFix.md` |
| Lesson from a decision outcome, tradeoff, or chosen direction after execution | `references/workflows/CaptureFromDecision.md` |
| Final content should be saved in the project | `references/workflows/FinalizeWithWriteDownPostmortem.md` |

## Resource Index

| Resource | Description |
|---|---|
| `references/templates/FeedbackAndLessonsTemplate.md` | Default structure for concise feedback capture |
| `references/examples/FeedbackCaptureExample.md` | Example output |

## Default Output Structure

1. Context
2. Lessons
3. What To Repeat
4. What To Avoid
5. Feedback for the Agent
6. Feedback for the User

## Anti-Patterns

- Writing generic advice detached from the actual work
- Capturing every detail instead of the behavior-changing ones
- Turning a small lesson set into a large narrative postmortem
