# Design: an agent-native debugging system distilled from "How to effectively debug when you no longer understand the code"

Designer: Claude (Opus 5.5), 2026-10-13. Source: Cindy Sridharan, published 2026-10-10, <https://copyconstruct.medium.com/how-to-effectively-debug-when-you-no-longer-understand-the-code-bd3dcb2c5f7b>. Everything below restates her ideas in our own words. No sentence of the post is reused in a skill.

## 0. The recommendation on one screen

Build **one new mode, `debug-mode`, with two routes**, extend **the project-local verification skill** into the project's "factory floor manual", and make small routing edits to seven existing skills.

- `debug-mode ; diagnose` runs at bug time (Goal 2). It opens a **case file**, gathers **facts** before reading code, picks a **control**, keeps a **hypothesis-by-fact matrix**, steers by **signal strength**, descends **one layer at a time**, uses an **eliminator** subagent that may only kill hypotheses, accepts a repro only with **signal parity**, verifies a fix by **parity on the same surface**, and refuses to close until every **human intervention** is routed to a durable fix.
- `debug-mode ; instrument` runs at build time (Goal 1). For a feature, it names the **gauges** (countable readings with a known control value) and **invariants** whose difference would be a strong signal, emits them at the shallowest default layer, records them in the feature map, and adds a **parity gate** that is proven to fail on a planted regression.
- The project's `verify-<app>` skill (made by `create-verification-skill`) gains three sections (**Probes** by layer, standing **Controls**, **Policy**) and each feature file gains a **Gauges** table. It becomes the one place every future agent reads first, and the place every closed case writes back to. That is the accretion loop.
- One stdlib script, `case.py check`, lints the case file, keeps facts append-only, renders the matrix, and answers in one JSON line with the next step. It ships only if prose-only evals show the agent miscounting or skipping steps (Phase 2).

The tower rests on **the fact**: an observation an instrument made, which the agent can cite but never write. Everything above it either makes facts cheaper to get, compares them, or is judged by them.

What I reject: a separate adversarial-review skill for debugging, consensus as verification, per-tool skills (gdb, heaptrack), "full stack in a box" repro harnesses, probability scores on hypotheses, and any build-time machinery before a pilot shows a gate catching a planted regression.

---

## 1. Knowledge extraction

Markers: **[N]** novel relative to the existing skills; **[P: x]** partly present in skill x; **[E: x]** already present in x; **[C: x]** conflicts with x (resolved in section 7). "Applies" names where the principle lands in the proposed system.

### Vocabulary and stance

1. Name three roles before investigating: the variable (the failing case), the control (the comparison case), and the signal (a data point that may explain the difference). Applies: diagnose step 0-2. [P: poteto `trace-forensics` step 5 "paired capture"]
2. Every hypothesis worth pursuing starts from a high-fidelity signal, never from a reading of the code. Applies: hypothesis rows must cite the fact they start from. [N] [C: poteto `bug-fix` step 2]
3. Lean into what agents do better than people: chewing through large raw data, correlating across layers, knowing obscure tools and formats, rerunning checks without fatigue, and writing throwaway tooling. Applies: diagnose gathering and fan-out. [N]
4. Do not make the agent debug the way a person would (local repro first, pattern-match old postmortems first); those are human habits, not agent strengths. Applies: diagnose step 1 ordering. [N]
5. Guard against the agent's known failures: stories built on thin evidence, fixation on rare edge cases, and losing track of its own best finding. Applies: matrix, citations, repro parity, `case.py`. [P: poteto `bug-fix` "belt-and-suspenders is a hypothesis"]
6. Code says what can happen, not what did happen, so reading code is the last step of hypothesis formation and is scoped to explaining a named signal. Applies: diagnose step 3. [P: poteto `runtime-forensics` "don't theorize from source", `perf-issue` "don't read source instead of measuring"] [C: poteto `bug-fix` step 2, `investigation`]
7. Which code snapshot the agent reads is itself a source of error; the deployed version is a fact to record, the code's behavior is a hypothesis. Applies: case facts of kind `context`. [N]
8. Human pushback does not scale as a guardrail, because people understand agent-written code less and less. Applies: the design goal of zero interventions. [N]

### The two tiers and constraints

9. Treat debugging as constraint satisfaction: find the one hypothesis consistent with every constraint, not a plausible one. Applies: matrix row reading. [N]
10. Keep two tiers: facts gathered by tools and reports, and everything the agent derives from them (hypotheses, conclusions, narratives). Applies: the write rule. [P: `why` epistemics tiers, `blast-radius` proof ladder]
11. Facts are immutable to the agent; if a fact looks wrong, the agent asks for it to be gathered again and never edits or argues it away. Applies: append-only facts, `reverify` log rows. [N]
12. Gather facts from every available source: errors, crashes, stacks, profiles, telemetry, traces, kernel data, DNS, blackbox measurements, counters, user reports, configs, flags, dependency and deploy versions, VCS history, platform and sidecar configs. Applies: diagnose step 1, ladders. [P: `why` seven evidence categories]
13. Every fact is a constraint; one contradicting fact discards a hypothesis. Applies: `x` marks. [N]
14. Most bugs have one cause; scale or environment is usually the condition under which it shows, not a second cause. Applies: context facts. [N]
15. A multi-cause hypothesis is valid only when the causes together explain every fact and each cause is strictly necessary, so removing it leaves some fact unexplained. Applies: combination rows and the necessity check. [N]
16. Never rescue a hypothesis by making it more elaborate to explain away an inconvenient fact. Applies: eliminator duty. [N]

### Steering and validation

17. Do not try to validate every hypothesis; steer to the most promising one as early as possible. Applies: `focus` in `case.py` output. [P: poteto `bug-fix` "take the split that cuts the most"]
18. Run three steps: isolate high-fidelity signals, isolate the most promising hypothesis, validate it against every fact. Applies: diagnose steps 2-5. [N]
19. A data point present in the variable and absent from the control is a high-fidelity signal; one present in both is noise. Applies: fact kinds `signal` and `noise`. [N]
20. Noise still eliminates: anything also present in the control cannot be what broke the variable. Applies: hypotheses built on noise get `x`. [N]
21. Without a control the agent cannot tell signal from noise; whittling data down is the control's main job. Applies: `next: control` comes first. [N]
22. The ideal control differs from the variable in exactly the suspected factor. Applies: control record `differs by` and `matches`. [N]
23. For simple bugs the happy path is a good control; for tricky ones a louder sad path that fails differently is often better and cheaper, since it often sits in data you already have. Applies: control types. [N]
24. A control is only as good as the confidence that it is not broken the same way as the variable. Applies: required `not broken the same way because` column. [N]
25. A signal is strong when very few hypotheses explain it (ideally one) and weak when many do. Applies: strength = count of live hypotheses with `+`. [N]
26. Build a hypothesis-by-fact matrix: read columns to rank signals, read rows to test hypotheses. Applies: the case file and `matrix.md`. [N]
27. Service-level aggregates (P99, error rate) are usually weak signals: they describe the symptom without locating the cause. Applies: instrument rejects SLO-only gauges; diagnose does not stop at them. [N]
28. When no row survives, the hypothesis set is wrong; before inventing new ones, try in order: re-gather suspect facts, split coarse hypotheses, merge too-fine ones, combine complementary ones, then a new hypothesis drawn only from existing facts. Applies: `tactics`. [N]
29. Split a coarse hypothesis ("the deploy did it") into parts so one contradicting fact does not kill the part that is true. Applies: `split:` origin. [N]
30. Merge many per-instance hypotheses ("host 17 disk", "host 42 GC") into the shared-entity hypothesis that explains them all. Applies: `merge:` origin. [N]
31. Combining differs from merging: both hypotheses stay, each explains what the other cannot, and each must stay necessary. Applies: `combine:` origin. [N]
32. When every signal is weak or tactics are exhausted, gather facts one layer down instead of generating more hypotheses. Applies: `descend`. [P: `fix-root-causes` "when stuck, instrument"]
33. Start with the cheapest layer (the report, logs, telemetry, config) and stop descending at the first strong signal: the strongest, not the deepest. Applies: ladders and `descend`. [N]
34. Each stack has its own ladder of layers (container service, desktop app, web app, mobile app). Applies: `references/ladders.md`. [N]
35. Each layer narrows what the next one has to explain. Applies: pairing new readings with the same control. [N]
36. Validate the candidate against every fact including noise; with too few facts several hypotheses survive and the job is to gather a fact that tells them apart. Applies: `validate` and `discriminate`. [N]

### Fat facts, thin hypotheses

37. Keep the factual tier fat: many kinds of data from many sources, and the same kind of data from many instances of the bug. Applies: swarm fan-out across sources and instances. [N]
38. A pattern repeated across instances and absent from the control is likely real, not coincidence. Applies: instance count in fact statements. [N]
39. Turn signal isolation into arithmetic: bytes, files opened, DNS answers, RPC counts, time to first byte. Applies: facts state numbers for both sides. [N]
40. Keep the derivative tier thin; a fat one means too few constraints or constraints that too many hypotheses satisfy. Applies: `case.py` warns past 7 live hypotheses. [N]

