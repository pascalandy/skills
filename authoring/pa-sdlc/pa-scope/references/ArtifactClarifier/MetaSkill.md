---
name: ArtifactClarifier
description: Explain one artifact in context so parent can include or exclude it from scope. USE WHEN one file, module, page, workflow, board, note, or document is ambiguous and scope depends on understanding it.
---

# ArtifactClarifier

ArtifactClarifier resolves one ambiguity around one artifact or tight area.

Use when question is "does this belong in scope?", not "what is whole scope?"

## Evidence Focus

Investigator, inline or delegated, follows these priorities. Delegated evidence returns 6-section format from `../DelegatedEvidence/MetaSkill.md`.

1. Identify the artifact and the scoping decision around it.
2. Explain the artifact's role, inputs, outputs, and nearest connections.
3. Identify apparent owning context, capability, or responsibility area.
4. Clarify how it relates to the requested change.
5. Judge in scope, adjacent, or out of scope from current evidence.
6. State unknowns blocking confident judgment.
7. State confidence and what would raise it.

## Subject Adaptation

- Code: module role, interfaces, deps, data flow, test relevance
- Websites/content: page, template, model, rule, or workflow; user-facing influence
- PM/workflow: board, field, automation, report, or status rule; process role
- Knowledge: note, hub, index, taxonomy artifact; routing/source-of-truth role

## Parent Synthesis Format

Parent brief sections. Omit only no-signal sections.

1. `Artifact`
2. `Artifact Role`
3. `Bounded-Context Fit`
4. `Immediate Connections`
5. `Why It Matters For Scope`
6. `Scope Judgment`
7. `Risks And Unknowns`
8. `Confidence`
9. `Recommended Next Step`

Closing trio (`Risks And Unknowns`, `Confidence`, `Recommended Next Step`) required in this order. `Scope Judgment` states in scope, adjacent, or out of scope.

## Boundaries

- Stay on one artifact or tight area
- Do not broaden into onboarding or architecture research
- Do not explain current state without a scoping decision
- Do not write plans or implementation advice
