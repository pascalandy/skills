---
name: "pa-brainstorm"
description: "Use when the user wants to brainstorm an idea, feature, design, product decision, workflow change, or improvement."
kind: "general"
---

# PA Brainstorm Session

Explicit entry point: `pa-brainstorm`.

Use Brainstorm to answer one question before direction or planning: what could this idea become?

Explore problem, users, value, options, tensions, candidate directions, assumptions, and open questions through dialogue. For product-shaped ideas, optionally run an office-hours-style diagnostic that tests demand, status quo, beneficiary specificity, narrowest wedge, and premise quality before `pa-vision`. Do not canonize product direction, non-goals, success criteria, acceptance expectations, or implementation scope. Do not implement code or design technical execution unless the brainstorm itself is about a technical/architectural decision.

## Core Contract

For each brainstorm session:

1. Start from the user's idea without prematurely narrowing it.
2. Clarify the beneficiary, problem, value, and possible success signals before naming candidate directions.
3. Separate verified facts, assumptions, options, decisions, and open questions.
4. Ask one high-leverage question at a time unless the user requests a compact synthesis.
5. Explore meaningful alternatives before recommending a direction.
6. Produce either a concise chat synthesis or a durable brainstorm artifact proportional to the scope.
7. Recommend the next `sdlc-pa` move based on what remains uncertain.

## Internal Modes

| Mode | Owns | Use when |
|---|---|---|
| `Exploration` | Default brainstorming | The user wants options, shape, or rough ideation without a hard product-worthiness test |
| `ProductDiagnostic` | Office-hours-style pressure test | The user asks whether an idea is worth building, who it is for, what wedge to pursue, or whether demand/value is real |
| `BuilderSpark` | Delight-first side-project ideation | The user is building for learning, fun, open source, demos, personal workflow delight, or a shareable artifact |

Do not use `ProductDiagnostic` for every brainstorm. Use it only when value, beneficiary, demand, wedge, or product shape are materially uncertain.

## Use This When

- A rough idea needs to become rich enough for `pa-vision` to accept, revise, or reject.
- Product behavior, scope boundaries, or success signals are still fuzzy and need exploration, not commitment.
- Multiple plausible directions exist and the user needs a thinking partner.
- The user asks whether an idea is worth building, who needs it, what the status quo is, or what the smallest useful wedge should be.
- A workflow, documentation, or agent-skill change needs idea exploration before direction.
- A non-software decision needs structured exploration and a compact synthesis.

## Boundaries

| If the real need is... | Use instead |
|---|---|
| quickly preserving a raw thought | `pa-idea` |
| stress-testing assumptions or tradeoffs in an already-stated plan | `grilling` |
| bounded current-state evidence or blast-radius mapping | `pa-scope` |
| deciding target state after the idea is clear | `pa-vision` |
| designing technical execution, phases, interfaces, or sequencing | `architect` or `figure-it-out` |
| building or fixing behavior | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |
| documenting an already-made change | `pa-doc-update` |

## Operating Rules

1. Ask one question at a time.
2. Prefer the platform's blocking question tool when available; use prose only for genuinely narrative or introspective questions.
3. Start by understanding what the user already thinks, tried, ruled out, or suspects.
4. Explore before narrowing. Do not anchor the user with a recommendation before they have seen meaningful alternatives.
5. Surface candidate behavior, possible boundaries, and success signals without treating them as accepted direction.
6. Keep implementation details out of the brainstorm artifact unless they are the subject of the decision.
7. Use repo-relative paths in generated documents; never use absolute paths inside durable artifacts.
8. If a claim about existing code, docs, dependencies, routes, config, schemas, or missing support is checkable, verify it before treating it as fact. Otherwise label it as an unverified assumption.

## Brainstorm Discipline

