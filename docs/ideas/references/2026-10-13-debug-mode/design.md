---
name: debug-mode design
description: Why and how to turn Cindy Sridharan's debugging post into one mode, debug-mode, plus edits to the skills it touches
date_created: 2026-10-13
status: proposed
---

# Design: debug-mode

This page explains the design. [plan.md](plan.md) holds the build steps. [sources/](sources/) holds the inputs: the brief, two independent designs (Codex GPT-6.1-Sol and Claude Opus 5.5), the lead's design written before reading them, and a prior-art survey.

The ideas come from Cindy Sridharan, [How to effectively debug when you no longer understand the code](https://copyconstruct.medium.com/how-to-effectively-debug-when-you-no-longer-understand-the-code-bd3dcb2c5f7b) (2026-10-10). Every skill built from this design restates her ideas in our own words and credits her with that link. No skill quotes her prose.

## The problem

Agents debug badly in predictable ways. They read code first and tell a story about what the code can do, not what it did. They take the first plausible cause for the cause. They skip the control, so they cannot tell signal from noise. They accept a repro because the symptom matches. They count a second agent's agreement as proof. In all three of the post's bugs, the agent was able to find the cause and did not, until a human supplied a control, a constraint, or a demand for citations.

Pascal's skills already hold pieces of the fix, scattered across six places with no shared vocabulary: poteto-mode's `bug-fix`, `runtime-forensics`, `trace-forensics`, and `perf-issue` playbooks, its `fix-root-causes` principle, and andy-mode's `qa` diagnosis loop. Two skills contradict the post outright: `bug-fix` seeds hypotheses by reading code with `how`, and `interrogate` treats reviewer agreement as evidence.

Pascal named two goals:

1. **Build time.** Each feature, or group of features, adds hooks to the verification loop, so it is easy to test and to trace back
2. **Run time.** A bug arrives from production. Gather every signal from it, then apply the method

## The one idea the system rests on

**Facts constrain hypotheses, and a control turns facts into signals.**

A fact is an observation a tool or a report made, saved with its source. The agent cites facts and never writes or edits them. A hypothesis is anything the agent derives. A hypothesis survives only while no fact contradicts it.

The same comparison serves both goals. At run time, the failing case is compared with a control to find the reading that differs. At build time, the new build is compared with the last good build to confirm that no reading differs except the intended ones. A gate is a diagnosis that found no signal.

So the readings a feature emits at build time are the facts a future investigation starts from. Goal 1 prepares Goal 2. Goal 2, when it closes, moves the reading that found the cause to a shallower layer, where Goal 1's gate checks it on every build. That loop is what makes the system accretive.

## Principles

These are the post's ideas, sharpened by the prior-art survey, written as rules an agent can act on. The skill turns each one into a step, a column, or a check. The survey's corrections to the post are marked *(survey)*.

**Stance**

1. Start from facts, not code. Code says what can happen, not what did happen. Read code only to explain a named signal
2. Play to agent strengths: reading large raw data, joining sources across layers, knowing obscure tools and formats, rerunning checks, and writing throwaway probes
3. Guard against agent weaknesses with structure, not exhortation. Required fields, citations, and checks work. Reminders do not *(survey: debiasing training failed in a controlled medical trial)*

**Facts**

4. Facts are append-only. A suspect fact is gathered again, never edited or argued away
5. An absence is a fact only with its coverage. "No logs" counts against a hypothesis only if the logs would have shown it *(survey: Heuer's expected-evidence check; the post's own auth team made this mistake)*
6. Keep the store fat and the working set thin. Raw artifacts stay on disk. The reasoning context holds one short row per fact with a pointer *(survey: more data raises confidence, not accuracy)*
7. Prefer arithmetic to narrative: counts, sizes, durations. 5 addresses against 400 settles what a paragraph cannot

**Controls and signals**

8. No control, no signal. Pick a control that differs from the failing case in the suspected factor only, and write why it is not broken the same way
9. A louder sad path that fails differently is often the cheapest good control
10. A signal is any reading that differs between the failing case and the control, in either direction. A reply the control receives and the failing case never gets is a signal *(survey: the post defines one direction only, and its hang was decided by the other)*
11. Measure the noise floor before calling a difference a signal: read two controls when readings vary *(survey: Diffy's A/A run)*
12. A signal is strong when few hypotheses explain it, ideally one. Service aggregates such as P99 are detectors, not locators

**Hypotheses**

13. Every hypothesis cites the fact it starts from and states the prediction that would kill it
14. Keep a "none of these" reservation. One surviving row does not prove the list was complete, so every claim holds only among the hypotheses listed *(survey)*
15. Before each probe meant to tell hypotheses apart, write what each live hypothesis predicts. Skip it when the predictions all agree *(survey: Platt's strong inference)*
16. One cited contradicting fact eliminates a hypothesis. Lack of support does not
17. When no row survives, repair the set before inventing: reverify facts, split coarse hypotheses, merge per-instance ones, combine complementary ones, and only then draw a new one from existing facts
18. When every signal is weak or the repairs fail, gather one layer down instead of guessing. Stop at the strongest signal, not the deepest
19. A combination is valid only when each member is needed to explain some fact. In an incident, the loop that sustains the failure matters more than the trigger *(survey: Bronson et al.)*
20. When failing instances disagree, they may be separate bugs. Cluster them and run one matrix per cluster *(survey)*

**Repros, review, and claims**

21. A repro is a hypothesis. Keep it only if it shows the report's strongest signal
22. Adversarial review eliminates. It never confirms, because no reviewer can see a missing fact. Give the reviewer facts, not the story, and use another model family
23. After a retraction, generate the next hypotheses in a fresh context from the case file alone *(survey: agents that take a wrong turn rarely recover in the same conversation)*
24. State the claim level: consistent, confirmed, or fixed. Confirmed needs a test that no other live hypothesis passes. Fixed needs, on the same surface, the signal that found the cause back at the control's value, the reported symptom gone, and no residual failure

**Build time and accretion**

25. Decide a feature's gauges and invariants before writing its code, and emit them by default at the shallowest layer
26. A gate that never failed proves nothing. Plant the regression and watch the gate fail
27. Every human intervention is a gap. Send each one to a probe, a control, a gauge, an invariant, a policy line, or an eval, so the next case does not need it
28. People set policy and make accountable calls. They do not relay commands or paste output for the agent

## The tower

Each level uses only the levels below it. An agent can enter at any level and know what it may read and write. (A level is part of this design. A layer, in the vocabulary below, is a depth of the system under investigation.)

| Level | Owns | Lives in |
|---|---|---|
| L0 Vocabulary | The terms below and the write rule | `debug-mode/SKILL.md`, `references/glossary.md` |
| L1 Observation | Probes read a layer of the system. Features emit gauges. Every reading becomes a fact | `references/ladders.md`, the project's `verify-<app>` skill |
| L2 Comparison | The variable against a control gives signal or noise. A new run against a baseline run gives parity | `references/parity.md` |
| L3 Inference | Hypotheses judged against facts: strength, candidates, combinations | the case file |
| L4 Steering | The next step: gather, control, hypothesize, judge, discriminate, repair, descend, validate | `playbooks/diagnose.md`, the eliminator |
| L5 Decision | Fix options, policy lookup, one question to Pascal, the fix, the parity fact | `playbooks/diagnose.md`, poteto `bug-fix` for the repair |
| L6 Accretion | Give every intervention and every deep signal a destination that is cheaper next time | close step, `references/destinations.md`, `playbooks/instrument.md` |

Build time uses L0, L1, L2, and L6. Run time uses all seven.

## Vocabulary

One term per concept. The skill uses no synonyms for these.

| Term | Meaning |
|---|---|
| case | One investigation of one reported failure, recorded in one case file |
| variable | The failing case, scoped: which hosts, users, versions, and time window |
| control | A case compared with the variable. Types: `happy` (works), `sad` (fails differently and louder), `baseline` (last good version or run) |
| noise floor | The spread between two readings of the same control |
| fact | An observation with its source and a saved artifact. Append-only for the agent |
| field, lab | Where a fact came from: the real failing environment, or a repro or harness. A lab fact never outranks a field fact |
| fact kind | `signal` (differs between variable and control, in either direction, beyond the noise floor), `noise` (same in both), `symptom` (seen on the variable, no control reading yet), `context` (a condition such as version, flag, or scale) |
| coverage | For an absence, what the probe could have seen. An absence without coverage cannot contradict a hypothesis |
| layer, ladder | One level of a stack, and the ordered list of levels from the cheapest (the report, logs) to the deepest (kernel tables) |
| probe | A command that reads one layer and saves its output as an artifact |
| gauge | A named, countable reading a feature emits on every run, with a known control value |
| invariant | A gauge whose control value is zero violations, enforced loudly in code |
| hypothesis | A derived claim of cause: mechanism, starting facts, and the prediction that would kill it. Status is `live`, `replaced` (the parent of a split or a merge), or `eliminated` |
| `H0` | The "none of these" reservation. It is never marked, never counted, and never a candidate. It limits every claim to the hypotheses listed |
| mark | One cell of the matrix. `+`: if the hypothesis is true, it produces this fact. `0`: compatible with the fact, but does not produce it alone. `x`: if the hypothesis were true, this fact could not have been observed, whatever other cause is added. Every `x` cites the fact. Blank: not judged yet |
| in scope | The facts a candidate must answer to: field facts of the variable, or of its cluster when instances were clustered, plus lab facts from repros that passed parity. Facts from a rejected repro stay in the file, out of scope |
| strength | For an in-scope signal or symptom, the number of live hypotheses marked `+`, counting a combination and its members once. Strong is 1 or 2 |
| candidate | A live hypothesis marked `+` on every in-scope signal and symptom and `x` on no in-scope fact |
| combination | Hypotheses that together are a candidate, where removing any member leaves an in-scope fact unexplained. Its marks are derived: `x` where any member has `x`, `+` where any member has `+`, `0` otherwise |
| repair tactic | One of the five moves when no candidate exists: reverify, split, merge, combine, new from facts |
| descend | Gather facts one layer down, paired with the same control |
| repro | A hypothesis of the form "this setup produces the reported failure" |
| parity | Two readings agree under a stated rule. Repro parity, fix parity, and gate parity use the same rules |
| eliminator | An independent read-only reviewer that may only eliminate hypotheses or flag defects in facts and controls |
| claim level | `consistent`: a candidate survives every in-scope fact gathered, among the hypotheses listed. `confirmed`: also passed a test no other live hypothesis passes, such as toggling the suspected cause and watching the strong signal move, or a directly observed causal chain. `fixed`: after the fix, on the same surface, the strong signal matches the control, the reported symptom is gone, and a residual check finds no other failing instance or signal. Other outcomes: `external` (the cause is in a component Pascal does not own) and `open` (stopped, naming the next observation needed) |
| requested outcome | Set at intake: `diagnosis` (read-only questions, andy-mode `qa`, audits of a claim) or `fix` |
| intervention | Any human input that changed the course of a case |
| destination | Where an intervention or a promoted signal lands so the next case does not need it |
| policy | A recorded human decision the agent applies next time without asking |
| gate | Two checks between a baseline run and a new run: detectors (outcomes such as success rate or latency) decide pass or fail, and gauges are compared by parity to show where a failure comes from |
| potency proof | The gate shown failing on a planted regression and passing on the real change |

## The skill

### One mode with two routes

`debug-mode` lives at `authoring/andy-devtools/debug-mode/`, `kind: "dev"`. Its description triggers on its own, like `code-review-mode`, because "prod is slow, debug it" must reach it without anyone naming a mode.

| Route | Goal | Entered from |
|---|---|---|
| `diagnose` | Goal 2: find the cause of a reported failure, verify the fix by parity, give every lesson a destination. Also audits someone's claimed cause, repro, or fix | Pascal, poteto `bug-fix`, `runtime-forensics`, `trace-forensics`, `perf-issue`, `investigation`, andy-mode `qa`, `interrogate` |
| `instrument` | Goal 1: pick a feature's gauges and invariants, emit them by default, record them, gate them, prove the gate fails | Pascal, poteto `feature`, the `diagnose` close step, `maintain-verification-skill` |

Pascal saw two skills in the post: adversarial debugging and the software factory. They are the two routes. They stay in one package because they share the vocabulary, the parity rules, the ladders, and the promotion from a closed case to a gauge. Two packages would duplicate those references or depend on each other across packages and drift.

Adversarial review is not a third skill. It is the eliminator, one prompt used inside `diagnose`: at the control, at the matrix, and at validation. Auditing someone else's diagnosis enters `diagnose` with their claim recorded as a hypothesis, because a claim can only be checked against facts and a control.

Package layout:

```
debug-mode/
	SKILL.md                    route picker, write rule, where cases live, credit
	playbooks/diagnose.md
	playbooks/instrument.md
	references/glossary.md
	references/principles.md    the list above, read when a step does not fit the case
	references/case-file.md     template, column rules, who writes what
	references/ladders.md       ladders per stack, cheap probes per layer, cautions
	references/parity.md        comparison rules, noise floor, normalization
	references/eliminator.md    the reviewer brief
	references/destinations.md  intervention category to destination
	evals/
```

### Why not the alternatives

| Shape | Proposed by | Why not |
|---|---|---|
| A helper skill `evidence-loop` plus a `debuggability` route inside poteto-mode | Codex | poteto-mode runs only when invoked by name, so the build-time route would never reach brigade-mode cooks, matt-mode tickets, or a plain session. poteto/ holds the PStack-derived skills. This is Pascal's own distillation |
| Separate skills for facts, hypotheses, review, repros, and observability | rejected by all three designs | The coordinator would learn the protocol by coordinating many shallow skills |
| The method pasted into each existing skill | rejected by all three designs | Six copies of the matrix rules guarantee drift. They have already drifted |
| An evidence branch inside `interrogate` | Codex | The eliminator's checks depend on the case file's columns, so they belong next to the case file. `interrogate` keeps code and plan review and sends root-cause claims to `diagnose` |

Codex's objection to a separate mode was two owners for bug fixing. The split below removes it: `diagnose` owns the diagnosis, poteto `bug-fix` owns the repair and the PR, and andy-mode `qa` owns the finding record.

## The case file

One Markdown file per case, at `${XDG_STATE_HOME:-~/.local/state}/debug-cases/<repo>/<case-id>/case.md`, with raw artifacts in `artifacts/` beside it. It stays out of git: cases hold private data and large captures. What persists in git is what the close step promotes.

One file is the whole state of the investigation. An agent resuming after compaction, a session pickup, or a fresh subagent after a retraction reads `case.md` and knows where the case stands. Markdown tables are what agents edit well and what Pascal reads directly. Codex proposed five files with JSON and hashes. That buys tamper evidence the evals have not shown a need for, at a cost every case pays.

Sections, each a strict table: header (variable, report, `verify-<app>` path, ladder, current layer), Controls, Facts, Hypotheses, Judgments, Log, Interventions, Decisions, Close. [sources/design-claude.md](sources/design-claude.md) section 4.1 has a filled example from the latency bug.

Column rules that carry the method:

- **Controls** require `differs by`, `matches`, and `not broken the same way because`
- **Facts** require `kind`, `layer`, `field` or `lab`, the reading on the variable and on the control, `source` (probe, host, window, tool version), `artifact`, and `supersedes`. An absence states its coverage in the statement
- **Hypotheses** require `from` (at least one fact) and `killed if` (the prediction). `origin` records `new`, `split:`, `merge:`, `combine:`, `repro`, `human`, or `reviewer`. Combination members may carry a role: `trigger`, `sustaining`, or `vulnerability`. A split or a merge marks its parent `replaced`, so the parent stops counting toward strength
- **Judgments** are append-only. A later row for the same hypothesis and fact supersedes the earlier one and cites why, so a wrong reading of a fact can be corrected without touching the fact. Every `x` cites a fact. Elimination is derived: a hypothesis whose current judgment on a current in-scope fact is `x` is eliminated. If a fact is superseded, the eliminations it caused reopen
- **Log** records each discrimination probe with what each live hypothesis predicted before it ran, each descent with its reason, each repair tactic, and each eliminator pass
- **Interventions** quote every human input that changed course, with a category. The close step fills the destination

Who writes what:

| Part | Agent | Eliminator | Pascal |
|---|---|---|---|
| Facts | Appends rows for saved artifacts or quoted reports. Never edits | Flags gathering defects as `reverify` log rows | Appends observations, retires a fact with a reason |
| Hypotheses | Adds with `from` and `killed if` | Reports facts no hypothesis explains | Adds as `by: human`, judged like any other |
| Judgments | Writes with a reason. Corrects by appending a superseding row | Appends `x` rows citing a fact | Same as the eliminator |
| Decisions | Writes options and a recommended default | None | Chooses |

### A script only if the evals ask for it

`case.py check` would lint the tables, refuse edits to fact rows, render the matrix with strength per signal, and print the next step as one JSON line under the [script output rule](../../../references/script-output.md). Phase 1 ships prose only. The script ships if a Phase 1 eval run shows a miscounted strength, an ignored `x`, a descent without repair tactics, or a lost best finding. [sources/design-claude.md](sources/design-claude.md) section 4.3 has its next-step table.

## Goal 2: a bug arrives

`diagnose`, in order. Each step ends on a condition the agent can check.

0. **Open the case.** Record the requested outcome. A `diagnosis` request stops after step 7 with the decision as a recommendation, and lists repairs and promotions as follow-ups unless Pascal authorizes them. Then pick the path. The inline path fits when the report's own facts leave one plausible cause and one cheap probe can test its killing prediction: skip the case file and the slate of three to seven, and keep the control, the probe's result, the fix parity reading, and the claim level in the reply. Switch to a case file at the first retraction, when two hypotheses survive, or when the bug is in production. Otherwise write the variable precisely, read the project's `verify-<app>` skill (Probes, Controls, Policy, the touched features' Gauges) and past cases for this repo. Open no source file yet
1. **Gather layer 1.** Record every fact the report carries. Run the cheap exclusions first: the deployed build is the one you think, flags and config match between variable and control, the time windows line up, no resource is exhausted, no upstream dependency changed. Then read raw telemetry, config, flags, and the diff between last good and first bad. Fan out across sources and across instances. If the report gives repro steps, run them now: the repro becomes a hypothesis and its readings are lab facts
2. **Choose the control and pair.** Prefer a standing control from `verify-<app>`. Fill the three control columns. Read the same quantities on the control, in both directions, and on a second control when readings vary. If failing instances disagree, cluster them
3. **Hypothesize from signals.** Each hypothesis cites its facts and its killing prediction. Now read code, scoped to the signal: "which paths at the deployed version could produce F6", not "how does the client work". Keep three to seven, plus the `H0` reservation
4. **Judge and steer.** Mark every live hypothesis against every in-scope signal and symptom. Strong signal with one or two hypotheses: discriminate. All weak: descend. Before each discrimination probe, write each live hypothesis's prediction, and skip the probe when the predictions all agree. That rule does not apply to initial collection, re-gathering, validation, or parity readings
5. **Validate.** For the candidate: test its killing prediction, and where it is safe, toggle the suspected cause and watch the strong signal move. Judge it against every in-scope fact including noise and context, check repro parity, test each combination member's necessity, and re-gather the one to three facts the conclusion rests on by an independent path. Then send the eliminator the case file and artifacts, never the transcript, on another model family when available
6. **When stuck.** Repair tactics in order, each logged. Then descend one layer through `verify-<app>` Probes, then the generic ladder. Process captures run through poteto `runtime-forensics`, `trace-forensics`, or Omarchy's `diagnose-crash`, each returning facts. After a retraction, a fresh context hypothesizes from `case.md` alone. After three failed fixes, stop and attack the premise. Stop with claim level `open`, naming the missing observation, when the deepest reachable layer is read, no valid control can be obtained, access is refused, the case's budget is spent, or two descents in a row bring no new signal
7. **Decide.** List fix options with tradeoffs. Apply a matching policy line and cite it, or ask Pascal one question. Rollback, escalation, and dropping support stay human unless policy says otherwise. When the cause sits in a component Pascal does not own, draft the owner's report with every claim citing a fact
8. **Fix and verify.** For a `fix` request only. Hand the repair to poteto `bug-fix` steps 3 to 6 or a plain implementation. The failing check written first must show the strong signal, not just fail. After the fix, on the variable's surface: the strong signal matches the control, the reported symptom is gone, and the other signals show no residual failure. Sweep for other instances of the same pattern
9. **Close.** Give every intervention a destination. Promote each strong signal found below layer 1 through `instrument`, or list it as a follow-up on a `diagnosis` request. State the claim level in the reply

## Goal 1: building a feature

`instrument`, in order.

1. **Find the project's `verify-<app>` skill.** Without one, propose `create-verification-skill` for a user-facing surface
2. **Write the failure model.** For each design assumption, write how its violation would look: "the new path routes by shard like the old one", "an exhausted state machine is never re-entered". Ask `blast-radius`'s question: the one fact this change is safe because of
3. **Pick a gauge or an invariant per row.** Never legitimate: an invariant that fails loudly. Legitimate but the value matters: a gauge with a control value, taken from config where possible. Score each gauge by the strength question: if this reading differed, how many causes could explain it? Keep gauges that answer one or two. Aggregate readings such as latency percentiles or success rate stay in the gate as detectors, never as gauges
4. **Emit by default at the shallowest layer.** Put the readings in the unit of work's one wide record: a CLI's one-line JSON answer, a run manifest, or one structured log line per request. Include what pairs runs: build, flags, host, and fan-out counts such as addresses resolved, backends contacted, and retries. No debug flag. Give every wait a timeout that records what it waited on, so a hang leaves a fact before anyone restarts the process. Budget the cost
5. **Record** the rows in the feature file's `## Gauges` table. That table is the registry: the verifier fails when a registered gauge is missing from a run
6. **Gate.** Detectors decide pass or fail on outcomes. The verifier compares each gauge with the last passing run, or with its config-derived value, under the parity rule. Before the run, declare each gauge the change is meant to move and its new expected value. Parity applies to every other gauge
7. **Prove potency.** On a scratch branch, plant the regression each gauge guards against. The gate must fail on it and pass on the real change

Applied to the post's latency feature before release: step 2 names "the mTLS path routes by shard", and step 7 plants the unsharded client. The gauge must survive that potency proof at pre-production scale. A count of addresses may not: with 2 shards of 1 replica each, the buggy client resolved only 2 addresses, a count a correct client can produce too. So step 3 records the lookups themselves, which names the client resolves and how many answers each returns, compared with the last good run. That is the comparison the post says would have caught the bug before production.

## The eliminator

The reviewer gets `case.md`, the artifacts, and one stage question. It never gets the transcript, the PR text, or the investigator's narrative, which act as framing. It may return only:

- a contradicting fact, as an `x` row citing it
- a defect in a fact's gathering (wrong host, window, tool version, missing coverage), as a `reverify` row
- a control broken the same way as the variable
- a missing discriminating fact: one reading that would split the survivors
- a checked null: "I looked for a contradiction in these facts and found none"

Stage checks follow the post. At the control: does each signal differ from the control beyond the noise floor, is the control broken the same way, how was each fact gathered. At the matrix: how many hypotheses fit each signal, were the repair tactics tried before a new hypothesis, was each descent justified. At validation: one contradicting fact, citations for every claim, and each combination member removed in turn.

The verdict is "eliminated by F#" or "survives F1 to Fn, missing: ...". It is never "confirmed".

## Accretion

The project's `verify-<app>` skill becomes the place every case reads first and writes back to. It gains three sections after Doctor (**Probes** by layer with access level, standing **Controls**, **Policy**) and each feature file gains a **Gauges** table.

| What happened in the case | Lands in | Read next time by |
|---|---|---|
| Pascal supplied a control | `verify-<app>` Controls | `diagnose` step 2 |
| Pascal supplied a fact the agent did not gather | `verify-<app>` Probes, or a context gauge | `diagnose` step 1 |
| Pascal demanded a step ("run the repro", "cite it") | a `debug-mode` eval, through `andy-mode ; retro-skill-usage` | every future case |
| Pascal pushed back from design knowledge | an invariant in product code, through `instrument` | the gate and `diagnose` step 1 |
| Pascal ran a command for the agent, or the agent lacked access | `verify-<app>` Probes with access, through `andy-mode ; retro-global` | `diagnose` descents |
| Pascal made a decision | `verify-<app>` Policy | `diagnose` step 7 |
| A strong signal was found below layer 1 | a feature gauge at layer 1 plus its gate, through `instrument` | build-time gate, `diagnose` step 1 |
| Evidence was destroyed before capture | a timeout that records its wait, in product code | `diagnose` step 1 |

A case cannot close while an intervention has no destination. `declined: <reason>` is a valid destination, so the rule forces a decision, not busywork. A category seen in two cases of the same repo becomes structure (a probe, a gauge, a gate, a policy line, or an eval), never a prose reminder. One line per closed case goes to `${XDG_STATE_HOME}/debug-cases/index.jsonl`: interventions per case by category is the measure of how agent-native a project is.

Method gaps go to `debug-mode` only through an eval built from the real case, so the skill grows only where a run failed. That reuses andy-mode's retro routes instead of a new mechanism.

Every artifact in the system has a reader, and something branches on it. The case file drives the next step. Gauges drive the gate. The index drives repeat detection. An artifact without a reader is ceremony and gets cut.

## Changes to existing skills

All paths are under `authoring/`.

| File | Change | Why |
|---|---|---|
| `poteto/poteto-mode/playbooks/bug-fix.md` | Steps 1 and 2 become "run `debug-mode ; diagnose` steps 0 to 7". Step 4 verifies by fix parity. The closing "Investigation fans out `how` + `why`" runs only after `diagnose` isolates a signal, scoped to it. Keep steps 3, 5, and 6 | Code-first seeding and repro-as-truth contradict the post |
| `poteto/poteto-mode/SKILL.md` | The bug-fix non-negotiable points to `diagnose` and keeps "reproduce yourself on the same surface", with parity. The `how` trigger for a nontrivial change or "are we sure?" excludes runtime failures, which gather facts through `diagnose` before any source reading | One entry point for diagnosis |
| `poteto/poteto-mode/principles/fix-root-causes.md` | "Reproduce first" becomes "facts and a control first, then reproduce with parity". "Ask why until the root cause" becomes "the hypothesis or minimal combination that explains every signal and that no fact contradicts". "When stuck, instrument" becomes "when stuck, descend one layer". Keep the restart-bug and pattern-sweep advice | Five Whys invites narrative depth and hides combinations |
| `poteto/poteto-mode/playbooks/runtime-forensics.md` | Capture the same signal on a control process when one exists. Inside a case, return facts. Live hotfixes or CDP injection on a daily-driver or production surface need explicit authority | Control first; Pascal's production rule |
| `poteto/poteto-mode/playbooks/trace-forensics.md` | Get the paired control capture first, or name why none exists. A cited cause at a boundary Pascal does not own is a valid diagnosis without that component's source | The hang was solved without the auth daemon's source |
| `poteto/poteto-mode/playbooks/perf-issue.md` | A slowdown with a known-good control is a regression: run `diagnose`. This playbook is for making something faster against a baseline | Two owners for regressions otherwise |
| `poteto/poteto-mode/playbooks/feature.md` | After `architect`, run `debug-mode ; instrument`. The Builder emits the gauges. Step 5 verifies through the gate | Goal 1 entry point |
| `poteto/poteto-mode/playbooks/investigation.md` | A question about why something fails at runtime routes to `diagnose` | Read-only diagnosis has one home |
| `poteto/how/SKILL.md` | In a debugging case, run after facts isolate a signal, and ask which paths could produce it | Keeps `how` scoped to a signal |
| `poteto/interrogate/SKILL.md` and `references/lead-judgment.md` | Root-cause claims go to the eliminator. Agreement among reviewers is a shared reading, not proof. One cited contradiction outranks any number of agreeing reviewers | The cert-reload theory survived an independent reviewer |
| `poteto/interrogate/references/rubric.md` | A bug-fix PR cites the signal that found the cause and shows it restored on the same surface. A fix justified by reading code alone is a hypothesis | Catches non-fixes in review |
| `poteto/principle-prove-it-works/SKILL.md` | For a fix or a regression check, the proof is parity: the reading that differed now matches the control on the same surface | Tests passing is necessary, not sufficient |
| `poteto/create-verification-skill/SKILL.md` and `references/feature-map-example/` | The interview asks where each layer is read and at what access. The generated skill gains Probes, Controls, and Policy. Feature files gain a fifth H2, `Gauges`. The proof run writes `gauges.json` | Makes `verify-<app>` the accretion home |
| `poteto/maintain-verification-skill/SKILL.md` | The live pass compares each feature's gauges with the last passing run. A feature without gauges is a gap routed to `instrument` | Keeps gauges honest |
| `poteto/show-me-your-work/SKILL.md` | A skill that keeps a typed record, such as the case file, keeps it and applies this skill's audit and review steps to it | Avoids a second audit format fight |
| `andy/andy-mode/playbooks/qa.md` | The bounded diagnosis loop keeps phases 1 and 2 (feedback loop, capture the symptom). When the cause matters to the finding, phases 3 and 4 hand off to `diagnose` | Removes the sixth copy of the method |
| `verify-loops/verify-video-archive/` | Pilot: `parallel-batch` and `interruption` gain Gauges, and the verifier writes `gauges.json` and compares it with the last passing manifest | Its manifest already records peak simultaneous media processes, peak RSS, and CPU, so the first gauges cost little |

Reused as they are: `why` (history and postmortems as fact sources, read as hypotheses, never as anchors), `blast-radius` (fix review and the safety fact for `instrument`), `swarm` (fan-out of fact gathering), `tdd` (failing check first), `arena` (competing fix designs), `figure-it-out`, `grill-for-unknowns` (the shape of the one question to Pascal), `code-review-mode`, Omarchy's `diagnose-crash` (the core-dump probe).

## Rejected and deferred

Rejected:

- Consensus, or "N reviewers agree", as verification anywhere
- Probability scores on hypotheses. Counts and contradictions decide without fake precision
- One skill per debugging tool. A tool is a probe at a layer, a row in `ladders.md`
- A local full-stack replica as a source of facts that outranks field facts
- Committing raw case files to repositories
- Activating the archived Jeffrey skills. Their best ideas are restated here: the match, state, and randomize axis table for controls, falsifiers on hypotheses, potency checks on negatives and gates, parity by normalized top frames, and hang capture recipes

Deferred until a real case asks for it:

- `case.py` (see above)
- A run record for every CLI invocation, one JSON line in the state directory: the post's default collection, adopted per tool when a case needed a fact a run record would have held. It would live in `coding-standard`
- A bug-report template that asks for last good and first bad versions, flags, artifacts, and unaffected instances, through `label-for-issues`
- Production access tooling beyond the Probes access column
- Canary analysis beyond the verifier gate
- A cross-machine case index
- brigade-mode's cook SOP calling `instrument`

## How the three designs compared

| Question | Lead | Codex | Claude | Decision |
|---|---|---|---|---|
| Kernel | Facts constrain hypotheses; one comparison at both ends of time | The evidence contract: a claim names what would refute it | The fact, which the agent cannot write | All three, stated together |
| Package | `debug-mode` with three routes | Helper `evidence-loop`, a poteto-mode route, an `interrogate` branch | `debug-mode` with two routes | Claude's |
| Case artifact | One Markdown file | Five files with JSON and hashes | One Markdown file, script later | One Markdown file |
| Matrix cells | explains, silent, contradicts, unknown | explains, consistent, contradicts, unknown | `+`, `0`, `x`, blank | Claude's marks with the shared meaning |
| Build-time record | Signals section per feature | JSON contract per feature | Gauges table per feature | Gauges table |
| Gate proof | not covered | Sensitivity check | Potency proof | Potency proof |
| Claim levels | not covered | Five evidence states | Close section | Codex's levels, simplified |
| Review | A refute route | `interrogate` evidence branch | Eliminator prompt in `diagnose` | Eliminator prompt |
| Accretion | Routes plus andy-mode retros | Accretion rows per case | Destination table, close gate, index | Claude's, through andy-mode retros |

The survey added the bidirectional signal, the noise floor, the pre-registered prediction before each probe, the `H0` reservation, coverage on absences, cause roles, clustering for separate bugs, the fresh context after a retraction, and the independent re-gathering of the facts a conclusion rests on.

A separate Codex review of this page, briefed only to eliminate, found 19 defects. All 19 are fixed in this version. The largest: diagnosis requests no longer reach repair, `confirmed` and `fixed` need stronger evidence, rejected repros no longer constrain the field diagnosis, the investigation has exits, and the latency gauge records lookups instead of a count that ties at pre-production scale. [sources/review-codex.md](sources/review-codex.md) lists them.

## Open questions for Pascal

1. **Production access.** For your projects, production is the fleet. May `diagnose` run read-only probes over SSH on om1, mbp, and the Mini without asking, each run recorded as a fact? The answer sets the first Policy line
2. **Case records in git.** Raw cases stay local. Should a one-page summary of each closed case be committed per project, so agents on other machines can read past cases, or is the promoted material enough?
3. **Policy home.** This design puts Policy in each project's `verify-<app>` skill, loaded only when debugging. Should it go in the project's `AGENTS.md`, read on every task?
4. **Shape and names.** One mode, `debug-mode`, with routes `diagnose` and `instrument`, against your first instinct of two skills
5. **Eval budget.** Phase 0 to 2 runs four scenarios on two agents at three refs, about 24 agent sessions, some long. Run Phase 0 on both agents, or one?
