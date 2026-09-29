---
name: "pa-vision"
description: "Use only when explicitly invoked as `pa-vision` before planning."
keywords: ["pa-vision", "vision", "direction", "alignment", "brief", "prd", "direction-check"]
---

# Vision

Explicit entry point: `pa-vision`.

Use Vision to answer one question before planning: where are we going?

`pa-vision` produces a vision artifact. It clarifies direction, target state, value, non-goals, risks, and the recommended next step. It does not own architecture, implementation planning, or implementation.

Synthesize from current conversation, visible repo evidence, and existing agent understanding. Do not run an interview. If evidence is thin but beneficiary, target state, and decision question exist, state assumptions/uncertainty in the artifact. If any anchor is absent or direction is too unclear, stop before export and use (and reload) `$grilling` or ask one blocking question.

## Route

Load `references/ROUTER.md`.

## Use This When

- You need to test whether a direction is worth pursuing.
- You need to make the target state explicit before planning.
- You need a durable brief for settled direction.

## Internal Modes

| Mode | Owns | Use when |
|---|---|---|
| `DirectionCheck` | Direction pressure test | You need a go, revise, defer, or stop recommendation |
| `AlignmentDraft` | Default pre-planning artifact | You need the current state, end state, and pattern choices made explicit |
| `BriefAuthoring` | Durable brief or PRD | The direction is settled and the main job is packaging it cleanly |

## Boundaries

`pa-vision` stops at the vision artifact. The next logical step is usually:

- `architect` when the direction needs system design, structure, trade-offs, or sequencing.
- `figure-it-out` when the direction is settled and needs a concrete implementation plan.
- A separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook when the work is ready to implement.
- `grilling` when the direction is still too vague, conflicted, or assumption-heavy.

| If the real need is... | Use instead |
|---|---|
| bounded current-state evidence before scoping | `pa-scope` |
| identifying what is in play for a change | `pa-scope` |
| designing execution, structure, or sequencing | `architect` |
| converting a settled direction into implementation slices | `figure-it-out` |
| building a simple change or fixing a bug | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |
| stress-testing unclear direction through questions | `grilling` |
| documenting an already-made change, decision, or artifact | `pa-doc-update` |
| refreshing, deduplicating, or repairing existing docs | `pa-doc-cleaner` |

## Default Output

Default to a direction-oriented artifact that makes these easy to find:

1. request or decision
2. current state
3. desired end state
4. key decisions or pattern choices
5. success signals
6. risks and review points
7. recommended next phase

Each mode already defines its own negative-space section (`Anti-Goals` in `DirectionCheck`, `Patterns To Avoid` in `AlignmentDraft`, `Scope And Non-Goals` in `BriefAuthoring`). Whichever section the active mode uses, it must not be empty — naming the trade-offs is where focus lives.

## Export

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-vision` export profile.

- Mandatory when this run produces a direction check, alignment draft, brief, PRD, or charter.

## Workflow

1. Use the current conversation, user request, visible repository/codebase evidence, and any already-gathered context as the source material.
2. Do not run an interview. If the source material has the three direction anchors but is thin, choose a conservative title/slug and mark assumptions or unknowns inside the artifact. If beneficiary, target state, or decision question is absent, stop before export and route to `grilling` or ask one blocking question.
3. Resolve `entry_slug`, `export_dir`, `export_file`, and `export_path` before editing any text.
4. Start from the synthesized context rather than inventing new requirements.
5. Route to the right Vision mode and produce the final vision artifact.
6. Do a light `writer-sk` pass for clarity and concision without softening critique, risks, trade-offs, assumptions, or recommendations.
7. Write the final text to the resolved `export_path`.
8. Only after export, return the folder path, file path, and final slug.

## Supporting References

- `references/vision-lenses.md` — selection of reframing lenses (HMW, First Principles, JTBD, Constraint Injection, Pre-Mortem, Analogous Inspiration, Inversion). Pick one or two that fit the situation; do not run all.
- `references/pressure-test-rubric.md` — value, feasibility, differentiation, assumption audit, decision matrix, and recommendation shape. Primary reference for `DirectionCheck`; secondary sanity pass for `AlignmentDraft` and `BriefAuthoring`.

## Tone

Direct and honest rather than supportive. If a direction is weak, say so with specificity. Push back on vague value claims, unstated assumptions, and scope that is growing instead of sharpening. Adapt vocabulary to the domain in play — product language for software, editorial language for content, workflow language for PM systems, structural language for knowledge systems, and plain first-person language for personal decisions.

## Direction Discipline

Apply these rules while shaping the vision artifact:

- **Simplicity first:** define the smallest clear direction, target state, and non-goals needed for the next phase. Do not invent requirements, features, or success metrics to make the vision feel complete.
- **Surface conflicts, don't average them:** if beneficiary, value, constraints, or source evidence conflict, name the trade-off and recommend a decision path instead of smoothing it over.
- **Read before you write:** inspect relevant conversation context, repo evidence, existing artifacts, and docs before treating current state claims as fact.
- **Success signals verify intent:** success signals should show why the direction matters for the beneficiary, not merely that a deliverable was produced.
- **Fail loud:** mark thin evidence, load-bearing assumptions, unresolved trade-offs, and missing anchors instead of writing confidence-heavy prose.

## Red Flags

Stop and re-route if any of these appear:

- Missing beneficiary, target state, or decision question — stop before export and clarify or route to `grilling`.
- No named beneficiary — "everyone could use this" means the value is unclear.
- Value claim is marginal when treated honestly — a nice-to-have framed as urgent.
- The mode's negative-space section (`Anti-Goals`, `Patterns To Avoid`, or `Scope And Non-Goals`) is empty or generic.
- Load-bearing assumptions exist but have not been named.
- Agreement instead of pressure-test when the direction has real consequences.
- Jumping to `BriefAuthoring` before `DirectionCheck` when the direction is not actually settled.
- Producing a `DirectionCheck` artifact before applying at least one lens from `vision-lenses.md`.

## Verification

Before declaring the vision artifact done:

- [ ] Beneficiary and success signals are concrete, not generic.
- [ ] The mode's negative-space section is populated with real trade-offs.
- [ ] Load-bearing assumptions are named; when the work has real stakes, they are tiered using the rubric.
- [ ] For `DirectionCheck`: at least one lens from `vision-lenses.md` informed the reasoning, and the artifact ends with a Proceed / Revise / Defer / Stop call plus a one-line reason.
- [ ] Artifact is written to the resolved `export_path` before any handoff.

## Rules

- Keep export naming mechanical and separate from the writing pass.
- Thin evidence should produce assumption-explicit artifacts, not confidence-heavy prose.
- Do not ask clarifying questions as part of normal execution; synthesize from existing conversation and codebase understanding, and make uncertainty visible. Ask only one blocking question when a direction anchor is missing.
- Keep the final artifact aligned with the selected Vision mode rather than forcing a single document shape.

## Non-Goals

Vision does not own scoping, architecture, implementation planning, implementation, release documentation, or documentation maintenance.