- **Simplicity first:** keep the exploration proportional. Do not turn a rough idea into a full requirements package unless the scope warrants it.
- **Surface conflicts, don't average them:** when candidate directions pull against each other, name the trade-off and keep alternatives distinct instead of blending them into a vague compromise.
- **Read before treating claims as facts:** use repository or artifact evidence for checkable claims; otherwise label assumptions.
- **Fail loud:** do not hand off to `pa-vision`, `architect`, `figure-it-out`, or a separate `poteto-mode` delivery session as if ready while blocking questions remain unnamed.

For `ProductDiagnostic`, apply sharper office-hours checks:

- **Interest is not demand:** compliments, waitlists, curiosity, or "this is cool" do not count unless paired with behavior, money, repeated usage, workaround pain, or direct pull.
- **The status quo is the competitor:** identify what the beneficiary does today before proposing what should exist.
- **Named beneficiary beats category:** "developers", "teams", or "creators" is too broad unless tied to a concrete role, context, and consequence.
- **Wedge before platform:** prefer the smallest useful proof over a broad product shape.
- **Observed behavior beats imagined behavior:** label imagined users, imagined workflows, and imagined willingness-to-pay as assumptions.

## Scope Levels

Classify the run before asking substantive questions:

| Scope | Use when | Expected artifact |
|---|---|---|
| `Quick` | clear topic, low ambiguity, user mostly needs a sounding board | chat synthesis; export optional |
| `Standard` | bounded feature, workflow, doc, or product decision with open questions | brainstorm artifact usually warranted |
| `Deep-feature` | cross-cutting or high-ambiguity work inside an existing product shape | brainstorm artifact required |
| `Deep-product` | primary actor, outcome, positioning, or core flows are materially unresolved | brainstorm artifact required |

If the scope is unclear, ask one targeted question to disambiguate.

## Mode Selection

Choose one mode before asking substantive questions:

- Use `Exploration` for ordinary feature, workflow, documentation, agent-skill, or product-shape exploration.
- Use `ProductDiagnostic` when the prompt or early answers imply product-worthiness uncertainty: "is this worth building", "who is this for", "what is the wedge", "does this have demand", "startup idea", "office hours", or a serious internal tool whose sponsor/user value is unclear.
- Use `BuilderSpark` when the main currency is delight, learning, open-source usefulness, demo value, personal workflow improvement, or a side-project artifact someone might want to show others.

Mode can change mid-session. If a BuilderSpark idea turns into a serious user/customer bet, switch to `ProductDiagnostic`. If ProductDiagnostic reveals the work is only a personal tool or learning project, switch to `BuilderSpark` or `Exploration`.

## ProductDiagnostic Question Bank

Ask one question at a time. Do not ask all questions by default. Pick the highest-leverage unresolved question and stop after asking it.

### Serious Product / Startup / Internal Tool

1. **Demand Reality:** What concrete behavior proves someone wants this, not just finds it interesting?
2. **Status Quo:** What are they doing today instead, even badly, and what does that cost them?
3. **Specific Beneficiary:** Name the actual person, role, or team that needs this most. What changes for them if it works?
4. **Narrowest Wedge:** What is the smallest version that creates real value this week?
5. **Observed Surprise:** Have you watched someone experience this problem or use a prototype? What surprised you?
6. **Future-Fit:** If the world changes over the next 1-3 years, does this become more or less important?

### Builder / Side Project / Open Source

Use these in `BuilderSpark`, not as startup validation:

1. What is the coolest version of this?
2. Who would you show it to?
3. What would make them say "whoa"?
4. What is the fastest shareable version?
5. What existing thing gets you halfway there?
6. What is the 10x version if time were unlimited?

## Workflow

1. Use the user's input as the starting idea. If no idea is present, ask what they want to explore and wait.
2. Check whether this is software/product/workflow work, non-software brainstorming, or a quick-help request that does not need this skill.
3. Look for existing matching context before substantive brainstorming:
   - recent idea, vision, architecture, or plan artifacts under the resolved `sdlc-pa` export root
   - relevant repo docs or source files
   - project instruction files such as `AGENTS.md`
