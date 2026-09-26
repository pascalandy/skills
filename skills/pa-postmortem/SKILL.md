---
name: "pa-postmortem"
description: "Use when the user mentions `pa-postmortem` after completed work or an incident."
keywords: ["pa-postmortem", "postmortem", "lessons-learned", "session-review", "incident-review", "feedback-capture", "reverse-engineer", "blameless", "five-whys", "root-cause"]
---

# PA Postmortem Session

Run a proportional postmortem after a work session, incident, fix, decision, delivery miss, or feedback moment. Route to one focused mode, preserve durable learning only, and export before returning.

## Core Contract

For each postmortem request:

1. Confirm the event or completed work is specific enough to review.
2. Route to exactly one primary mode: `SessionReview`, `IncidentReview`, or `FeedbackCapture`.
3. Gather only the evidence needed for that mode.
4. Separate facts, inference, assumptions, lessons, and follow-up actions.
5. Keep the writeup proportional to the event size and consequence.
6. Preserve blameless language for incidents.
7. Write the final artifact to the resolved export path.
8. Return the artifact path, durable lessons, unresolved unknowns, and recommended next phase.

## Route

Load `references/ROUTER.md` to determine which sub-skill handles the request.

Choose one primary mode:

1. `SessionReview` when the user wants to reverse-engineer a completed conversation or work session into memory types, lessons, fixes, and feedback.
2. `IncidentReview` when a real operational, delivery, project, or process incident needs impact, timeline, causes, and follow-up actions.
3. `FeedbackCapture` when work is done and the durable object is a lesson from execution: what happened, what it revealed, and what should change next time.

If the request combines modes, choose the mode that owns the most durable artifact and mention any secondary material as context instead of producing multiple competing templates.

## The Problem

"Postmortem" can mean different things.

- Sometimes the user wants to reverse-engineer a conversation and preserve what matters.
- Sometimes they need a blameless incident review with impact, timeline, causes, and follow-up actions.
- Sometimes they already finished the work and only want the durable lessons and feedback.

Without routing, these use cases collapse into one vague template: too heavy for small sessions, too weak for real incidents, or too noisy for durable lesson capture.

## Internal Modes

| Mode | Owns | Use when |
|---|---|---|
| `SessionReview` | Reverse-engineering a session | Preserve memory types, lessons, fixes, and feedback from a completed conversation |
| `IncidentReview` | Blameless incident review | Real operational or delivery incident needs impact, timeline, causes, and follow-ups |
| `FeedbackCapture` | Durable lessons from completed work | The durable object is a lesson from execution: what happened, what it revealed, and what should change next time |

## Proportional Capture Rule

Use the smallest artifact that preserves the durable lesson.

Do not run `pa-postmortem` merely because work completed. Run it only when the event reveals lessons, incidents, execution feedback, repeated mistakes, process gaps, or decisions that should change future work.

- Tiny run: use a compact `FeedbackCapture` with 3-7 bullets when a small lesson should survive future sessions.
- Normal completed work: use concise `FeedbackCapture` or `SessionReview`, depending on whether the durable object is a lesson or a reconstructed session.
- Incident, outage, rollback, or delivery failure: use `IncidentReview`; choose quick or standard depth based on impact.

## Postmortem Discipline

Apply these rules while preserving lessons:

- **Simplicity first:** use the smallest artifact that preserves the durable lesson. Do not inflate completion notes into incident reviews.
- **Surface conflicts, don't average them:** when timelines, recollections, logs, or outcomes disagree, record the conflict and confidence instead of writing a blended story.
- **Read before you write:** inspect the conversation, diff, artifacts, logs, validation, and explicit feedback needed for the selected mode.
- **Lessons verify intent:** lessons and follow-ups should explain what should change next time, not merely that work happened.
- **Fail loud:** do not invent root causes, hide skipped evidence, erase uncertainty, or present incomplete follow-up ownership as resolved.

## What's Included

| Component | Path | Purpose |
|---|---|---|
| Skill router | `references/ROUTER.md` | Minimal routing table for postmortem requests |
| SessionReview skill | `references/SessionReview/MetaSkill.md` | Reverse-engineer conversations and work sessions |
| SessionReview references | `references/SessionReview/references/` | Workflows, template, rubric, and example |
| IncidentReview skill | `references/IncidentReview/MetaSkill.md` | Blameless incident review and root-cause analysis |
| IncidentReview references | `references/IncidentReview/references/` | Workflows, template, and example |
| FeedbackCapture skill | `references/FeedbackCapture/MetaSkill.md` | Capture durable lessons and feedback from completed work |
| FeedbackCapture references | `references/FeedbackCapture/references/` | Workflows, template, and example |