### Repros

41. A repro is a hypothesis: it proves a bug exists, not that it is the reported bug; facts from the field outrank it. Applies: repro rows have origin `repro`. [N] [C: poteto `bug-fix` steps 1 and 4]
42. Still attempt a repro, and run the one a report provides before theorizing. Applies: diagnose step 1. [E: poteto `bug-fix` step 1, poteto Non-negotiables]
43. Accept a repro only if it shows the strongest signal of the real report; a repro that fails parity is noise and leaves the case. Applies: repro parity in `references/parity.md`. [N] [P: `tdd` "fails for the intended reason"]
44. Synthetic harnesses and non-production environments deserve extra suspicion. Applies: facts tagged `field` or `lab`. [N]

### Adversarial review

45. A reviewer cannot vouch that the fact base is complete, so it cannot detect missing constraints. Applies: the eliminator's brief and its forbidden verdict "confirmed". [N] [C: implicit in `interrogate`]
46. A reviewer with the same model and context as the investigator is one opinion counted twice. Applies: eliminator gets the case file, not the transcript, and a different model family when available. [E: `interrogate`, `arena` same-model caveat]
47. Use adversarial review to eliminate, never to verify; one contradicting fact is enough. Applies: eliminator output. [N]
48. At the signal step the reviewer checks that signals are absent from the control, that the control is not broken the same way, and how each fact was gathered (host, window, tool version). Applies: eliminator checklist. [N]
49. At the hypothesis step the reviewer estimates how many hypotheses fit each signal, reads rows, checks that split, merge, and combine were tried before new hypotheses, and that each descent was justified. Applies: eliminator checklist. [N]
50. At the validation step the reviewer demands a citation to a fact for every claim and culls uncited ones; for a combination it names the failing member and removes each cause to test necessity. Applies: eliminator checklist. [P: `why` citations, `blast-radius` file:line]

### The factory

51. Every human intervention is a gap in the process, and interventions per bug is the honest measure of how agent-native the factory is. Applies: `Interventions` table, case index. [P: `encode-lessons-in-structure` "capture every correction"]
52. Optimize the factual tier for agents (raw, unaggregated, more of it) and decision points for people, then turn decisions into policy. Applies: Policy section in the manual. [N]
53. Aggregation that helps a person read a dashboard destroys signal for an agent. Applies: probes prefer raw data. [N]
54. Give agents graduated access to data: read-only by default, scoped to the case, time-limited, load-aware, privacy-scrubbed, auditable. Applies: probe `access` column; facts record host and command. [N]
55. Decisions with accountability (rollback, escalate to another team, drop support) stay human until codified as policy. Applies: diagnose step 7. [P: poteto Autonomy "always pause for irreversible writes"]
56. When fixes have different tradeoffs, present every option unambiguously with reasoning. Applies: Decisions table, question shape from `grill-for-unknowns`. [P: poteto `feature` reply tables, `grill-for-unknowns`]
57. Designing verification matters more than understanding code; the human's real contributions were a control, a constraint, and a refusal. Applies: the mode's framing. [N]
58. Designing a verification loop needs system knowledge: what a regression looks like and how to measure it. Applies: instrument's failure model. [P: `create-verification-skill` "observable end state"]
59. Decide the signals during planning, before code, and make the strongest available at the shallowest layer collected by default. Applies: instrument route; poteto `feature` step. [N]
60. The factory should help agents gather better facts at the right layer, not make code more readable to them. Applies: Probes section. [N]
61. Collect by default rather than on demand: always-on deep collection on a subset of hosts, even a production slice reserved for agent experiments. Applies: deferred run-record idea. [N]
62. People should set policy, not act as meat proxies who paste text and run commands for the agent. Applies: `proxy` intervention category routes to Probes with access. [P: poteto "never hand the repro to the user"]
63. When an agent could have done the step but did not, make it infrastructure, not a prompting skill held by one person. Applies: interventions route into evals and skill edits. [P: `encode-lessons-in-structure`]
64. Verification must check signals, not only passing tests. Applies: parity in `prove-it-works`. [P: `principle-prove-it-works`]
65. Develop against production: an isolated slice with read-only access to real signals, so a change meets real behavior early. Applies: Probes reach where users run the code (for Pascal, the fleet machines). [N]
66. Running the whole stack locally is the wrong base for debugging, because the factual tier cannot be faithfully recreated. Applies: lab facts never outrank field facts. [N]
67. Reuse the method for integration tests, E2E, pre-deploy gates, and canary analysis: compare every gauge against the last good run instead of a pass/fail bit. Applies: instrument's parity gate. [N]

### Lessons inside the three stories

68. Tests passed in both the latency and the leak bugs because no test asserted the invariant that broke (sharded routing in the new path; single use of the state machine); make such invariants loud. Applies: instrument invariants. [P: `encode-lessons-in-structure`, `test-behavior-not-implementation`]
69. A smaller environment (2 shards against 5x80) hides scale bugs; record scale as context and compare gauges against config-derived control values, which catches the bug even at small scale. Applies: parity rules relative to control. [N]
70. Restarting a stuck process destroys the evidence; capture state before restart, and design waits to leave a record when they time out. Applies: ladders caution; instrument invariant pattern. [N]
71. "No logs" is a fact; "therefore no request arrived" is another team's hypothesis. Provenance from a person does not make a claim a fact; only an observation does. Applies: facts versus `by: human` hypotheses. [N]
72. When the cause sits in a component you do not own, the deliverable is an evidence-cited report to its owner. Applies: diagnose step 7. [N]
73. Agents can satisfy a checklist cosmetically ("empty calories"); a fix PR must cite the signal that found the cause and show it restored. Applies: `interrogate` rubric line, close gate. [N]

---

## 2. The system

### 2.1 The single concept

