---
name: "grill-for-unknowns"
description: "Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation. Do not use for ordinary idea stress tests or work with settled acceptance criteria."
kind: "dev"
---

# Evidence-grounded unknowns grill

Use this skill to expose the few missing facts or decisions that could materially change a complex implementation plan. It owns the evidence-grounded planning interview.

Run the investigation and interview within this workflow. The only optional documentation dependency is the `domain-modeling` procedure inside `matt-mode`, under the conditions below. Resolve every bundled path relative to the directory containing this `SKILL.md`.

## Working model

- **Map**: the request, plan, assumptions, prior context, and current mental model
- **Territory**: the codebase, authoritative docs, APIs, tests, product constraints, deployment environment, and user taste
- **Unknowns**: material gaps between the map and the territory

An unknown is material when resolving it could change architecture, scope, user-facing behavior, data, permissions, cost, migration, or acceptance criteria.

## Guardrails

- Stay in planning behavior until every discovered material unknown is resolved, defaulted, or explicitly accepted
- Retrieve facts instead of asking the user for them; reserve questions for decisions only the user can make
- Keep the working ledger in the conversation unless the user authorizes a durable artifact
- End this workflow after the user confirms shared understanding or accepts labeled assumptions; implementation requires a separate request outside this skill
- Do not create or update project files without write authorization
- Do not spawn subagents unless the user or project instructions authorize delegation

## Workflow

### 1. Restate the map

Summarize the intended outcome, current plan, stated constraints, and existing evidence. Separate user statements from verified facts.

Complete this step when the map is explicit enough to compare with the territory.

### 2. Read the territory

Inspect the relevant source, tests, configuration, logs, project conventions, and primary documentation. Mark inaccessible evidence and claims that remain unverified.

Current code and tests show observed behavior, not necessarily intended behavior. Treat contradictions between source, docs, tests, and user intent as unknowns to resolve.

Complete this step when the evidence explains the high-risk gaps and every remaining verification gap is visible.

### 3. Find the material unknowns

Use these categories as discovery lenses when they could expose a gap:

| Lens | What to look for |
| --- | --- |
| Known knowns | Claims stated by the user or supported by evidence |
| Known unknowns | Decisions already recognized as unresolved |
| Unknown knowns | Criteria the user can recognize but has not verbalized |
| Unknown unknowns | Constraints or failure modes nobody has raised yet |

Once exposed, an unknown no longer needs a special category. Record it once with:

- what is missing
- why it could change the plan
- the available evidence or verification gap
- its resolution, default, or open status, plus the next action when one remains

For high-risk dependencies, inspect documented limits and known failure modes. When the user can judge behavior or appearance but cannot specify it, show contrasting examples or a cheap prototype and capture the reaction as a verification rubric.

For a complex session that warrants a durable artifact, read `references/templates/grill-session.md`. Do not create it without write authorization.

Complete this step when every discovered material gap appears once in the ledger and is resolved, defaulted, accepted, or has a cheap next action.

### 4. Resolve facts and grill decisions

Resolve retrievable facts directly. Ask one blocking question when its answer could change the next question. When two or three material questions are independent, ask them together.

Each question must cover one decision and be:

- **Material**, because the answer could change the plan
- **Grounded**, because it points to evidence or a concrete verification gap
- **Answerable**, because the user can choose or accept a default

Use this shape:

```md
Blocking question: <question>
Why it matters: <what changes between the plausible answers>
Evidence: <source, test, documentation, or verification gap>
Recommended answer: <default and rationale>
If you do not care: I will use <default> in the plan
```

Do not ask about facts the agent can retrieve, preferences a competent agent can default, or taste the user can only recognize when shown examples.

Keep about five blocking questions as the default total budget. Ask whether to continue before exceeding it. If the user becomes terse or says to choose, stop interviewing and present the remaining defaults as one batch for veto.

After each answer or batch, update the ledger and report how many material unknowns remain. Complete this step when none remain blocked.

### 5. Close the planning loop

Present:

1. resolved decisions and defaults with their evidence
2. remaining open questions or accepted risks
3. implementation steps with verification gates
4. a deviation policy for contradictions found during implementation

Ask the user to confirm the shared understanding. Then stop. Confirmation closes the grill and does not authorize implementation.

## Domain language and durable decisions

When the session reveals fuzzy terms, conflicting vocabulary, or a durable trade-off, clarify it in the conversation. If the user also requests documentation and authorizes project writes, read `references/domain-modeling-add-on.md` and use Matt-mode's `domain-modeling` procedure for that bounded documentation task. A technical topic or a request to investigate does not itself enable documentation.

## Deviation policy

- Continue and log a low-risk local adjustment
- Stop and ask when new evidence changes architecture, migration, security, cost, permissions, or user-facing behavior
- Treat a conflict between the map and territory as a new unknown, not an automatic correction

## Final check

Before closing, confirm that:

- factual claims cite inspected evidence or state their verification gap
- every discovered material unknown is resolved, defaulted, or accepted
- subjective criteria have an example or rubric
- verification gates exist before implementation
- no unauthorized files or implementation changes were made
- any use of Matt-mode's `domain-modeling` procedure was limited to the requested documentation and authorized write scope

For provenance and maintenance history, read `references/upstream-lineage.md` only when updating this skill.
