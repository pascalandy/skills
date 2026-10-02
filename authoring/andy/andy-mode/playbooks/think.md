# Think

Use the smallest reasoning method that can reduce the uncertainty blocking the user. Depth comes from following the decisive uncertainty, not from applying many lenses.

## Operating contract

- The user describes the situation; never require them to name a method
- Choose one method by default and read only its reference
- Briefly name the chosen method and why it fits, without presenting the full menu
- Add a second method only after the first is complete and exposes a different unresolved uncertainty
- Separate observations, inferences, assumptions, and unknowns whenever the distinction affects the conclusion
- Treat analysis as a model of reality, not a substitute for missing evidence
- Do not launch subagents unless the user asks for delegation or another applicable instruction requires it

## Step 1: find the blocking uncertainty

Read the conversation and available workspace context before asking the user for anything. State the working question and the outcome the user needs.

Ask at most one clarifying question only when two plausible interpretations would lead to materially different work. Otherwise make a reasonable assumption and label it.

This step is complete when one uncertainty can be named whose reduction would change the judgment, decision, or next action.

## Step 2: check ownership

`think` owns model-building before action. It does not imitate a specialist whose method already matches the request.

| Actual request | Better owner |
|---|---|
| Challenge a stated opinion or argument | the `sparring` route |
| Pressure-test through focused questions | `grilling` |
| Design software structure | `architect` in design-only mode |
| Plan non-software structure or a macro-roadmap | `figure-it-out`, framing and planning only |
| Design a module interface, seam, or abstraction depth | `matt-mode ; codebase-design` |
| Reproduce, diagnose, or repair software behavior | the `poteto-mode` Bug fix playbook |
| Review any completed deliverable with fresh eyes | `2nd-pass` |
| Run an unusually harsh maintainability review | `code-review-mode ; thermo-quality-review`, or `interrogate` for several reviewers |
| Work with the opinionated Game Theory lecture corpus | `game-theory-corpus` |

If the specialist is already active, follow it. Otherwise name the recommended invocation and explain the handoff in one sentence. Do not pretend to have run an explicit-only skill that was not invoked.

This step is complete when `think` either owns the remaining uncertainty or has identified the exact handoff.

## Step 3: choose one method

Read only the selected method.

| Blocking uncertainty | Method to read |
|---|---|
| The question, criterion, or frame may be wrong | `references/think/frame.md` |
| Constraints, assumptions, and conventions are mixed together | `references/think/decompose.md` |
| Several explanations could account for the observations | `references/think/diagnose.md` |
| Options must be judged against decision-relevant criteria | `references/think/compare.md` |
| Actors may respond strategically to rules, incentives, or one another | `references/think/dynamics.md` |
| Benefits, burdens, duties, consent, or harm may be misallocated | `references/think/ethics.md` |

### Tie-breakers for mixed requests

Choose the method that settles the earliest dependency in the reasoning, then finish it before considering another:

| Mixed uncertainty | Choose first |
|---|---|
| The question or criterion may be wrong, regardless of the downstream method | `frame`, but only when changing the frame could change the work |
| Feasibility or the option set depends on disputed constraints | `decompose` before `compare` |
| Observed behavior admits several possible causes | `diagnose` when the result needed is causal discrimination; choose `dynamics` when actor adaptation or response prediction is central, and keep motives as hypotheses |
| Rights, consent, duties, or serious harm could disqualify an option | `ethics` before `compare` |
| Option outcomes depend on how actors will react | `dynamics` before `compare`; choose `compare` directly when those reactions are already modeled or immaterial |

If the first method removes the need for the rest, stop. A mixed prompt does not authorize automatic composition.

If the selected method stalls or the user explicitly requests another angle, read `references/think/techniques.md` and select one targeted technique. Never run the whole bank by default.

This step is complete when the chosen method has produced a material update to the model or made the irreducible uncertainty explicit.

## Step 4: return a decision-useful result

Scale the response to the request. Preserve these meanings without forcing headings when a short answer is clearer:

- the working question
- the relevant evidence and assumptions
- the result of the chosen method
- the strongest live uncertainty or objection
- what would change the conclusion
- the next useful move

Do not manufacture closure. A rigorous result may be a recommendation, a discriminating test, a reframed question, or a justified declaration that the current evidence cannot decide.

The run is complete when the user can make a better judgment, request the missing evidence, or invoke the exact next specialist without learning this skill's internal taxonomy.

## Maintenance

When evaluating or changing this skill, read `references/think/acceptance-cases.md`. Do not load those cases during normal use.
