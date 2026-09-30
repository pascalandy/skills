---
name: "pa-qa"
description: "Use only when explicitly invoked as `pa-qa` for post-implementation validation or a reported user-facing problem."
kind: "dev"
---

# PA QA Session

Run post-implementation QA after the selected implementation workflow or before closing a change. Validate accepted user-facing behavior when no problem is reported. When the user reports problems conversationally, clarify lightly, inspect enough context, and produce durable QA findings or follow-ups in project domain language.

## Core Contract

For each validation pass or reported problem:

1. Choose the QA mode: `ValidationPass` or `FindingCapture`.
2. Listen and clarify just enough when a problem is reported.
3. Explore relevant product, code, and documentation context.
4. Validate accepted behavior or decide whether the report is clear enough to record.
5. If unclear, run a bounded diagnosis loop.
6. Decide whether to keep one finding or split into behavior slices.
7. Produce a validation summary or concise, numbered QA finding record(s) with reproduction steps or explicit reproduction status.
8. Include a behavior-focused repair handoff when a finding is ready for implementation.
9. Share the validation summary or finding record(s) in chat unless the user names another destination.

## QA Modes

| Mode | Owns | Use when |
|---|---|---|
| `ValidationPass` | Final user-facing behavior check | Accepted behavior, workflow continuity, command output, rendered artifact, or manual walkthrough needs validation before close |
| `FindingCapture` | Durable QA finding records | The user reports a problem or validation discovers a user-facing failure |

Use `ValidationPass` first when the goal is final E2E validation and there is no reported problem. Switch to `FindingCapture` only when validation reveals a concrete issue.

## QA Discipline

Apply these rules during validation and finding capture:

- **Simplicity first:** use the smallest proof loop that can validate the accepted behavior or clarify the finding. Do not turn QA into broad debugging or implementation.
- **Surgical changes:** if diagnosis requires temporary probes, tag and remove them. Do not clean, refactor, or fix adjacent implementation from `pa-qa`.
- **Surface conflicts, don't average them:** when accepted behavior, docs, implementation, and observed behavior disagree, report the conflict and route the decision; do not soften it into a vague partial pass.
- **Read before you validate:** inspect the user-facing contract, docs, CLI/help/API surface, workflow, or artifact before deciding what should happen.
- **Tests verify intent:** proof signals must exercise the user-facing reason the behavior matters, not only a nearby implementation path.
- **Checkpoint after significant steps:** after reproduction, diagnosis, validation, or split/keep decisions, restate what is observed, verified, remaining, and uncertain.
- **Match project conventions:** use the project's QA, issue, test, logging, and artifact conventions when they exist.
- **Fail loud:** mark `Not fully verified` when checks are skipped, the environment blocks validation, reproduction is partial, or the proof signal is weaker than the accepted behavior.

## Workflow

### 1. Listen and lightly clarify

For `ValidationPass`, start from the accepted behavior, implementation brief, `AC-*`, review record, or user-approved workflow and identify the strongest available proof signal.

For `FindingCapture`, let the user describe the problem in their own words. Ask **at most 2–3 short clarifying questions** before moving forward.

Prefer questions about:

- What they expected vs what actually happened
- Steps to reproduce, if not obvious
- Whether the behavior is consistent or intermittent
- The affected user, workflow, command, screen, or artifact

Do not over-interview. If the behavior is clear enough to validate or record, validate or record it.

### 2. Explore context without leaking implementation details

Inspect relevant codebase and documentation context to understand:

- The project's vocabulary and domain terms
- The expected behavior
- The user-facing behavior boundary
- The workflow, command, screen, or artifact involved
- Related docs, ADRs, prior QA notes, README sections, CLI help, or product specs **if present**

Do not assume specific documentation files exist. Discover the local project structure first, then use whatever source of truth is actually available. If there is no clear project vocabulary, use plain user-facing language.

This improves finding quality, but final QA findings should **not** cite internal files, line numbers, function names, or implementation details.

### 3. Decide whether bounded diagnosis is needed

Do **not** force every QA report through full debugging. Use the bounded diagnosis loop only when one of these is true:

- Reproduction steps are unclear
- The symptom is intermittent or flaky
- A performance regression is reported
- The behavior boundary is ambiguous
- You cannot tell whether this is one finding or multiple findings
- You need a sharper pass/fail signal to avoid recording a vague finding

If the user-facing behavior is already clear enough, skip diagnosis and validate it or record the finding.

## Bounded Diagnosis Loop

Diagnosis exists to clarify the QA finding, not to silently turn `/pa-qa` into implementation.

### Phase 1 — Build or identify a feedback loop

Find the fastest agent-runnable signal that demonstrates the reported behavior.

Try, in roughly this order:

1. Failing test at the right seam: unit, integration, or e2e
2. CLI invocation with fixture input and expected output
3. Curl / HTTP script against a local dev server
4. Headless browser script for UI behavior
5. Replayed captured trace, request, payload, event log, or fixture
6. Throwaway harness around the smallest useful system slice
7. Repeated loop for flaky behavior
8. Differential run between old/new version or two configs
9. Human-in-the-loop script only as a last resort

A useful loop is:

