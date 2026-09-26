---
name: SessionReview
description: Reverse-engineer a completed conversation or work session into structured memories, lessons, discoveries, fixes, and feedback. USE WHEN reverse engineer the session, review what we did together, what is worth remembering, classify memories, postmortem our conversation, lessons from this session.
---

# SessionReview

Turn a completed conversation or work session into a durable postmortem focused on what is worth remembering.

## Core Principles

1. Reconstruct what actually happened before extracting lessons.
2. Keep only durable memories, not every turn of the conversation.
3. Use the memory taxonomy consistently.
4. Separate lessons, discoveries, fixes, and feedback.
5. Do not invent intent, rationale, or failures that are not supported by the session.

## Workflow Routing

| Trigger | Workflow |
|---|---|
| "reverse engineer what we did together", "reconstruct the session" | `references/workflows/ReverseEngineerConversation.md` |
| "classify the memories", "what memory type is this" | `references/workflows/ClassifyMemoryTypes.md` |
| "what did we learn", "what went wrong", "feedback for agent or user" | `references/workflows/ExtractLessonsFixesFeedback.md` |
| Final content should be saved in the project | `references/workflows/FinalizeWithWriteDownPostmortem.md` |

## Resource Index

| Resource | Description |
|---|---|
| `references/templates/SessionReviewTemplate.md` | Default structure for a full session postmortem |
| `references/templates/MemoryTypeRubric.md` | Definitions for the memory types |
| `references/examples/SessionReviewExample.md` | Example output |

## Output Structure

Default shape:

1. What We Did
2. Elements Worth Remembering
3. What Went Wrong
4. What We Discovered
5. Fixes Applied
6. Feedback for the Agent
7. Feedback for the User

Within `Elements Worth Remembering`, label each entry with a `MEMORY TYPE`.

## Anti-Patterns

- Turning the result into a full incident report when the source is just a work session
- Listing every message instead of keeping only durable memories
- Mixing observations, errors, and decisions without labels
- Saving draft content before the postmortem is actually final