4. Classify scope: `Quick`, `Standard`, `Deep-feature`, or `Deep-product`.
5. Select `Exploration`, `ProductDiagnostic`, or `BuilderSpark` mode.
6. Match the opening questions to the selected mode:
   - `Exploration`: examine only uncertainties that affect the idea being explored, such as the intended use, constraints, or meaningful alternatives.
   - `BuilderSpark`: focus on enjoyment, learning, personal usefulness, and the smallest satisfying experiment. Commercial demand or viability is relevant only if the user makes it part of the goal.
   - `ProductDiagnostic`: test demand evidence, beneficiary specificity, the current workaround, attachment to a solution before value is clear, material future changes, and the smallest proof before expanding scope.
7. Ask only the highest-leverage unresolved question. Continue one question at a time until the idea is clear enough or the user explicitly wants to proceed.
8. If multiple plausible directions remain, present 2-3 concrete approaches before recommending one. Include at least one non-obvious angle when useful. For `ProductDiagnostic`, this alternatives pass is mandatory.
9. Synthesize the result into either a chat summary or a durable brainstorm artifact.
10. If exporting, resolve `entry_slug`, `export_dir`, `export_file`, and `export_path` before writing.
11. Return the final synthesis, artifact path when written, and recommended next `sdlc-pa` move.

## Approach Exploration

When options differ meaningfully, present them before evaluation:

- **Baseline:** the most direct version of the user's request.
- **Simpler proof:** the smallest version that still proves or disproves the bet.
- **Challenger:** a reframing or adjacent addition that may create more value without disproportionate carrying cost.

For each approach, include:

- what it is
- when it is best suited
- main upside
- main risk or tradeoff

Then recommend one direction with a clear reason.

For `ProductDiagnostic`, always produce 2-3 approaches before recommending a next move:

- **Minimal Proof:** smallest version that tests the core value.
- **Strong Direction:** best version if the premise is true.
- **Lateral / Reframe:** a different angle that may solve the same problem more simply.

## Brainstorm Artifact

Create a durable artifact when the conversation produces decisions that should survive handoff. Skip export for quick brainstorms where the chat synthesis is enough.

Use this template and omit sections that do not help the next phase:

```markdown
# <Topic Title>

**Mode:** `Exploration` | `ProductDiagnostic` | `BuilderSpark`

## Problem Frame

[Who is affected, what is changing, and why it matters.]

## Product Diagnostic

[Include for `ProductDiagnostic` only.]

### Demand / Motivation Evidence

[Concrete behavior, observed pain, direct request, payment, repeated workaround, or personal need. Label imagined demand as an assumption.]

### Status Quo

[What happens today if this is not built.]

### Specific Beneficiary

[Named person, role, team, or user type with context and consequence.]

### Narrowest Wedge

[Smallest useful version that proves or disproves the bet.]

### Premises To Test

- P1. [Load-bearing premise]

### Diagnostic Recommendation

Proceed / Revise / Defer / Stop: [one direct reason]

### Feed Into `pa-vision`

- Beneficiary: [candidate]
- Target state: [candidate]
- Decision question: [candidate]
- Assumptions: [load-bearing assumptions]
- Risks: [main risks]

## Actors

[Include when multiple humans, agents, systems, or roles affect decisions.]

- A1. [Name or role]: [What they do in this context]

## Key Flows

[Include when the work is interaction-shaped or sequence-shaped.]

- F1. [Flow name]
  - **Trigger:** [What starts it]
  - **Actors:** A1
  - **Steps:** [3-7 steps]
  - **Outcome:** [What is true afterward]
  - **Related candidates:** C1, C2

## Candidate Directions

[For Standard and Deep runs, use C-IDs. Group by concern when useful. These are raw material for `pa-vision`, not accepted requirements.]

- C1. [Possible direction, behavior, or requirement candidate]

## Candidate Success Signals

- [Possible human outcome]
- [Possible downstream-agent handoff quality]

## Possible Boundaries / Tensions

- [Possible exclusion, trade-off, or unresolved boundary]

## Emerging Preferences

- [Preference or leaning]: [Rationale and uncertainty]

## Dependencies / Assumptions

- [Material dependency, verified fact, or explicit assumption]

## Outstanding Questions

### Resolve Before Direction

- [Question that blocks `pa-vision` or target-state decision]

### Deferred To Later

- [Question better answered by `pa-scope`, `architect`, or implementation]

## Recommended Next Move

`pa-vision` / `pa-scope` / `architect` / `figure-it-out` / separate `poteto-mode` delivery session
```