Resolve these paths relative to this skill directory. Do not hardcode an agent-specific install root.

## Invocation Scenarios

| Trigger | What Happens |
|---|---|
| "reverse engineer what we did together" | Routes to `SessionReview` |
| "what is worth remembering from this session" | Routes to `SessionReview` |
| "write a blameless postmortem for this outage" | Routes to `IncidentReview` |
| "do a quick postmortem on this incident" | Routes to `IncidentReview` |
| "run 5 whys on this failure" | Routes to `IncidentReview` |
| "capture lessons from this fix" | Routes to `FeedbackCapture` |
| "what feedback should the agent remember next time" | Routes to `FeedbackCapture` |

## Boundaries

| If the real need is... | Use instead |
|---|---|
| capturing a rough idea | `pa-idea` |
| deciding whether the direction is right | `pa-vision` |
| bounded current-state evidence or blast-radius mapping | `pa-scope` |
| designing execution, structure, or sequencing | `architect` or `figure-it-out` |
| building the change or fixing a bug | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |
| user-facing QA finding capture | `pa-qa` |
| documenting an already-made change, artifact, or decision rationale without lessons analysis | `pa-doc-update` |
| refreshing, deduplicating, or repairing existing docs | `pa-doc-cleaner` |

## Default Output

Route to one primary mode, then use that mode's output contract. In all modes, make these easy to find:

1. what happened
2. what was learned
3. what should be remembered
4. follow-up actions or feedback
5. evidence, assumptions, and unknowns
6. recommended next phase or owner

## Export

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-postmortem` export profile.

- Mandatory when this run produces a session review, incident review, or feedback capture artifact.
- Resolve `entry_slug`, `export_dir`, `export_file`, and `export_path` before editing the final artifact.
- Write the final artifact before returning the summary.

## Workflow

1. Use the user's remaining input, current conversation, visible repository evidence, and any named artifacts as source material.
2. If the event, session, or completed work is missing or too thin to title, ask one short question.
3. Resolve `entry_slug`, `export_dir`, `export_file`, and `export_path` before editing the final artifact.
4. Load `references/ROUTER.md` and choose one primary mode.
5. Load the selected mode's `MetaSkill.md` and only the references needed for the selected mode.
6. Build the evidence baseline from available facts: conversation history, git diff/status when relevant, logs or timelines when supplied, completed artifacts, and explicit user feedback.
7. Draft the postmortem using the selected mode's output contract.
8. Use (and reload) `$simple-editor` to clean the artifact while preserving facts, chronology, user voice, and blameless framing.
9. Use (and reload) `$writer-sk` for clarity and concision without weakening lessons learned, follow-up actions, incident nuance, or feedback signal.
10. Write the final artifact to the resolved `export_path`.
11. Return the folder path, file path, final slug, unresolved unknowns, and recommended next phase.

## Quality Gate

Before returning, confirm:

- The selected mode matches the user's real request.
- The artifact is proportional to the event size and consequence.
- Facts, inference, assumptions, and unknowns are not collapsed together.
- Lessons are durable and actionable, not generic advice.
- Follow-up actions have an owner or clear next phase when possible.
- Incident language is blameless and avoids personal fault framing.
- The artifact was written to the resolved `export_path`.

## Rules

- Keep export naming mechanical and separate from the writing pass.
- Keep the final artifact aligned with the selected Postmortem mode rather than forcing a single document shape.
- Preserve blameless language for incidents.
- Keep session reviews grounded in what actually happened.
- Capture only durable lessons, not every detail.
- Prefer concise artifacts; expand only when impact, complexity, or stakeholder need justifies it.
- Treat quick capture as a compact `FeedbackCapture`, not as a separate mode.

## Anti-Patterns

Do not:

- produce a generic postmortem template without routing to a mode
- inflate a small session into an incident review
- reduce a real incident to vague lessons without timeline, impact, causes, and follow-up actions
- blame individuals instead of describing system, process, communication, or decision failures
- invent root causes without evidence
- bury uncertainty behind confident prose
- capture every detail when only transferable learning matters
- create multiple overlapping artifacts when one primary mode can own the result
- skip export when the run produces a postmortem artifact

## Non-Goals

Postmortem does not own discovery, scoping, product direction, execution planning, implementation, QA, or documentation maintenance.