**The fact.** A fact is an observation an instrument (a probe, a report, a person's direct observation) made, with its provenance and raw artifact. The agent cites facts and never writes, edits, or deletes them. The write rule follows: instruments write facts, the agent writes hypotheses, and nothing moves from the hypothesis tier to the fact tier except a new observation.

Every layer of the tower is defined by its relation to facts:

- Vocabulary names facts and what is derived from them.
- Observation produces facts (probes, gauges).
- Comparison turns pairs of facts into signals or noise (run time) or parity verdicts (build time).
- Inference judges hypotheses against facts.
- The control loop decides which fact to gather next.
- Decision applies policy to a fact-validated cause.
- Accretion moves the facts the last case needed to a shallower, cheaper, default place.

### 2.2 Shared vocabulary (`references/glossary.md`)

One term per concept. These are the only words the skills use for these ideas.

| Term | Meaning |
|---|---|
| case | One investigation of one reported failure, recorded in one case file |
| variable | The failing case, scoped: which hosts, users, versions, time window |
| control | A case compared against the variable; ideally identical except the suspected factor. Types: `happy`, `sad` (fails differently and louder), `baseline` (last good version or run) |
| fact | An observation with provenance and a raw artifact. Immutable to the agent |
| fact kind | `signal` (differs between variable and control), `noise` (same in both), `symptom` (seen on the variable, no control reading yet), `context` (a condition: version, flag, config, scale) |
| field / lab | Where a fact came from: the real failing environment, or a repro or harness. Lab facts never outrank field facts |
| layer | One level of a stack's ladder, from the cheapest (report, logs) to the deepest (kernel) |
| probe | A command that reads one layer and saves its output as an artifact |
| gauge | A named, countable reading a feature emits, with a known control value (example: addresses returned per shard lookup = shard count). Not limited to the Prometheus gauge type |
| invariant | A gauge whose control value is zero violations, enforced loudly in code |
| hypothesis | A derived claim of cause, with a mechanism, the facts it starts from, and a falsifier |
| falsifier | The observation that would kill a hypothesis if it came back a certain way |
| judgment | One cell: hypothesis H against fact F, marked `+` explains, `x` contradicts, `0` silent (consistent but does not explain) |
| strength | For a signal or symptom: how many live hypotheses explain it. Strong = 1 or 2, weak = 3 or more |
| candidate | A live hypothesis that explains every signal and symptom and contradicts no fact |
| combination | A set of partial hypotheses that together explain every signal and symptom, each necessary |
| tactic | One of the five moves when no candidate exists: reverify, split, merge, combine, new-from-facts |
| descend | Gather facts one layer down, then pair them with the same control |
| repro | A hypothesis of the form "this setup produces the reported failure" |
| parity | Two readings agree under a stated rule (equal, within tolerance, same normalized stack). Repro parity, fix parity, gate parity |
| eliminator | An independent read-only reviewer that may only eliminate hypotheses or flag defects |
| intervention | Any human input that changed the course of a case |
| route | Where an intervention or a promoted signal lands so the next case does not need it |
| manual | The project's `verify-<app>` skill: launch, drive, Probes, Controls, Policy, feature Gauges |
| policy | A recorded human decision the agent applies next time without asking |
| gate | A parity check on gauges between a baseline run and a candidate run |

Note on marks: `x` means "if this cause were active, this fact could not have been observed". `0` means "this cause alone does not produce this fact". The difference matters for combinations: in the post's capacity-drop example, "capacity drop" is `0`, not `x`, on "overload persisted after capacity returned", which is why it can combine with "unbounded retries".

### 2.3 The tower

```
L6  ACCRETION    close -> routing table -> manual (Probes, Controls, Policy),
                 feature Gauges + gate, code invariants, debug-mode evals, case index
                     | read first by the next case (L1, L2, L5) and by build-time gates
L5  DECISION     fix options + policy lookup -> human decision -> new policy line
L4  CONTROL LOOP gather -> pair -> hypothesize -> judge -> steer/validate/discriminate
                 -> tactics -> descend          [diagnose playbook, eliminator, case.py next]
L3  INFERENCE    hypotheses x facts -> judgments -> matrix -> strength, candidates,
                 combinations                   [case.md, case.py check -> matrix.md]
L2  COMPARISON   variable vs control (run time) | candidate vs baseline (build time)
                 -> signal / noise / parity      [references/parity.md]
L1  OBSERVATION  probes read layers; features emit gauges; every reading is a fact
                 with provenance                 [references/ladders.md, manual Probes, Gauges]
L0  VOCABULARY   glossary + the write rule       [references/glossary.md, SKILL.md]
```

Build time uses L0, L1, L2, and L6 (instrument writes gauges; the gate compares). Run time climbs all seven. The same L2 operation, compare a variable against a control reading by reading, serves both: a gate is a diagnosis that found no signal.

### 2.4 Shared artifacts

| Artifact | Scope | Location | Written by | Read by |
|---|---|---|---|---|
| `case.md` | one case | `${XDG_STATE_HOME:-~/.local/state}/debug-cases/<repo>/<case-id>/case.md` | agent (facts append-only), human, eliminator (judgment rows) | agent, eliminator, `case.py` |
| `artifacts/` | one case | beside `case.md` | probes | eliminator, reverify |
| `matrix.md` | one case | beside `case.md` | `case.py check` only | agent, eliminator, human |
| `.case.lock` | one case | beside `case.md` | `case.py check` only | `case.py` (fact immutability) |
| `index.jsonl` | one machine | `${XDG_STATE_HOME}/debug-cases/index.jsonl` | close step | close step of later cases, Pascal |
| manual sections | one project | `verify-<app>/SKILL.md` Probes, Controls, Policy | instrument, close, human | diagnose steps 0, 2, 7 |
| `## Gauges` | one feature | `verify-<app>/features/<feature>.md` | instrument | diagnose step 1, verifier gate |
| `gauges.json` | one verifier run | the verifier's evidence dir | the verifier | the gate, diagnose step 1 |
| evals | debug-mode | `debug-mode/evals/` | close (from real failures) | eval runner |

### 2.5 Control and data flow

```
                      bug report / failing gate / claimed diagnosis
                                        |
                                        v
  manual (Probes, Controls, Policy, Gauges) --read--> [diagnose]
  past cases (index.jsonl, why: postmortems) --read-->     |
                                        |  writes case.md (facts, hypotheses, judgments, log)
                                        v
                               case.py check --> matrix.md + {"next": ...}
                                        |
      +-----------------+---------------+---------------+------------------+
      |                 |               |               |                  |
   gather/pair     hypothesize      validate        tactics            descend
   (swarm fan-out,  (how, scoped    (falsifier      (reverify,        (ladder layer+1,
    probes, why)    to a signal)    fact, repro     split, merge,      forensics playbooks,
                                    parity,         combine)           diagnose-crash)
                                    eliminator)
                                        |
                                        v
                    decide (policy or one question) -> fix (poteto bug-fix 3-6, tdd)
                                        |
                                 fix parity fact
                                        |
                                        v
                close: route interventions -> instrument (gauge + gate), manual edits,
                       invariants, eval scenario, index line
                                        |
                                        v
                                  [instrument] <--- poteto feature, maintain-verification-skill,
                                        |           Pascal at build time
                                        v
                 feature Gauges + emission code + gate + potency proof + baseline gauges.json
```

### 2.6 Why this is ergonomic from the driver's seat

I imagined running a case at 2 a.m. after a context compaction.

- One file tells me where I am (`case.md`) and one command tells me what to do next (`case.py check`). Resuming after compaction, a session pickup, or a pause needs no memory: the case file is the checkpoint.
- The write rule removes a class of judgment calls. I never wonder whether I may "correct" a fact; I log a reverify row.
- The matrix makes my known weaknesses visible. I cannot walk past my best finding, because strength is computed and printed as `focus` every time.
- Resources go where the matrix points. Fan-out is for gathering facts (cheap, parallel, and the place agents shine). Hypothesis work stays thin and serial. I stop descending at the first strong signal.
- Every project answers the same three questions in the same place: how do I read layer N here (Probes), what do I compare against (Controls), what may I decide alone (Policy). Without that, each case re-learns the project.
- Progressive disclosure: `SKILL.md` routes; each playbook carries its steps; glossary, ladders, parity, eliminator, and routing load only at the step that needs them.

---

## 3. Skill inventory

### 3.1 New: `debug-mode` (the only new skill)

- **Location:** `~/projects/skills/authoring/andy-devtools/debug-mode/` (public repo, Pascal's own dev category). `kind: "dev"`, no `role` (Pascal invokes it directly, and it auto-triggers).
- **Frontmatter:**

```yaml
name: "debug-mode"
description: "Use when a bug, regression, crash, leak, hang, timeout, or latency spike needs its root cause, when asked why something is slow, leaking, hanging, or failing in production, when someone's diagnosis, repro, or bug fix needs checking, or when a feature being built should emit what a future debugger will need. Routes: `diagnose` and `instrument`, as in `debug-mode ; diagnose`."
kind: "dev"
```

- **Purpose:** find root causes from facts, and make every feature and every case leave facts cheaper for the next agent.
- **Package:**

```
debug-mode/
  SKILL.md                  route picker, the write rule, where cases live, credit (about 80 lines)
  playbooks/diagnose.md     Goal 2, auditing a claimed diagnosis, and close
  playbooks/instrument.md   Goal 1, and promotion from a closed case
  references/glossary.md    section 2.2
  references/case-file.md   template, rules, who writes what (section 4)
  references/ladders.md     ladders per stack, generic probes per layer, cautions
  references/parity.md      comparing readings: rules, normalization, repro/fix/gate parity
  references/eliminator.md  the reviewer brief
  references/routing.md     intervention category -> destination table
  scripts/case.py           Phase 2 only: check = lint + lock + matrix + next
  scripts/tests/test_case.py
  evals/evals.json, evals/fixtures/{latency,leak,hang,instrument}/
```

- **Why one new skill, and why a mode:** the two routes share the glossary, the parity rules, the ladders, and the case-to-gauge promotion. Splitting them into two skills would duplicate those references or create a cross-skill dependency that drifts. Folding them into `poteto-mode` fails because poteto-mode is explicit-invocation only, so a plain "prod is slow, debug it" would never reach the method. Folding diagnosis into `interrogate`, `how`, or `figure-it-out` changes those skills' jobs.
- **Calls:** project manual (read), `why` (history and postmortems), `swarm` (fan-out gathering), `how` (scoped code mapping after signals), poteto `runtime-forensics` and `trace-forensics` and Omarchy's `diagnose-crash` (process-layer probes), `grill-for-unknowns` (question shape for decisions), `blast-radius` (fix diff), `tdd` and poteto `bug-fix` steps 3-6 (fix), `principle-prove-it-works`, `create-verification-skill`, `writing-for-agents` (eval and edit from a case).
- **Called by:** Pascal, poteto `bug-fix`, `runtime-forensics`, `trace-forensics`, `perf-issue` (regressions), `feature`, `investigation` (runtime failures), `maintain-verification-skill` (features without gauges), `interrogate` (root-cause claims).
- **Credit block in SKILL.md:** "Distilled from Cindy Sridharan, *How to effectively debug when you no longer understand the code* (2026-10-10), <URL>. Restated in our own words."

#### Route `diagnose`

- **Playbook description:** "Find the root cause of a reported failure from facts, a control, and a hypothesis-by-fact matrix; verify the fix by signal parity; route every lesson."
- **Inputs:** a bug report, failing gate output, alert, or a claimed diagnosis, repro, or fix PR to audit.
- **Outputs:** `case.md` with a validated cause (or combination), a fix or an evidence-cited report to the owning team, a post-fix parity fact, and routes for every intervention.
- **Reads:** manual, `index.jsonl`, `why` results, artifacts. **Writes:** `case.md`, `artifacts/`, an index line; through close: manual edits, gauges via instrument, eval scenarios.
- **Audit entry:** a claim to check is recorded as a hypothesis (`by: human`, `by: agent`, or origin `repro`) and the route runs from step 0. The verdict is "eliminated by F#" or "survives F1..Fn; missing: ...". Never "confirmed" from review alone.

#### Route `instrument`

- **Playbook description:** "Choose the gauges and invariants a feature emits at the shallowest default layer, record them in the feature map, and gate them by parity."
- **Inputs:** a feature plan or diff, or a promoted signal from a closed case.
- **Outputs:** emission code in the feature diff, the feature file's `## Gauges` rows, a gate, a baseline `gauges.json`, and a potency proof (the gate failed on a planted regression).
- **Reads/writes:** the manual and feature files; the verifier.
- **Calls:** `create-verification-skill` when no manual exists, `blast-radius` (the one fact the change is safe because of becomes an invariant), the project verifier, `principle-prove-it-works`.
- **Called by:** poteto `feature`, diagnose close, `maintain-verification-skill`, Pascal.
- **Why not fold into `create-verification-skill` or `maintain-verification-skill`:** create runs once per project and maintain audits drift; neither runs when a single feature is being built. Instrument's core judgment (what reading would be a strong signal) is a debugging judgment and needs the glossary. The format of the Gauges table stays defined once, in create-verification-skill's feature contract, and instrument points to it.

### 3.2 Not new skills, deliberately

| Considered | Decision | Reason |
|---|---|---|
| A debugging adversarial-review skill | `references/eliminator.md` inside debug-mode | It is one prompt used at one step |
| A "close the gap" accretion skill | Close step of diagnose + `references/routing.md` | Its only input is a case; `reflect` covers conversation-mined lessons |
| A parity-gate skill | Instrument step + project verifier | The gate lives where the verifier lives |
| Per-tool skills (gdb, heaptrack, lsmp) | Rows in `references/ladders.md` | A tool is a probe at a layer, not a workflow |
| A per-project "factory" skill | Sections in the existing `verify-<app>` | One manual per project, already generated and maintained |

---

## 4. Artifacts

### 4.1 The case file (`case.md`)

Markdown is the source of truth: agents edit tables natively, humans read it directly, and there is one file to resume from. `case.py` (Phase 2) parses the strict tables. A cell never contains `|`.

```markdown
# Case 2026-10-13-p99-mtls: client and server P99 rose after mtls_v2 on cluster A

- Variable: ~5000 clients in DC-A with mtls_v2 on, servers with mtls_v2 on, since 14:02 UTC
- Report: alerts/p99-0412.json, Slack thread link
- Manual: ~/proj/storage/.agents/skills/verify-storage/SKILL.md
- Ladder: container-service (layers 1-5)
- Current layer: 2

## Controls
| id | control | type | differs by | matches | not broken the same way because |
|---|---|---|---|---|---|
| C1 | DC-B clients and servers, mtls_v2 off | happy | mtls_v2 flag | binary version, hour, load class | flag off; P99 flat for 30 days in F1's query |

## Facts
| id | kind | layer | where | statement | variable | control | source | artifact | supersedes |
|---|---|---|---|---|---|---|---|---|---|
| F1 | signal | 1 | field | server P99 | 410 ms | 22 ms (C1) | telemetry query q1, agent, 14:30-15:30 | artifacts/F1.csv | |
| F2 | signal | 1 | field | client P99 | 520 ms | 40 ms (C1) | telemetry query q2, agent | artifacts/F2.csv | |
| F3 | context | 1 | field | prod topology | 5 shards x 80 replicas | same | config/prod.toml@a1b2c3 | artifacts/F3.toml | |
| F4 | noise | 2 | field | TCP handshake time | 31 ms | 30 ms (C1) | tcpdump on c-0412 / c-1177, agent | artifacts/F4.pcap | |
| F5 | noise | 2 | field | cert loads per TLS session | 1 | 1 (C1) | bpftrace on c-0412, agent | artifacts/F5.txt | |
| F6 | signal | 2 | field | A records per shard lookup | ~400 | ~5 (C1) | DNS capture on c-0412 / c-1177, agent | artifacts/F6.pcap | |

## Hypotheses
| id | claim (mechanism) | from | falsifier | origin | by |
|---|---|---|---|---|---|
| H1 | new server code path is slow | F1 | server CPU per request unchanged vs C1 | new | agent |
| H2 | cert reloaded on every RPC | F1 | cert loads per session = 1 | new | agent |
| H3 | client stopped routing by shard | F1 | lookups return shard-local addresses | new | agent |
| ... | (H4-H7: capacity, event loop stalls, throttling, slow upstream) | | | | |

## Judgments
| h | f | mark | because |
|---|---|---|---|
| H2 | F1 | + | per-RPC TLS work raises server latency |
| H2 | F5 | x | F5: one cert load per session on the variable |
| H3 | F6 | + | an unsharded client resolves every replica: 400 = 5 x 80 |
| H3 | F1 | + | random-pod routing forces cross-shard hops |

## Log
| step | type | target | detail | result |
|---|---|---|---|---|
| 2 | descend | layer 2 | all layer-1 signals weak: F1 and F2 strength 7 | probes tcp, cert, dns on both sides |
| 5 | validate | H3 | eliminator pass, other model family (codex) | no elimination |

## Interventions
| step | who | what | category | route |
|---|---|---|---|---|

## Decisions
| question | options | chosen | by |
|---|---|---|---|

## Close
- Root cause: H3
- Fix: PR link
- Verified by: F9 (A records per lookup on c-0412 after fix: 5)
```

Column rules:

- **Facts.** `kind` is one of `signal`, `noise`, `symptom`, `context`. `where` is `field` or `lab`. `variable` and `control` hold the readings with units; `control` names the control id. `source` names the probe or report, who ran it, the host, and the window. `artifact` is a saved file. `supersedes` names the fact a re-gathered fact replaces.
- **Hypotheses.** `from` lists at least one fact (a hypothesis with no starting fact is rejected). `falsifier` is required. `origin` is `new`, `split:H2`, `merge:H4,H5`, `combine:H3,H6`, `repro`, `human`, or `reviewer`. A combination row has no judgments of its own; its marks are derived (`x` if any member has `x`, `+` if any member has `+`).
- **Judgments.** Append-only. A later row for the same `h, f` supersedes the earlier one. Every `x` cites the fact it rests on. `+` states the mechanism in one line.
- **Log.** Types: `descend`, `tactic`, `reverify`, `validate`, `discriminate`, `note`. Every descent states why (weak signals or tactics exhausted).
- **Interventions.** `category` is one of `control`, `fact`, `check`, `pushback`, `access`, `proxy`, `decision` (section 6). `route` is filled at close.

### 4.2 Who may write which part

| Part | Agent | Eliminator | Human | `case.py` |
|---|---|---|---|---|
| Facts | Append a row only for a probe run whose artifact is saved, or a report it quotes. Never edit or delete. | Flags gathering defects as `reverify` log rows | Appends observations; may retire a fact with a reason | Locks each fact row by hash; fails on any change or removal |
| Controls | Proposes and records | Challenges "not broken the same way" | Supplies or approves | Lints required columns |
| Hypotheses | Adds, with `from` and `falsifier` | Cannot add; reports uncovered facts | Adds as `by: human`, judged like any other | Rejects rows without `from` or `falsifier` |
| Judgments | Writes, with `because` | Appends overturning rows citing a fact (`by` in the `because` text) | Same as eliminator | Derives combination marks and elimination |
| Log | Writes | Writes `validate` rows | Writes | Reads to know which tactics and validations ran |
| Interventions | Logs every human input that changed course, quoted | None | None | Refuses close while any lacks a route |
| Decisions | Writes options and a recommended default | None | Chooses | Requires a row before `close` |
| Close and routes | Writes | None | Approves policy lines | Checks routes and the parity fact |
| `matrix.md`, `.case.lock` | Read only | Read | Read | Only writer |

Elimination is derived, never declared: a hypothesis with any `x` is eliminated. That keeps the agent from "eliminating" by assertion and keeps the eliminator honest, since its overturn needs a cited fact.

### 4.3 `case.py check` (Phase 2)

`uv run <debug-mode>/scripts/case.py check <case-dir>`. Stdlib only, PEP 723 block, answers per `docs/references/script-output.md`.

- **Lint:** required columns, known kinds and marks, ids resolve, every `x` cites a fact id, hypotheses have `from` and `falsifier`, facts unchanged since the lock. Each error names the fix, such as `F3 changed; facts are append-only: restore the row and add a reverify log row`.
- **Matrix:** writes `matrix.md`: rows are live hypotheses plus the last eliminated ones; columns are signal and symptom facts plus any fact holding an `x`; a strength row under the columns.
- **Next:** the first rule that holds.

| Condition | `next` |
|---|---|
| No control | `control` |
| No signal or symptom fact | `gather` (current layer) |
| No live hypothesis | `hypothesize` (from the unexplained facts) |
| A live hypothesis has an unjudged signal or symptom cell | `judge` (cells listed) |
| Exactly one candidate, validation incomplete | `validate` (missing: falsifier fact, unjudged noise or context cells, eliminator pass, repro parity) |
| Exactly one candidate, validated | `decide` |
| Two or more candidates | `discriminate` (their falsifiers; descend if none is readable at this layer) |
| A combination explains every signal and symptom, each member necessary | `combine` (members) |
| No `tactic` log row since the last descent and some signal has strength 2 or less | `tactics` (concrete suggestions: facts that alone eliminate an otherwise complete row, eliminated rows that explain half the signals, three or more rows each explaining one instance) |
| Otherwise | `descend` |
| Decision recorded | `close`; then `closed` when routes and parity fact exist |

Every answer carries `focus`: the strongest signal with strength 1 or more and the hypotheses that explain it. Example:

```json
{"ok":true,"file":"/home/pascal/.local/state/debug-cases/storage/2026-10-13-p99-mtls/matrix.md","next":"validate","focus":{"fact":"F6","strength":1,"hypotheses":["H3"]},"missing":["eliminator pass"]}
```

Why the thresholds: strength 1 or 2 is "strong" because the post's ideal is 1 and a discriminating observation between two is one probe away; 3 or more sends the agent down a layer rather than into more hypotheses. More than 7 live hypotheses (the post's latency matrix size) turns any `judge` or `discriminate` answer into `tactics` with merge suggestions, so a fat derivative tier is handled by the state machine, not by a warning the output rule would have to treat as a failure.

### 4.4 Manual extensions (`verify-<app>`)

`SKILL.md` gains three sections after Doctor:

```markdown
## Probes
| layer | reads | command | access | cost and cautions |
|---|---|---|---|---|
| 1 | the CLI's answer and readiness | `transcript doctor --source youtube` | local | no paid call |
| 2 | evidence bundles | `ls -t ~/.local/state/eval-transcript/runs` | local | none |
| 3 | network to Deepgram | `ssh mbp 'curl -w @fmt -o /dev/null https://api.deepgram.com'` | read-only, fleet | one request |
| 4 | live process stacks | `py-spy dump --pid <pid>` | local | pauses briefly; capture before any restart |

## Controls
- Last good version: the newest tag whose verifier run passed, from `git tag --sort=-creatordate`
- Sad path: runs with an invalid key fail loudly with `auth` errors; use them against silent failures

## Policy
- Revert a default-on change that caused a regression without asking; open the forward fix as a separate PR
- Ask before any change to Pascal's archive folders or any paid run beyond the canonical test video
```

Each feature file gains a fifth H2, defined once in `create-verification-skill/references/feature-map-example/README.md`:

```markdown
## Gauges
| gauge | layer | read with | control value | parity rule | guards against |
|---|---|---|---|---|---|
| `batch.peak_media_procs` | 1 | `manifest.json` checks | selected worker count | <= control | worker cap bypass |
| `batch.orphan_media_pids` | 1 | `manifest.json` checks | 0 | = 0 (invariant) | children surviving SIGINT |
```

The verifier writes `gauges.json` (`{"<gauge>": value}`) into each evidence bundle. The gate compares it with the last passing run's file under the rule, after normalization (`references/parity.md`).

### 4.5 `index.jsonl`

One line per closed case, for the metric and for repeat detection:

```json
{"id":"2026-10-13-p99-mtls","repo":"storage","closed":"2026-10-14","class":"latency regression","layers":2,"facts":9,"hypotheses":7,"interventions":{"control":1,"access":1},"cause_layer":2,"promoted":["dns.records_per_lookup"]}
```

---

## 5. Goals walked end to end

### 5.1 Goal 1, build time: `debug-mode ; instrument`

Scenario: Pascal asks for parallel conversion in `video-archive` (the existing `parallel-batch` feature is a real example).

1. **Locate the manual.** Read `verify-video-archive/SKILL.md` and `features/README.md`. No manual: run `create-verification-skill` first for a user-facing surface. Done when the feature file for the target exists or is created from the contract.
2. **Write the failure model** (in the PR plan, not the code). For each design assumption, write how its violation would look: "workers never exceed the selected cap", "Ctrl+C leaves no media process", "a second invocation never publishes twice", "throughput scales with workers". Ask `blast-radius`'s question: the one fact this change is safe because of. Done when every assumption has a row.
3. **Pick invariant or gauge for each row.** Never legitimate: make it an invariant (fail loud, control value 0). Legitimate but value matters: make it a gauge with a control value (from config or from the last good run). Score each gauge with the strength question: if this reading differed from its control, how many causes could explain it? Keep gauges answering 1 or 2; drop aggregate-only gauges (throughput alone fits many causes). Done when each row has a gauge or invariant with a control value.
4. **Emit at the shallowest default layer.** The feature writes the readings on every run (the run answer, the manifest, or a structured log line), raw, with the identifiers needed to pair runs: version, flags, host, worker count. No debug flag. For waits, add a timeout that records what it waited on, so a hang leaves a fact before anyone restarts the process. Done when the readings appear in a normal run's output.
5. **Record.** Add rows to the feature file's `## Gauges` table. Done when `maintain-verification-skill`'s index hygiene would find every gauge documented.
6. **Gate.** Add the gauges to the verifier's `gauges.json` and its parity comparison against the last passing run. Done when the verifier answers with the parity verdict.
7. **Prove potency.** On a scratch branch, plant the regression each gauge guards against (ignore the worker cap; skip killing children) and run the verifier: the gate must fail on the planted change and pass on the real one. A gate that never failed proves nothing, the same rule `test-audit` applies to regression tests. Done when the failing and passing verifier answers are pasted.
8. **Capture the baseline** from the passing run. **Reply:** gauges with layer and control value, invariants, the potency proof, the baseline path.

Applied to the latency bug's feature before release: step 2 names "the new mTLS path routes like the old one"; step 3 picks `routing.records_per_lookup` with control value "replicas per shard" (from config) and the invariant "requests sent to a non-owning shard = 0"; step 7 plants `DatabaseClient` and the pre-production gate fails at 2 shards x 1 replica, because the reading is compared to config, not to an absolute number.

### 5.2 Goal 2, bug in production: `debug-mode ; diagnose`

Scenario: the latency bug, run by an agent with this system in place.

0. **Open the case.** Copy the template to `${XDG_STATE_HOME}/debug-cases/<repo>/<id>/case.md`. Write the variable precisely (population, versions, window). Read the manual (Probes, Controls, Policy, the touched features' Gauges), `index.jsonl` for this repo, and run `why`'s incident and postmortem investigators only for the touched area. Do not open source files yet. Done when the header is filled and the manual is read or recorded as missing.
1. **Gather layer 1, fat.** Record every fact the report carries, then the cheap layer: raw telemetry (not dashboard screenshots), configs, flags, versions, deploy and VCS diff between last good and bad. Fan out with `swarm` across sources and across instances of the bug (several hosts, several reports). If the report includes repro steps, run them now: the repro becomes hypothesis R1 (origin `repro`), and its readings are `lab` facts. Every fact gets an artifact and a source. Done when every listed source is read or recorded unavailable.
2. **Choose the control and pair.** Prefer a standing control from the manual. Otherwise pick the case that differs by the suspected factor (flag off, last good version, unaffected cohort), or a louder sad path already in the data. Fill `differs by`, `matches`, and `not broken the same way because`. Read the same quantities on the control and classify each fact. Done when at least one `signal` exists or the next step is `descend`.
3. **Hypothesize from signals.** Each hypothesis cites its starting facts and a falsifier. Now read code, scoped: run `how` on "which paths at the deployed version could produce F6" rather than "how does the client work". Include at least one hypothesis outside the component you suspect. Keep 3-7 hypotheses. Done when every signal is explained by at least one hypothesis or flagged unexplained.
4. **Judge and steer.** Fill every live hypothesis x signal and symptom cell with a mark and a reason. Run `case.py check` (or apply its table by hand in Phase 1). Follow `next`, spending gathering effort on the `focus` hypotheses first. In the latency case, layer 1 gives F1 and F2 at strength 7, so `discriminate` and then `descend`.
5. **Validate.** For the candidate: gather its falsifier observation if no fact covers it; judge it against every fact including noise and context; check repro parity if a repro is used (`references/parity.md`); for a combination, remove each member and confirm a fact goes unexplained; send the eliminator `case.md`, `matrix.md`, and the artifacts (never the transcript), on a different model family when available. The eliminator can only append `x` judgments with citations or `reverify` rows. Done when `next` is `decide`.
6. **When stuck.** `tactics` in order (reverify, split, merge, combine, new from facts), each logged; then `descend` one layer using the manual's Probes, then the ladder's generic probes. Process-layer captures run through poteto's `runtime-forensics` (live) or `trace-forensics` (artifact) or `diagnose-crash` (core dump), each returning facts to the case. Back to step 2: pair the new readings with the same control. Stop at the first strong signal.
7. **Decide.** List fix options with tradeoffs. If Policy covers the choice, apply it and cite the line. Otherwise ask one question in `grill-for-unknowns`'s shape (question, why it matters, evidence, recommended answer, default if Pascal does not care). Rollback, escalation, and dropping support stay human unless Policy says otherwise. If the cause sits in a component Pascal does not own, draft the owner's bug report with every claim citing a fact id and artifact. Done when a Decisions row exists.
8. **Fix and verify.** Hand to poteto `bug-fix` steps 3-6 or a plain implementation. The failing check written first must show the case's strongest signal (the gauge reading), not merely fail. After the fix, read the same gauge on the variable's surface: it must match the control. Record that reading as the parity fact. Tests passing are necessary, not sufficient. Done when the Close section names the parity fact.
9. **Close.** Route every intervention (section 6), promote each strong signal found below layer 1 through `instrument`, add standing controls and probes to the manual, write Policy for decisions taken, write an eval scenario for any step the human had to request, append the index line. Done when `case.py check` answers `closed`.

The same route audits a claim: the coworker's clock-skew repro in the hang becomes R1, fails parity on two facts (packet sequence diverges; no outstanding reply right), and leaves the case as noise.

---

## 6. Accretion

Each case should make the next one cheaper in four ways: fewer layers to descend, a control already chosen, a decision already made, and a method gap already closed.

### 6.1 Routing table (`references/routing.md`)

| What happened in the case | Post's example | Lands in | Mechanism | Read next time by |
|---|---|---|---|---|
| Human supplied a control | flag-off clients as baseline | manual `## Controls` | standing control line | diagnose step 2 |
| Human supplied a fact the agent did not gather | amortization is opt-in, default off | manual `## Probes` (the config read), or a `context` gauge | probe or default emission | diagnose step 1 |
| Human demanded a check | "run the repro", "cite it" | debug-mode | eval scenario from the case, then a skill edit through `writing-for-agents` | every future diagnose run |
| Human pushed back from design knowledge | "the state machine is single-use" | product code | invariant through `instrument` | tests, gate, diagnose step 1 |
| Human ran a command for the agent (proxy) or the agent lacked access | ssh and tcpdump on a prod host | manual `## Probes` with `access` | probe recipe; access granted by Pascal | diagnose descend |
| Human made a decision | which of two leak fixes | manual `## Policy` | policy line | diagnose step 7 |
| Strong signal found below layer 1 (not an intervention) | DNS answers at layer 2 | feature `## Gauges` at layer 1 + gate | `instrument` | gate at build time, diagnose step 1 |
| Evidence destroyed before capture | users restarted the hung daemon | product code | timeout that records its wait; capture on timeout | diagnose step 1 |

### 6.2 Rules

- `case.py check` answers `ok:false` at close while an intervention row has no route. A route can be `declined: <reason>`, so the gate forces a decision, not busywork.
- Repeat detection: at close, read `index.jsonl`. A category seen in two cases of the same repo becomes structure (a probe, a gate, a policy line, an eval), per poteto's Encode Lessons in Structure principle. Prose reminders are not a valid route for a repeat.
- The metric is interventions per case, by category, from `index.jsonl`. It falls when the factory improves and rises when a project changes faster than its manual.
- Method gaps never go into the manual; they go into debug-mode through an eval first (BP_20: evaluations from real failures), so the skill only grows where a real run failed.
- Raw cases stay out of git (private data, large artifacts). What persists is what was promoted: manual sections, gauges, gates, invariants, evals, policy.

### 6.3 Who reads what next time

| Next reader | Reads | Saves |
|---|---|---|
| diagnose step 0-1 | Probes, Gauges, `gauges.json`, index | layers and on-demand probes |
| diagnose step 2 | Controls | choosing and justifying a control |
| diagnose step 7 | Policy | a human decision |
| verifier at build time | gates | the bug reaching production at all |
| debug-mode itself | evals | the same method failure in any project |

---

## 7. Changes to existing skills

All paths under `/home/pascal/projects/skills/authoring/`.

### 7.1 Edits

| # | File | Edit | Reason |
|---|---|---|---|
| 1 | `poteto/poteto-mode/playbooks/bug-fix.md` | Replace steps 1-2 with "Run `debug-mode ; diagnose` steps 0-7: facts and a control before code, the repro kept only with signal parity, `how` only after signals." Step 4 becomes "the case's strongest gauge on the same surface matches the control; the repro passing is necessary, not sufficient." Reply adds the signal and the parity fact. Keep steps 3, 5, 6. | Conflicts C1 and C2 |
| 2 | `poteto/poteto-mode/SKILL.md` | Non-negotiable "For bug fixes, reproduce first on the same surface yourself" becomes "For bug fixes, run `debug-mode ; diagnose`; reproduce on the same surface, and keep the repro only with signal parity." Playbook list: Bug fix, Runtime forensics, and Trace forensics say their diagnosis runs through debug-mode. | C2; single entry point |
| 3 | `poteto/poteto-mode/principles/fix-root-causes.md` | Pattern: "Reproduce first" becomes "Gather facts and a control first; reproduce and check parity"; "Ask why until you hit the root cause" becomes "The root cause is the hypothesis, or minimal necessary combination, that no fact contradicts and that explains every signal"; "When stuck, instrument" becomes "When stuck, descend one layer". Keep the restart-bug and pattern-grep advice. | C4 |
| 4 | `poteto/poteto-mode/playbooks/trace-forensics.md` | Move "confirm against a paired capture" from step 5 to step 1 (get the control capture first, or name why none exists); state that inside a case the output is facts plus at most one hypothesis. | C9; control first |
| 5 | `poteto/poteto-mode/playbooks/runtime-forensics.md` | Step 1 also captures the same signal on a control process when one exists; inside a case the output is facts for `case.md`. | Control first; one record |
| 6 | `poteto/poteto-mode/playbooks/perf-issue.md` | First line: "A slowdown with a known-good control (a version, a flag, a cohort) is a regression: run `debug-mode ; diagnose`. This playbook is for making something faster against a baseline." | C7 |
| 7 | `poteto/poteto-mode/playbooks/feature.md` | New step after `architect`: "Run `debug-mode ; instrument`; the Builder's scope includes emitting the gauges, and step 5 verifies them through the gate." | Goal 1 entry |
| 8 | `poteto/poteto-mode/playbooks/investigation.md` | One line: "A question about why something fails at runtime is a diagnosis: route to `debug-mode ; diagnose`." | C8 |
| 9 | `poteto/interrogate/SKILL.md` | New short section: "Not for root-cause claims. Agreement among reviewers cannot show that the facts are complete. Use debug-mode's eliminator." In Step 4, consensus is reported as a shared reading, not proof. | C3 |
| 10 | `poteto/interrogate/references/rubric.md` | Verification lens, bug fixes: "Does the PR cite the signal that identified the cause and show it restored on the same surface? A fix justified by code reading alone is a hypothesis." | Principle 73: catch non-fixes in review |
| 11 | `poteto/principle-prove-it-works/SKILL.md` | One bullet under Code and features: "For a fix or a regression check, the proof is parity: the reading that differed now matches the control, on the same surface." | Principle 64 |
| 12 | `poteto/create-verification-skill/SKILL.md` | Interview adds **Observe by layer** (where each layer is read, with access level). Generated skill adds **Probes**, **Controls**, **Policy** after Doctor. Step 3: feature files have five H2s, with `Gauges`. Step 4: the proof run writes `gauges.json`. | Manual becomes the factory floor |
| 13 | `poteto/create-verification-skill/references/feature-map-example/README.md`, `create-note.md`, `search.md` | Feature entry contract gains `Gauges` (format in 4.4); the two examples gain a table each. | One definition of the format |
| 14 | `poteto/maintain-verification-skill/SKILL.md` | Live pass: compare each feature's gauges with the last passing run; a missing reading is harness drift, a changed reading is a product regression to report. Triage: a feature with no gauges is a gap, routed to `debug-mode ; instrument`. | Gauges stay honest |
| 15 | `verify-loops/verify-video-archive/` (pilot) | `features/parallel-batch.md` and `features/interruption.md` gain Gauges; `scripts/verify_video_archive.py` writes `gauges.json` and compares with the last passing manifest; tests extended. | Its manifest already records peak processes, RSS, CPU, orphan PIDs, so gauges cost little |
| 16 | `poteto/how/SKILL.md` | One line: "In a debugging case, run after facts isolate a signal, and ask which paths could produce that signal." | C1, keeps `how` honest about what code can tell |
| 17 | `poteto/show-me-your-work/SKILL.md` | "Composing this skill": "A skill whose run keeps a typed record, such as debug-mode's case file, keeps that record and applies this skill's audit and independent review steps to it." | C6 |

### 7.2 Conflicts and resolutions

- **C1, code first.** `bug-fix` step 2 seeds hypotheses with `how` over the subsystem; the post says code is an unreliable narrator. Resolve for the post: facts and control first; `how` later, scoped to a named signal. Keep `how` itself unchanged except edit 16.
- **C2, repro as truth.** `bug-fix` step 1 and the Non-negotiable treat the repro as the ground truth and step 4 treats "the repro now passes" as verification. The post agrees on reproducing early (the leak agent's failure was not running the provided repro) but treats the repro as a hypothesis needing parity. Resolve: keep "reproduce early, yourself, on the same surface"; add parity on the strongest signal for acceptance and for fix verification.
- **C3, review as verification.** `interrogate` counts consensus and lets the lead judge "act on" findings; for root causes, consensus cannot reveal a missing fact (the cert-reload theory survived an independent subagent). Resolve: interrogate keeps code and design review; root-cause claims go to the eliminator, which may only eliminate.
- **C4, "ask why until the root cause".** Iterated why invites narrative depth. Resolve: the root cause is defined by the matrix.
- **C5, local verification against "full stack in a box".** `create-verification-skill` launches the app locally. No real conflict for Pascal's tools: they run on his machines, so local is production. Where a project runs elsewhere, Probes must reach where the failure happened, and lab facts never outrank field facts.
- **C6, one audit trail.** `show-me-your-work` asks other skills to route trails through it; the case file is a typed record with different rows. Precedent: `hillclimb` keeps its own `decision.tsv` columns. Resolve with edit 17.
- **C7-C9** are the routing edits 6, 8, and 4.
- **`tdd`** says the test must fail "for the intended reason". Aligned; debug-mode defines the intended reason as the case's strongest signal. No edit (DRY: the rule lives once, in diagnose step 8).

### 7.3 Reused as-is, and why

| Skill | Role in the system |
|---|---|
| `poteto/why` | Fact source: postmortems, regression history, error trackers; its epistemics tiers stay its own |
| `poteto/blast-radius` | Fix-diff review at diagnose step 8; its "one fact it is safe because of" feeds instrument step 2 |
| `poteto/figure-it-out` | Still the fallback when no playbook fits; debugging now has one |
| `poteto/swarm` | Fan-out of fact gathering across sources and instances |
| `poteto/arena` | Fix design when the fix crosses a boundary (via `architect`); not used for diagnosis |
| `poteto/tdd` | Failing-check-first cadence for the fix |
| `poteto/poteto-mode/playbooks/hillclimb.md` | Already one change, one measurement; its repro rule fits |
| `poteto/poteto-mode/principles/sequence-verifiable-units.md`, `test-behavior-not-implementation.md` | Aligned (failing check first; behavior over implementation) |
| `poteto/poteto-mode/references/agent-runtime.md` | About agent tooling; production access rules live in debug-mode and the manual's Probes, their only consumers |
| `andy-devtools/code-review-mode` | `test-audit`'s gate ("what credible regression makes it fail") and its rule that a regression test must have failed already match; thermo and architecture are unrelated |
| `matt/grill-for-unknowns` | Its question shape is reused for decisions; the skill itself is planning-time |
| `verify-loops/verify-skills`, `verify-transcript` | Unchanged until the pilot proves the gauge format; then gauges added when next touched |
| Omarchy `diagnose-crash` | Process and kernel layer probe for core dumps |

### 7.4 Borrowed from the archived Jeffrey skills (ideas only, restated)

Paths under `~/projects/skills-private/skill_archived/jeffreys-skills/`.

- Control design as an axis table: each axis must match, is the stated difference, or is varied on purpose (`profiling-software-performance/references/APPLES-TO-APPLES-MATRIX.md:19-45`). Feeds the `differs by` and `matches` columns.
- Hypotheses must carry a falsifier and expected evidence, and refuted ones name the evidence that killed them (`brennerbot-with-ntm/SKILL.md:662-688`). Feeds the `falsifier` column and cited `x` marks.
- Repro parity on crashes and heaps by hashing the top five function names without line numbers (`testing-fuzzing/references/TRIAGE.md:98-123`), and scrubbing timestamps, ids, ports, and paths before comparing (`testing-golden-artifacts`). Feeds `references/parity.md`.
- A detector must catch a planted mutation (`testing-metamorphic`). Feeds instrument step 7.
- Hang symptom tables across strace and gdb (`gdb-for-debugging/SKILL.md:341-349`), per-question tool tables with overhead (`gdb-for-debugging/references/COMPLEMENTARY-TOOLS.md`), samplers per language (`profiling-software-performance/SKILL.md:116-124`), and a parallel hang capture (`deadlock-finder-and-fixer/scripts/hang-capture.sh`). Feed `references/ladders.md`, rewritten.
- Rejected from the same set: consensus as confidence (`multi-model-triangulation/SKILL.md:12`, the gauntlet's unanimous vote), support-point accumulation and confirmation by debate (`brenner`, `brennerbot-with-ntm`), code-first entry points (`multi-pass-bug-hunting`, `reality-check-for-project`), and repro without parity (`gdb-for-debugging` delay injection as proof, `deadlock-finder-and-fixer`'s "gone after the fix" done-criterion).

---

## 8. Evals

Each scenario lives in `debug-mode/evals/evals.json` and runs through `writing-for-agents`'s eval runner (fresh session per agent, skill copied from a ref). Fixtures are small Python repos plus canned evidence. Layer-2+ evidence is reachable only through a `./probe` script, so descending is an observable choice in `events.jsonl`. Grading reads `answer.md`, `events.jsonl` (order of reads and commands), and the case file.

### 8.1 Latency (control, weak versus strong signal, red herring)

**Fixture:** `storage/` with `DatabaseClient` and `ShardedDatabaseClient`; the new `mtls.py` path builds `DatabaseClient`. A memoized `ssl_context()` called inside `rpc()` looks like a per-call reload when read. Unit tests pass. `evidence/` holds P99 CSVs for both populations, `prod.toml` (5x80), `preprod.toml` (2x1), and a 2025 postmortem about per-RPC cert reloads (the lure). `./probe --list` offers `tcp-handshake`, `cert-loads`, `dns` per population (`variable`, `control`, `candidate`); `candidate` imports the working tree and counts resolver answers, so fix parity is real.

**Query:** "After enabling mtls_v2 on the 5000-host client cluster, client and server P99 latency jumped (evidence/). Find the root cause and fix it. Production probes: ./probe --list."

| Step | Correct behavior | Failure (from the post) |
|---|---|---|
| 0-1 | Opens a case; reads evidence and config before any file under `src/` | Opens `src/` first and builds a story from `rpc()` |
| 2 | Records a control differing only by the flag | No control; compares nothing |
| 3-4 | P99 recorded as a signal of strength 7 (or several); does not stop there | Treats P99 as a locator; picks cert reload because the postmortem matches |
| 6 | Runs probes on both populations; TCP handshake is noise; DNS 400 versus 5 is the strong signal | Runs only variable probes; no pairing |
| 5 | Cert reload eliminated, citing the `cert-loads` fact | Ships a per-session cert cache; a subagent "validates" it |
| 3 | Reads code only to explain 400 answers; finds the unsharded client | |
| 8 | One-line fix; `./probe dns --population candidate` shows about 5 | "Verified" by passing unit tests |
| 9 | Proposes gauge `records_per_lookup` = replicas per shard at layer 1, gated against config, which fails at pre-prod scale | No promotion; or a P99 alert as the "gauge" |

### 8.2 Memory leak (run the repro, constraints, split then combine, decision)

**Fixture:** `authflow/` with tags `v1.4` (good) and `v1.5` (bad) 24 commits apart. `engine.py` has a recursive, single-use `run_state_machine` that retains a frame record per entry; `cache.py` (v1.5) keeps engines process-wide, default on; `amortize.py` (v1.5) is opt-in, default off, entry `deduped_run_state_machine`. `BUG.md` gives versions and repro steps (`python -m authflow.demo --no-creds --max-mb 200`); `heap.txt` points at `run_state_machine` at the fixture's line, not the deduped entry.

**Query:** "Users report the tool gets OOM-killed when no auth credentials are set (BUG.md, heap.txt). Find the root cause and propose a fix."

| Step | Correct behavior | Failure (from the post) |
|---|---|---|
| 1 | Runs the provided repro before theorizing; repro parity: same top frame as `heap.txt` | Theorizes from code; never runs the repro |
| 2 | Controls: `v1.4` with the same repro (no growth) and the same version with credentials (no growth) | No control, so "recent version" is never a constraint |
| 3-4 | Facts: regression since v1.5, amortization off, frame in plain recursion, only without credentials. "Retries unbounded" gets `x` on "since v1.5"; "amortization" gets `x` on "amortization off" | Proposes bounding retries; then blames amortization |
| 6 | No row survives, so tactics: split "the amortization work" into "process-wide cache, default on" and "amortizing engine, default off" | Proposes bisecting 24 commits; asks the human whether to bisect |
| 6 | Combines "cache keeps the engine alive" with "state machine assumes single use"; removes each to show necessity | Invents four new hypotheses |
| 7 | Presents two fixes (engines out of the cache; state machine safe to re-enter) with tradeoffs and a recommended default; does not pick silently | Applies one fix without saying there was a choice |
| 8 | After the chosen fix, the repro shows flat memory and the frame is gone | "Fixed" by a retry cap that only delays the OOM |
| 9 | Proposes an invariant (an exhausted engine refuses re-entry) and a gauge (entries per engine, control 1) | No invariant; the next cache change repeats the bug |

### 8.3 The hang (sad-path control, layer discipline, repro parity, claims versus facts, citations)

**Fixture:** no auth daemon source; our client library source exists with a retry loop that looks like it could spin (the lure). `reports/user-{a..d}/` each hold `system.log` (timeouts only), `pcap.txt` (handshake, upgrade, then only pings), `spindump.txt` (our thread waiting in a synchronous XPC send), and a long `lsmp.txt` with one line showing the auth daemon holding a send-once reply right for our port, aged 67 hours. `reports-denied/` holds two permission-failure bundles with loud auth errors, an auth exchange in the pcap, and no outstanding right. `coworker-repro/` holds a clock-skew bundle whose pcap shows token rejection and retries, and no outstanding right. `email-auth-team.md` says no logs means no request reached them.

**Query:** "Users report 60s VFS timeouts in vfsd (reports/). Server telemetry is clean during the timeouts. A coworker says they reproduced it with clock skew (coworker-repro/). The auth team says it is not them (email). Find the cause and draft the bug report for the owning team."

| Step | Correct behavior | Failure |
|---|---|---|
| 0 | Records the coworker repro as R1 and the auth team's statement as a hypothesis; only "no authd logs" is a fact | Accepts "no logs, so no request" as a fact |
| 2 | Uses `reports-denied/` as a sad-path control, stating why it is not broken the same way | No control; or builds a local daemon setup |
| 6 | Descends in order, logging each: logs (no signal versus control), packets (silent after upgrade versus an auth exchange), process (waiting, not spinning), IPC table (outstanding reply right in all four variable reports, absent from the control); stops there | Jumps straight to `lsmp.txt` without a control; or stops at packets with a story |
| 5 | R1 fails parity on two facts (pcap sequence, IPC table) and leaves the case | Accepts clock skew because the symptom matches |
| 3 | Our retry loop gets `x` from "process waiting, not spinning" | Blames the retry loop after reading our code |
| 7 | Bug report for the auth team where every claim cites a report id, file, and line; escalation presented as a decision, not sent | Uncited claims; sends or files without asking |
| 9 | Proposes a client-side invariant: time-bound the XPC wait and log the peer and request on timeout, plus a capture on timeout, because restarts erased evidence | No promotion |

### 8.4 Build-time twin (instrument)

**Fixture:** the latency repo at the commit before release, with the feature diff and `verify-storage/` manual. **Query:** "debug-mode ; instrument for the mtls_v2 routing change before it merges." **Correct:** failure model names routing parity; gauge `records_per_lookup` with control from config, emitted by default; feature file Gauges row; gate; potency proof by planting `DatabaseClient`, failing at 2x1. **Failure:** only unit tests; P99 as the gauge; a gauge behind a debug flag; a gate never shown to fail.

### 8.5 Baseline and scoring

- Run each scenario on Claude Code and Codex at three refs: no debug-mode (baseline), Phase 1 prose, Phase 2 with `case.py`.
- Score is the share of expected behaviors met, per step, plus one counter: how many steps needed the follow-up a human gave in the post. In a single-shot eval, a missing step counts as one intervention.
- Each eval's fixture is checked before use: unit tests pass with the bug present (proves tests do not catch it), probes print the documented numbers, the lure is present.

---

## 9. Phased plan

Each unit ends in a check. Nothing in a later phase starts before the earlier phase's check passes.

### Phase 0: evals and baseline (measure twice)

- **U0.1** Latency fixture. Done when its unit tests pass with the bug and `./probe dns --population variable` prints about 400 answers.
- **U0.2** Leak fixture. Done when the repro shows growth at `v1.5`, none at `v1.4`, and the top frame matches `heap.txt`.
- **U0.3** Hang fixture. Done when the four variable reports share the outstanding right and neither control nor repro has it.
- **U0.4** Baseline runs without debug-mode, on two agents. Done when every scenario has a recorded score. If the baseline already meets 80 percent of behaviors, cut Phase 1 to the glossary, the eliminator, and the bug-fix edit.

### Phase 1: diagnose, prose only (most value)

- **U1.1** `SKILL.md`, `glossary.md`, `case-file.md`, `diagnose.md`, `eliminator.md`, `parity.md`, and `ladders.md` with the CLI ladder (Pascal's main stack) plus the four ladders the post names, generic probes rewritten from 7.4. Done when `validate_skill.py` answers `{"ok":true}` and the three evals beat baseline.
- **U1.2** Close step and `routing.md`, `index.jsonl` line. Done when each eval's case ends with every intervention routed or declined.

### Phase 2: `case.py` (only if Phase 1 evals show matrix errors)

Trigger: miscounted strength, an `x` ignored, a descent without tactics, or a lost best finding in at least one Phase 1 run.

- **U2.1** `case.py check` with tests built from the post's three matrices as literal fixtures: latency (P99 strength 7, DNS strength 1, `next` = `validate` H3), leak before tactics (no candidate, `next` = `tactics` with the split suggestion), leak after split and combine (`next` = `combine`, necessity holds), and fact immutability (an edited fact row fails). Done when tests pass and evals beat Phase 1.

### Phase 3: routing edits

- **U3.1** Edits 1-6, 8-11, 16, 17 (edit 7 waits for the instrument playbook in U4.2; edits 12-15 belong to Phase 4). Done when `just compile-skills` and `just check` pass, poteto's existing evals still pass, and a `poteto: fix <latency fixture>` run reaches diagnose.

### Phase 4: build time, piloted

- **U4.1** Gauges contract and manual sections in `create-verification-skill` (edits 12, 13). Done when a generated skill on a scratch repo has the sections filled from the interview, no placeholders.
- **U4.2** `instrument.md` and edit 7 (poteto `feature` calls instrument). Done when eval 8.4 passes.
- **U4.3** Pilot on `verify-video-archive` (edit 15). Done when the verifier writes `gauges.json`, parity against the last passing run is in its answer, and a planted regression (ignore the worker cap) fails the gate while the real code passes. This is the E2E proof of Goal 1.
- **U4.4** `maintain-verification-skill` edit 14. Done when a maintain pass on the pilot reports gauge parity per feature.

### Phase 5: first real case

- **U5.1** The next real bug in any of Pascal's projects runs through diagnose and close. Done when the case is closed with routes, and a second case in the same repo shows fewer interventions or a reason why not.

### Deferred (YAGNI until a case asks)

- A run-record convention for every CLI (one JSONL line per invocation in the state dir): the post's default collection, adopted per tool when a case needed a fact that a run record would have held.
- Production access tooling beyond the Probes `access` column.
- Canary analysis and deploy gating beyond the verifier gate.
- A cross-machine or cross-repo case index.
- An event-log (JSONL) case format with a write CLI; only if Markdown editing proves error-prone.
- Ladders beyond the five in Phase 1.
- brigade-mode's cook SOP calling instrument.

### Rejected

- A separate adversarial-review skill for debugging (a prompt is enough).
- Consensus, or "N reviewers agree", as verification anywhere in the system.
- Probability or confidence scores on hypotheses; counting and contradictions carry the decision without fake precision.
- One skill per debugging tool.
- Local "full stack" repro harnesses as a source of facts that outrank field facts.
- Committing raw case files to repositories.

---

## 10. Open questions only Pascal can answer

1. **Production access.** For his projects, production is the fleet (om1, mbp, mini). May a diagnose run execute read-only probes over SSH on those machines without asking, as long as each run is recorded as a fact? This sets the default `access` level and the first Policy line.
2. **Case records in repositories.** Raw cases stay local. Should a sanitized one-page record of each closed case be committed per project (for example `docs/cases/`), so `why` and future agents on other machines can read past cases, or is the promoted material enough?
3. **Policy home.** I put Policy in each project's `verify-<app>` manual so it loads only when debugging. Should debugging policy instead sit in the project's `AGENTS.md`, read by every agent on every task?
4. **Name.** `debug-mode` follows `code-review-mode`'s domain naming. Pascal's other imported modes carry their author's name; this one is a distillation in his own words, which is why I did not name it after the author. Keep `debug-mode`?
5. **Eval budget.** Phase 0-2 runs three to four scenarios on two agents at three refs, about 24 agent sessions, some long. Is that budget acceptable, or should Phase 0 run one agent only?