At `Deep-product` scope, split `Possible Boundaries / Tensions` into:

- `Deferred for later`
- `Outside this product's identity`

## Export

Read `references/export-artifacts.md` from the active `pa-doc-update` skill directory and follow its `pa-brainstorm` export profile.

- Mandatory for `Deep-feature` and `Deep-product`.
- Usually warranted for `Standard`.
- Optional for `Quick`.

## Handoff

Recommend the next move based on what remains uncertain.

Before recommending `pa-vision`, `ProductDiagnostic` should identify:

- beneficiary
- target state candidate
- decision question
- narrowest wedge
- load-bearing assumptions
- unresolved evidence gaps

If these are missing, do not hand off as ready for `pa-vision`; either continue brainstorming, recommend `grilling`, or mark the missing anchors and ask whether the user accepts them as assumptions.

General handoff table:

| State after brainstorm | Recommended next move |
|---|---|
| raw thought should be preserved first | `pa-idea` |
| assumptions are still fuzzy | `grilling` |
| current state or blast radius is unclear | `pa-scope` |
| target state is ready to decide | `pa-vision` |
| direction is settled but execution shape is unclear | `architect` |
| architecture is clear but ordering is unclear | `figure-it-out` |
| work is tiny, clear, and verifiable | a separate `poteto-mode` delivery session using the matching Feature or Bug fix playbook |

Do not hand off as ready for direction while `Resolve Before Direction` has unanswered questions unless the user explicitly accepts them as assumptions.

## Anti-Patterns

Do not:

- treat a raw idea as settled direction
- turn brainstorming into implementation, architecture, or planning by default
- ask a long questionnaire before giving useful structure
- run the office-hours diagnostic as a mandatory interview for every brainstorm
- anchor on the user's first solution shape before testing the underlying value
- invent candidate requirements, actors, workflows, or repository facts without evidence
- hide unresolved assumptions inside confident prose
- export a durable artifact for a quick exchange that only needs chat synthesis
- hand off to `pa-vision`, `architect`, `figure-it-out`, or a separate `poteto-mode` delivery session while blocking questions remain unnamed
- use absolute local paths in durable artifacts

## Verification

Before declaring the brainstorm complete:

- [ ] The possible beneficiary, value, and success signals are concrete enough to evaluate.
- [ ] Possible boundaries name real exclusions or tensions, not generic "future work".
- [ ] Standard and Deep candidate directions are clear enough for `pa-vision` to accept, revise, or reject.
- [ ] Product-shape alternatives were considered when more than one plausible direction existed.
- [ ] In `ProductDiagnostic`, Minimal Proof / Strong Direction / Lateral or Reframe alternatives were considered before recommendation.
- [ ] In `ProductDiagnostic`, status quo, specific beneficiary, narrowest wedge, and demand or motivation evidence are explicit, or their absence is named.
- [ ] Load-bearing assumptions are named.
- [ ] Checkable repository facts were verified or labeled as assumptions.
- [ ] Implementation details did not leak in unless the brainstorm was inherently technical.
- [ ] The recommended next `sdlc-pa` move follows from the remaining uncertainty.
- [ ] When export is required, the artifact is written before handoff.

## Non-Goals

Brainstorm does not own final direction, architecture, implementation planning, coding, code review, QA, postmortems, or documentation maintenance.