- Fast enough to run repeatedly
- Deterministic, or at least high-reproduction-rate for flaky bugs
- Specific to the user-described symptom
- Narrow enough to clarify scope

If you genuinely cannot build or identify a loop, say so. List what you tried and ask for the missing artifact: logs, HAR, recording, exact command, sample input, environment access, or permission to add temporary instrumentation.

### Phase 2 — Reproduce or capture the symptom

Confirm that the observed failure matches the **user's** report, not a nearby unrelated problem.

Capture:

- The exact symptom
- Inputs, flags, config, screen, or workflow involved
- Expected vs actual result
- Whether it reproduces consistently
- Any minimal condition that changes the result

### Phase 3 — Hypothesize only when needed

If the cause or behavior boundary is still unclear, generate **3–5 ranked hypotheses** before testing any one explanation.

Each hypothesis must be falsifiable:

> If `<cause>` is true, then `<probe/change>` should make `<observable result>` happen.

Avoid anchoring on the first plausible explanation. If the user has domain context, share the ranked list briefly and invite correction, but do not block indefinitely if they are unavailable.

### Phase 4 — Instrument narrowly

Each probe must test one prediction from the hypothesis list.

Prefer:

1. Debugger or REPL inspection when available
2. Targeted logs at boundaries that distinguish hypotheses
3. Profiling, timing harnesses, or query plans for performance regressions

Avoid "log everything and grep."

If adding temporary logs, tag them with a unique prefix such as `[DEBUG-a4f2]` so they can be removed reliably.

### Phase 5 — Clarify finding scope

Use diagnosis findings to answer:

- What behavior is wrong?
- How can someone reproduce it?
- Is this one finding or multiple independent behavior slices?
- Is there a reliable pass/fail signal a future implementer can use?
- Is the fix blocked by another finding or prerequisite?

### Phase 6 — Cleanup if investigation changed files

Before declaring the QA investigation done:

- Remove temporary `[DEBUG-...]` instrumentation
- Delete throwaway prototypes, or move them to a clearly marked debug location if the user wants to keep them
- Note any missing test seam as QA context, without over-exposing implementation details
- Re-run the repro loop if the investigation itself changed local state

## Scope Assessment

Before recording the result, decide whether the report should remain one durable finding or be split.

### Break down when

- There are multiple independent user-facing failure modes
- Fixes can be delivered independently
- Different workflows, actors, commands, screens, or product areas are affected
- One symptom blocks another finding from being tested
- The report mixes bug, design ambiguity, and documentation gap

### Keep as one finding when

- One behavior is wrong in one place
- Symptoms share the same user-facing behavior boundary
- Splitting would create implementation-shaped tasks rather than useful behavior slices
- The reproduction steps are naturally one scenario

## Validation Pass Output

When no issue is found, default to a concise validation summary:

```markdown
### QA Validation — [Short behavior-focused title]

**Accepted behavior checked**
[What user-facing behavior, workflow, command, or artifact was validated.]

**Proof signal**
[Automated check, manual walkthrough, rendered preview, command transcript, or explicit next-best check.]

**Result**
Pass / Needs follow-up / Not fully verified.

**Gaps or risks**
[Unverified paths, skipped checks, environment limits, or none.]

**Recommended next phase**
Stop / `pa-doc-update` / a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook / another QA pass.
```

If validation discovers a user-facing issue, produce a QA finding instead of hiding it in the validation summary.

## QA Finding Record

Default to producing the QA finding in chat. Only write to a tracker, project board, document, or external system when the user explicitly asks or the repository already defines that destination. If the repository defines a QA or issue tracker convention, offer to export the finding there after presenting it in chat; do not export silently.

Use stable finding IDs within each QA session so findings can be referenced by the next implementation pass, tracker items, follow-up docs, or later QA passes.

Use this portable format:

```markdown
### QA-001 — [Short behavior-focused title]

**What happened**
[Actual behavior in plain language.]

**What I expected**
[Expected behavior.]

**Steps to reproduce / reproduction status**
1. [Concrete step, or state what is currently unknown]
2. [Concrete step]
3. [Relevant input, flag, config, screen, or workflow]

**Scope**
[One finding, split finding, blocker, affected workflow, or product area.]

**Repair handoff**
- Candidate next workflow: a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook
- Required proof signal: [Observable pass/fail signal for the user-facing behavior]
- Blockers or missing context: [If any]

**Additional context**
[Useful observations only. Avoid internal paths, line numbers, and implementation guesses.]
```

The repair handoff must describe the next verification target, not the implementation strategy. Keep it behavior-focused unless the repository convention explicitly requires implementation details or the user asks for them.

For split findings, repeat the same format for each independent behavior slice and note any prerequisite relationship in `Scope`.

## Anti-Patterns

Do not:

- Treat final validation as only issue capture when accepted behavior can be checked directly.
- Turn every QA report into a full debugging expedition.
- Produce implementation-shaped tasks when the user reported behavior.
- Hide uncertainty behind confident prose.
- Guess a root cause without a repro or clear evidence.
- Split findings merely by code module.
- Ask a long questionnaire before doing useful exploration.
- Leave debug logs or throwaway harnesses behind.

## Session Loop

After each validation pass, finding, or finding set, share the QA summary and continue with the user's next QA report, repair request, export request, or stop signal.
