---
name: IncidentReview
description: Write a blameless postmortem for an incident, outage, failure, or rollback. Includes standard, quick, and 5 Whys workflows. USE WHEN blameless postmortem, incident review, outage review, rollback postmortem, 5 whys, quick postmortem, incident timeline, contributing factors.
---

# IncidentReview

Write a blameless incident postmortem with the right amount of rigor for the event size.

## Core Principles

1. Focus on systems and conditions, not blame.
2. State impact clearly.
3. Separate root cause from contributing factors.
4. Prefer factual timelines over narrative spin.
5. Keep action items concrete and owned when ownership exists.

## Workflow Routing

| Trigger | Workflow |
|---|---|
| Full blameless review, outage, rollback, incident writeup | `references/workflows/StandardPostmortem.md` |
| "run 5 whys", "root cause chain" | `references/workflows/FiveWhys.md` |
| "quick postmortem", "lightweight incident review" | `references/workflows/QuickPostmortem.md` |
| Final content should be saved in the project | `references/workflows/FinalizeWithWriteDownPostmortem.md` |

## Resource Index

| Resource | Description |
|---|---|
| `references/templates/IncidentPostmortemTemplate.md` | Default structure for incident reviews |
| `references/examples/IncidentExample.md` | Example output |

## Default Output Structure

1. Summary
2. Impact
3. Timeline
4. Root Cause
5. Contributing Factors
6. Detection and Response
7. Fixes Applied
8. Follow-up Actions

## Anti-Patterns

- Naming a person as the root cause
- Skipping impact because the failure was short-lived
- Mixing assumptions into the timeline without marking them
- Writing action items that are vague or not testable
