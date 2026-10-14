# Prior art for "How to effectively debug when you no longer understand the code"

Research date: 2026-10-13. Read-only research; no repository was edited.
Subject post: Cindy Sridharan, Oct 10 2026 (full text at /tmp/debug-post/post.txt, read in full).

Evidence tags used below:
- [P] I read the primary text (or a verbatim extraction of it) in this session.
- [S] Secondary summary, search snippet, or a fetched page that summarised the source. Treat numbers as "as reported".
- [L] Local file under ~/projects/skills-private/skill_archived/jeffreys-skills/ that I read.
- [inf] My own inference, not stated by the source.

Mapping labels: SAME (the post already says this), STRONGER (prior art says it more rigorously or with evidence), EXTENDS (adds a step or case the post lacks), SHARPENS (corrects a detail), CONTRADICTS.

---

## 0. Cross-cutting verdicts (read this first)

1. **The post's matrix is ACH, minus five features that matter.** Heuer's Analysis of Competing Hypotheses (ACH) adds: graded diagnosticity (probability of seeing E if H), tri-state cells (consistent / inconsistent / not applicable) rather than a binary tick, "unproven is not disproved", an explicit "would I expect to see evidence of this if H were true?" check on every absence, and a sensitivity analysis on the winner (not only when nothing fits). It also asks for milestones (tripwires) after the conclusion. Orientation is transposed (Heuer: hypotheses across the top, evidence down the side) but a 2024 experiment found hypotheses-as-rows (the post's layout) reduced confirmation bias while the ACH-style layout did not. So keep the post's layout. [P][S]
2. **The post's "strong signal" test is retrospective; prior art makes it prospective.** The post counts how many hypotheses a fact fits after the fact is in hand. Platt's "The Question" ("what hypothesis does your experiment disprove?"), Zeller's "derive a prediction that separates it from likely alternatives", Google SRE's "design tests with mutually exclusive alternatives", Brenner Bot's lint rule that every prediction row must differ across hypotheses, and Pocock's "each hypothesis states its prediction" all force the discrimination to be written down before the probe runs. That is the single most transferable upgrade. [P][L]
3. **Control/variable is a solved, automated technique in several fields.** Honeycomb BubbleUp (rank every attribute by difference between an anomalous cohort and a baseline), differential flame graphs, statistical bug isolation (Liblit), Tarantula-style suspiciousness, Twitter Diffy (primary/secondary/candidate), Netflix/Google canary analysis. Those fields also supply what the post leaves implicit: how to validate the control itself (A/A noise floor, fresh baseline, concurrent comparison, MATCH/STATE/RANDOMIZE axes) and the fact that diffs must be **bidirectional** (a signal can be something present in the control and absent in the variable; the post's own "hang" was exactly that, a missing reply). [P][S][L]
4. **"Fat factual tier" needs a qualifier.** Heuer (ch. 5), ITBench-AA, EviRCA and Datadog's Bits AI SRE all report that more raw data does not help the reasoner: confidence rises faster than accuracy; over-investigation adds false positives; compact deterministic "evidence cards" beat raw telemetry by 15-26x in tokens and ~3x in accuracy. So: fat store, thin working set, facts produced by deterministic tooling (not by the agent). [P][S]
5. **Multi-cause handling is right but incomplete.** Bronson et al. say the *sustaining* effect (not the trigger) is the true root cause of a metastable failure, and triggers are interchangeable. Cook/Allspaw say "each necessary, but only jointly sufficient". Liblit adds a third case the post does not name: several *independent* bugs, each explaining a different subset of the failing instances. The post's "remove each cause and a fact is left unexplained" test also fails under overdetermination (two redundant sufficient causes). [P][S][inf]
6. **Adversarial review: the post is right and the evidence is now quantitative.** Correlated errors across LLMs (60% agreement when both are wrong; nine judges act like about two independent votes), framing effects (a 97% successful bias-injection attack on Claude Code / CodeRabbit review), confirmation-biased test selection (11 LLMs), and "LLMs get lost in multi-turn conversation" (-39%) all back the post. They also give concrete mitigations (counterexample prompting 42% -> 56% discovery rate; give reviewers facts, not narratives; independence = a route that could fail separately). In human medicine, cognitive-forcing training showed no effect in a controlled trial, which argues for structural enforcement (required fields, linters, citation rules) over exhortation. [P][S]
7. **Existing agent skills are strong on enforcement and weak on evidence structure.** obra/superpowers and Pocock's `diagnosing-bugs` have pressure-tested discipline (iron laws, red-capable loops, 3-failed-fixes circuit breaker). None has a factual tier, signal strength, control validity, or multi-cause handling. obra's skill actively contradicts the post in three places (single hypothesis; "95% of no-root-cause cases are incomplete investigation"; repro first). Brenner Bot (local) is the closest in spirit and the only one that lints hypothesis quality. [P][L]
8. **Reproduction-first (Agans, Pocock, Addy, obra) vs forensic-first (the post).** Both are right in their domain. Resolution that fits all sources: a repro is a *probe generator*; Pocock's "red-capable, deterministic, fast, agent-runnable" criteria decide whether it is a usable probe, and the post's signal-parity check decides whether it is a probe of *this* bug. When no repro is possible (the post's hang), proceed from the factual tier, which Pocock's skill forbids ("Do not proceed to hypothesise without a loop"). [P]

---

## 1. Analysis of Competing Hypotheses (Heuer, CIA)

Primary source read: Heuer, *Psychology of Intelligence Analysis*, ch. 4, 5, 8 (full PDF text extracted).
https://www.cia.gov/resources/csi/static/Pyschology-of-Intelligence-Analysis.pdf (book page: https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/)

### 1.1 The eight steps [P]
1. Identify possible hypotheses (group brainstorm, different perspectives). 2. List significant evidence and arguments for and against each, **including your own assumptions** and **absences**. 3. Matrix of hypotheses x evidence; analyse **diagnosticity**. 4. Refine the matrix; delete evidence with no diagnostic value; reword or merge hypotheses. 5. Draw tentative conclusions, "trying to disprove the hypotheses rather than prove them". 6. **Sensitivity analysis**: "how sensitive your conclusion is to a few critical items of evidence". 7. Report relative likelihood of **all** hypotheses, not just the winner. 8. Identify **milestones** for future observation.

Mapping to the post: SAME at steps 1, 3, 5 (this is the matrix and the "row with no contradiction"). The post lacks steps 2 (assumptions/absences as evidence), 4 (delete non-diagnostic evidence, merge when evidence cannot distinguish), 6, 7, 8 as explicit steps.

### 1.2 Diagnosticity [P]
- Definition: "the extent to which any item of evidence helps the analyst determine the relative likelihood of alternative hypotheses." Heuer's analogy: a high temperature tells a doctor the patient is sick but "relatively little value in determining which illness". This is exactly the post's server-P99 signal (fits 7 of 7 hypotheses).
- Graded version: for each cell ask "If this hypothesis is true, what is the probability that I would be seeing this item of evidence?" Optional extra scales: intrinsic importance of the evidence; **ease with which it could be concealed, manipulated or faked**.
- Mapping: STRONGER. The post counts hypotheses consistent with a signal (binary). Heuer's graded likelihood supports ranking *signals* by how unequal their probabilities are across hypotheses, and tells you when a "✓" is weak (consistent but unlikely).
- Skill use: matrix cells hold {C, I, N/A, ?} plus an optional likelihood bucket (expected / possible / unlikely). Diagnosticity score of a fact = spread of its cell values across live hypotheses. A fact scoring zero spread is recorded but never used to steer.

### 1.3 Count inconsistencies, not support [P]
- "The pluses ... are far less significant ... a long list of evidence that is consistent with almost any reasonable hypothesis can be easily made. What is difficult to find, and is most significant when found, is hard evidence that is clearly inconsistent." The hypothesis with fewest minuses is probably the most likely.
- Mapping: SAME in direction (the post's "any contradicting fact discards the hypothesis"), STRONGER in the ranking rule when no row is fully clean: rank by number and weight of inconsistencies instead of declaring "none fit" (the post routes straight to the five tactics). Heuer also warns "the matrix should not dictate the conclusion"; if the ranking feels wrong, a factor is missing from the matrix: add it.
- Skill use: when no row is all-C, print the ranking by weighted I-count and name the single fact driving each elimination. This tells the agent which facts to re-verify (tactic 1) first.

### 1.4 Unproven is not disproved [P]
- "For an unproven hypothesis, there is no evidence that it is correct. For a disproved hypothesis, there is positive evidence that it is wrong ... Unproven hypotheses should be kept alive until they can be disproved." Heuer's example: the 1998 Indian nuclear tests, where "no indication" was read as "not planning".
- Mapping: EXTENDS. The post's matrix discards on contradiction (correct) but is silent on hypotheses that merely lack support. Agents prune the unglamorous ones early.
- Skill use: each hypothesis carries status LIVE / KILLED(fact id) / PARKED(retry condition). Only a cited contradicting fact moves LIVE to KILLED. (See also the negative-ledger idea in section 7.)

### 1.5 Expected-evidence check for absences ("the dog did not bark") [P]
- Step 2: "If this hypothesis is true, what should I expect to be seeing or not seeing ... Note the absence of evidence as well as its presence." Closing lesson: whenever tempted to write "there is no evidence that ...", ask "If this hypothesis is true, can I realistically expect to see evidence of it?"
- Mapping: EXTENDS, and the post's own hang story is a live specimen. The authentication team said "no logs, therefore no request reached us" and declined ownership. That is an unexamined absence. The post's definition of signal is "seen in variable, not in control"; it never defines the reverse (present in control, absent in variable), yet the decisive fact in the hang was a *missing* completion (an unanswered reply right).
- Skill use: any negative ("no logs", "no errors", "no such call") must be stored with a coverage note: which channel, which host, which window, and whether the thing would have produced that artifact if present. Diffs are computed in both directions.

### 1.6 Sensitivity analysis and linchpins [P]
- Step 6 and ch. 4: find "the few linchpin assumptions or items of evidence that really drive the outcome" and recheck them, including where the evidence came from; "One advantage of the ACH procedure is that it tells you what needs to be rechecked."
- Mapping: EXTENDS. The post's tactic 1 (reverify how facts were gathered) fires only when nothing fits. Heuer applies the recheck to the *winner*, which is where a wrong conclusion actually hides. In the latency bug the winner rested on a single DNS observation from one host.
- Skill use: after a row survives, list the 1-3 facts whose reversal would flip the ranking; require a second independent measurement (another host, another time window, another tool) for each before declaring done.

### 1.7 Report all hypotheses; milestones [P]
- Steps 7-8: give relative likelihood of the alternatives, and say "in advance what would cause you to change your mind", which "will also make it more difficult for you to rationalize such developments".
- Mapping: EXTENDS. The post's end state is one validated hypothesis plus (for ambiguous fixes) a list of options for a human.
- Skill use: the final report lists killed hypotheses with the killing fact, the surviving one, and 2-4 post-fix tripwires (signals that must return to control values; observations that would mean the diagnosis was wrong). This is the debugging twin of the post's deploy-gate parity checks.

### 1.8 More information raises confidence, not accuracy [P]
- Ch. 5 summary of the handicapper experiment: accuracy stayed flat as data grew from 5 to 40 variables while confidence rose steadily; "With only five items of information, the handicappers' confidence was well calibrated". Similar results in other fields.
- Mapping: SHARPENS the "fat on facts" principle. A large factual tier is only safe if each fact is weighed by diagnosticity. Otherwise the agent will become more sure as consistent-but-nondiagnostic facts pile up.
- Skill use: confidence statements are computed from the matrix (surviving hypotheses, margin, linchpin re-checks), never from the volume of supporting facts.

### 1.9 Evidence about whether ACH works (be honest about this) [S]
- Cheikes et al., MITRE 2004: beliefs held when evidence arrived changed how much weight it got; ACH reduced the bias only for participants without professional analysis experience. https://www.mitre.org/sites/default/files/pdf/04_0985.pdf
- Dhami, Belton, Mandel 2019 (Applied Cognitive Psychology, n=50 analysts): trained analysts skipped steps; mixed evidence on bias; ACH may increase judgement inconsistency. https://strathprints.strath.ac.uk/69049/
- Cognitive Research: Principles and Implications 2024 (n=161 + 62 Dutch military analysts): hypotheses-in-rows layout cut the confirmation-biased choice to 39% vs 62% (hypotheses in columns, i.e. ACH layout) and 67% (text). https://pmc.ncbi.nlm.nih.gov/articles/PMC11169332/
- Takeaway for skills: the benefit comes from *structure that forces disconfirmation*, not from the ritual. Keep the post's rows-are-hypotheses layout; enforce steps mechanically (required fields) because trained humans skip them. Single-task, two-hypothesis experiment, so replication is needed.

---

## 2. Platt, Popper, Chamberlin, severity, differential diagnosis

### 2.1 Platt, "Strong Inference" (Science 146, 1964) [P]
https://people.csail.mit.edu/ythomas/InterestingArticles/Strong_Inference.pdf
- Steps: (1) devise alternative hypotheses; (2) devise a crucial experiment (or several) "with alternative possible outcomes, each of which will, as nearly as possible, exclude one or more of the hypotheses"; (3) carry it out "so as to get a clean result"; (1') recycle with sub-hypotheses. A logical tree; "Any conclusion that is not an exclusion is insecure and must be rechecked."
- **"The Question"**: on hearing any explanation ask "But sir, what experiment could disprove your hypothesis?"; on hearing an experiment described ask "But sir, what hypothesis does your experiment disprove?"
- Mapping: STRONGER on the *prospective* side. The post asks "how many hypotheses fit this fact" after the fact exists. Platt asks, before running the probe, which hypotheses each possible outcome would exclude. A probe whose outcomes exclude nothing is waste regardless of how cheap it is.
- Skill use: a pre-probe record with columns hypothesis -> predicted outcome. Refuse (or at least flag) a probe where all live hypotheses predict the same outcome. Rank candidate probes by number of hypotheses split / cost. The "recycle with sub-hypotheses" step is the post's tactic 2 (split).

### 2.2 Chamberlin, multiple working hypotheses; Popper [P]
- Platt quotes Chamberlin: a single hypothesis breeds "parental affection ... a pressing of the theory to make it fit the facts and a pressing of the facts to make them fit the theory". Cure: multiple working hypotheses, so the fight is "purely a conflict between ideas". Platt on Popper: "science advances only by disproofs"; hypotheses that cannot be refuted "do not say anything".
- Railsback's modern reprise of Chamberlin records the multiple-causation point: "a phenomenon is the result of several causes, not just one". https://railsback.org/railsback_chamberlin.html [S]. (The 1897 original is a scan I could not text-extract: https://www.eps.mcgill.ca/~courses/c590/Chamberlain%201897.pdf)
- Mapping: SAME (derivative tier = working hypotheses) and a historical anchor for the post's "combine complementary hypotheses" tactic: Chamberlin argued the method naturally yields *combinations* of causes.
- Skill use: language for the skill's core rule: no hypothesis is "the" hypothesis until all competitors are explicitly dead. "Ruling theory" is the failure to name.

### 2.3 Mayo's severity principle (the missing quality gate on "validation") [S]
https://www.cambridge.org/core/books/statistical-inference-as-severe-testing/D9DF409EF568090F3F60407FF2B973B2 ; https://blog.apaonline.org/2019/03/07/interview-with-deborah-mayo/
- A claim is warranted to the degree it has passed a test that *would probably have found a flaw if one existed*. A pass by a test that could not have failed is not evidence.
- Mapping: EXTENDS and explains the post's central adversarial-review failure: the cert-reload theory "survived an independent subagent's validation" because the subagent had no fact that could fail it. It was a zero-severity test.
- Skill use: every validation step logs "what outcome would have falsified this and was it possible to observe it?" A validation with no possible falsifying outcome is recorded as "not tested", not "passed".

### 2.4 Differential diagnosis and the "can't-miss" list [S]
- SAEM clerkship primer: strategies are hypothetico-deductive, **rule-out-worst-case**, pattern recognition (prone to anchoring/confirmation), exhaustive. The differential "should include all of the potentially life-threatening conditions, even if they are uncommon or less likely"; the cost is longer workups, and less common benign diagnoses can be delayed. https://www.saem.org/cdem/education/online-education/m3-curriculum/group-focused-chief-complaint-history-physical-examination-and-differential-diagnosis/developing-a-case-specific-differential-diagnosis
- Croskerry's cognitive forcing strategies (premature closure, anchoring, search satisficing) https://pubmed.ncbi.nlm.nih.gov/12514691/ ; practical lists at https://first10em.com/mitigation-of-errors/ : ask "what else could this be?", "does anything not fit?", **"is there more than one thing going on?"**, SPIT (most Serious, Probable, Interesting, Treatable), cognitive stop points (before initial orders, when not progressing, at handovers).
- Caveat on the debiasing evidence: a controlled trial of cognitive-forcing training in 191 medical students showed no reduction in diagnostic error (search-satisficing second-diagnosis rate 52% vs 48%, p=0.91). https://www.cambridge.org/core/journals/canadian-journal-of-emergency-medicine/article/ineffectiveness-of-cognitive-forcing-strategies-to-reduce-biases-in-diagnostic-reasoning-acontrolled-trial/B768948819704516DBE325909A8D611E . First10EM says these techniques "have no evidence base in medicine". [S]
- "Pertinent negatives": none of the fetched sources defined the term formally. The working meaning (a finding that should be present if H were true and is absent, so it counts against H) is the same logic as Heuer's expected-evidence check (1.5). Treat as [inf].
- Mapping: EXTENDS. The post ranks by evidence fit only. DDx adds a **severity axis**: low-probability but catastrophic or cheap-to-exclude hypotheses stay on the board.
- Skill use: a standing can't-miss slate for debugging, each with a cheap exclusion test: wrong artifact deployed or stale build (Agans "check the plug"), flag/config skew between control and variable, clock or time-window mismatch, resource exhaustion, recent change in an upstream dependency, observability gap (the channel could not have shown it). Run those exclusion tests first because they are cheap, not because they are likely.
- Caveat for skill design: since exhortation-style forcing performs poorly in humans, build these as required artifacts (a populated slate, a "more than one thing going on?" field) rather than prose advice. In LLMs, counterexample prompting does help (section 8.5), so both layers are justified.

---

## 3. Zeller, delta debugging, git bisect, Agans, Gregg

### 3.1 Zeller: scientific debugging, hypothesis log, "Why Programs Fail" [P/S]
https://www.debuggingbook.org/html/Intro_Debugging.html ; book: https://shop.elsevier.com/books/why-programs-fail/zeller/978-0-12-374515-6
- Method: question -> hypothesis -> **derive a prediction that separates it from likely alternatives** -> experiment -> refine or reject; repeat "until hypotheses, predictions, and observations no longer conflict". Each new hypothesis must be consistent with all earlier observations (his analogy is the Mastermind game). [P]
- **Hypothesis log**: record every experiment in a table (Input, Expectation, Output, Outcome), number the hypotheses; lets you pause, resume or hand off. [P]
- "Start to fix if and only if you have a diagnosis" with two properties: **causality** (how and why the failure occurs, so the fix makes it disappear) and **incorrectness** (how the code is wrong, so the fix generalises). [P]
- Failure chain: defect -> infected state -> failure; investigate by working backward from the symptom. [S]
- Mapping: SAME in structure (the post is Zeller's Mastermind consistency rule applied to a fact table). EXTENDS with (a) the explicit prediction step, (b) the experiment log as a second artifact next to the matrix (facts come from experiments; the log says why each fact exists and how it was gathered, which is what the "reverify facts" tactic needs), (c) the causality/incorrectness acceptance test, (d) the infection-chain model, which gives "layers" a causal meaning: layer N+1 is a later link in the chain.
- Skill use: keep two files: `facts.md` (immutable, ID'd, with provenance) and `experiments.md` (hypothesis, prediction, command, expected, observed, outcome). The matrix cites fact IDs; facts cite experiment IDs.

### 3.2 Delta debugging (ddmin) [P]
https://www.debuggingbook.org/html/DeltaDebugger.html
- Reduces a failing input to a **1-minimal** one (removing any remaining element makes the test pass). Three outcomes per test: PASS / FAIL / **UNRESOLVED** (a different failure; treated as not-failing so the reduction step is rejected). General `dd` maximises the passing side and minimises the failing side until they differ by the *failure-inducing difference*. Best case ~log2 n tests, worst case O(n^2); needs deterministic, reasonably fast tests.
- Mapping: EXTENDS in three ways.
  1. 1-minimality is the precise form of the post's "each cause is strictly necessary" and of Pocock's "every remaining element is load-bearing".
  2. UNRESOLVED is the missing third value for the matrix and for repro attempts ("failed differently" is not "reproduced").
  3. **Building a control**: when variable and control differ on many axes (config flags, versions, hosts, data), run `dd` over the set of differing axes to find the minimal differing subset. This answers the post's open question "how to pick the right control" by constructing intermediate controls mechanically.
- Skill use: a `minimize-diff` routine for config/env/flag sets and input payloads; it requires a deterministic oracle (the strongest signal as the pass/fail test, not "doesn't crash").

### 3.3 git bisect (and flaky tests) [P]/[S]
https://git-scm.com/docs/git-bisect
- `git bisect run`: exit 0 good, 1-127 (except 125) bad, **125 = cannot test (skip)**, other codes abort. Skipping a commit adjacent to the culprit leaves the answer ambiguous. The script must give a consistent verdict per revision. [P]
- Flaky oracle problem: plain bisect is unreliable with a nondeterministic test. Google's ICST 2023 "Flake-Aware Culprit Finding" uses Bayesian inference plus noisy binary search with priors on which changes are likely, evaluated on >13,000 breakages. https://research.google/pubs/flake-aware-culprit-finding/ ; a third-party tool `git-bayesect` does greedy expected-entropy selection (aggregator listing only, unverified). [S]
- Mapping: EXTENDS. The post never addresses nondeterministic controls. Bisect/dd are the natural agent-run mechanical steps once an oracle exists, but only with the 125/UNRESOLVED escape hatch and repeated runs.
- Skill use: the bisect harness template always includes the skip path, runs the oracle N times, and records the observed flake rate; if the flake rate is above a threshold, switch to the probabilistic variant.

### 3.4 Agans, *Debugging: the 9 Indispensable Rules* [S]
https://embeddedartistry.com/blog/2017/9/6/debugging-9-indispensable-rules
Rules: Understand the system; Make it fail; Quit thinking and look; Divide and conquer; Change one thing at a time; Keep an audit trail; Check the plug; Get a fresh view; If you didn't fix it, it ain't fixed.

| Agans rule | Mapping to the post |
|---|---|
| Quit thinking and look ("look until the visible failure has only a few possible causes") | SAME as "code is an unreliable narrator", "facts before hypotheses" |
| Make it fail | CONTRADICTS-in-part: the post treats a repro as a hypothesis needing signal parity. Agans' sub-advice is to *stimulate* the real failure, not *simulate* it, which is the post's concern in different words. |
| Divide and conquer, keep the failing half; fix one problem before looking for others | SAME as progressive narrowing; "fix one first" EXTENDS (a known-bad part can mask the real bug) |
| Change one thing at a time; back out a no-effect change at once | SAME as control/variable discipline; EXTENDS to interventions, not just observation |
| Keep an audit trail | STRONGER than the post: the post asks for citations but has no durable experiment log |
| Check the plug (build loaded, defaults, start sequence) | EXTENDS the post's tactic 1: verify preconditions *before* trusting any fact |
| Get a fresh view: "Report symptoms, not theories" | STRONGER on reviewer design: give the reviewer facts, not your story |
| If you didn't fix it, it ain't fixed: remove the fix, see the failure return, reapply, see it stop | EXTENDS: interventional verification. The post validates a hypothesis by fact consistency only (passive). Where an intervention is safe, flip the suspected cause and re-measure the strong signal. |

- Skill use: acceptance criterion for "fixed" = the strong signal returns to control values with the fix on and (when safe) reappears with it off. For the latency bug that is "client resolves ~5 addresses with the fix, ~400 without".

### 3.5 Brendan Gregg: methodologies and anti-methods [P/S]
Catalogue: https://www.brendangregg.com/methodology.html ; USE: https://www.brendangregg.com/usemethod.html ; differential flame graphs: https://www.brendangregg.com/blog/2014-11-09/differential-flame-graphs.html
- **Anti-methods**: Streetlight (run familiar tools, look for obvious issues), Random change (alter things, keep what beats baseline), Blame-someone-else (hypothesise a component you do not own and redirect), Drunk man (change things at random until it goes away).
  - Mapping: EXTENDS as a failure checklist for agents. Streetlight = the agent greps code because it can. Drunk man = shotgun fixes. **Blame-someone-else = the auth team's "no logs, not us"**, and also an agent attributing to an upstream it cannot inspect. Each is a lintable behaviour in an investigation log.
- **USE method**: for every resource check utilisation, saturation, errors; errors first (cheap, easy to interpret); claims ~80% of server issues for ~5% effort; explicitly "one tool in a larger toolbox", and "the first problem found may be 'a' problem rather than 'the' problem". [P]
  - Mapping: EXTENDS as a fixed, cheap layer-1 pass (exhaustive over resources) before any hypothesis, and as a caution matching the post's multi-cause stance.
- **Drill-down analysis**: start at the highest level, examine the next level of detail, pick the most interesting breakdown, repeat. **Workload characterization**: who is causing the load, why, what, how does it change. **Problem statement method**: what changed, did it ever work, is it latency/errors. [P]
  - Mapping: SAME as progressive signal discovery (drill-down is its ancestor); STRONGER in prescribing *which* breakdown to open next ("most interesting" = largest difference between variable and control).
- **Differential flame graphs**: baseline vs regressed profile; a one-directional diff cannot show code paths that disappeared ("if code paths vanish completely in the second profile, then there's nothing to color blue"); fix = also render the negated diff, or an "elided" view. [P]
  - Mapping: SHARPENS the post's signal definition. Signals must be computed **in both directions** (present-in-variable-absent-in-control and the reverse).
- "Linux Performance Analysis in 60,000 Milliseconds" (ten fixed commands: uptime, dmesg|tail, vmstat, mpstat, pidstat, iostat, free, sar -n DEV, sar -n TCP,ETCP, top; errors and saturation first). https://www.thomas-krenn.com/en/wiki/Linux_performance_analysis_in_60_seconds [S]
  - Mapping: a ready-made "layer 1/2 default collection" for hosts. The post's call for default collection is this, institutionalised.
- Skill use: ship a `layer-playbooks/` reference per target type (host, k8s pod, macOS app, web, mobile; the post's figures 23-26) where each layer lists cheap commands and the artefacts they produce; the agent descends only when the matrix says every signal is weak.

### 3.6 Other human-method lineage (not deeply read)
Stuart Halloway's talk "Debugging with the Scientific Method" (problem statement, testable hypotheses, observation, refinement) is a widely cited practitioner treatment; I found only summaries. https://danielcompton.net/snippets/debugging-with-the-scientific-method [S]

---

## 4. Observability for agents: wide events, canonical log lines, vocabularies

### 4.1 Majors / Honeycomb: wide structured events, "observability 2.0" [P/S]
https://www.honeycomb.io/blog/time-to-version-observability-signs-point-to-yes
- Claim: a single source of truth of arbitrarily wide structured events with trace/span IDs; metrics, logs and traces are derived at read time. Pre-aggregated metrics "discard ... context at write time". High cardinality and dimensionality are the point.
- Status note: in a March 2025 interview Majors reports she stopped using the "2.0" label while keeping the mental model; a March 18 2026 podcast has her discussing agents closing the loop between code changes and production validation; Honeycomb markets "Agent Observability" and an MCP server. [S] https://www.techtarget.com/it-infrastructure/podcast/Charity-Majors-on-AI-observability-and-the-future-of-SRE
- Mapping: SAME and the independent source for the post's "aggregation destroys the value of the signal". EXTENDS with a concrete data model.
- Skill use: when the agent is asked to *add* telemetry, default to one wide event per unit of work with deployment metadata (commit, version, region, instance, flags) so control and variable can be split on any dimension afterward.

### 4.2 Honeycomb BubbleUp: Step 1 automated [P/S]
https://www.honeycomb.io/platform/bubbleup ; core analysis loop https://www.honeycomb.io/blog/debugging-with-the-core-analysis-loop-and-what-to-build-vs-buy
- You select an anomalous region; BubbleUp compares it to a baseline across hundreds of dimensions and surfaces the attributes that differ most. The "core analysis loop" is four steps (determine what you know; prove/disprove; look for why via outliers and correlated patterns; assess and repeat) and is framed as the scientific method; BubbleUp automates the "look for why" iteration.
- Mapping: SAME as control/variable and "signal = present in variable not in control". STRONGER because it is arithmetic over all attributes, not an agent eyeballing logs. It does not model competing hypotheses; the core loop is single-hypothesis. The post's matrix is the missing layer on top.
- Skill use: a `cohort-diff` script: input two cohorts of events (variable, control), output attributes ranked by distribution difference (categorical: share difference; numeric: effect size; counts: ratio) in both directions, plus a within-control A/A baseline (see 5.3) to discard noise. Works on JSONL log lines when no vendor tool is available.

### 4.3 Stripe canonical log lines [P]
https://stripe.com/blog/canonical-log-lines
- One long line per request, emitted at the end from middleware, written in an `ensure`/finally block so it still fires on exceptions, wrapped so a logging failure never fails the request. Fields include HTTP method/path/status, auth identity, rate-limiter result, **timing and resource counts (number of DB queries, objects allocated)**, request ID, team. Stable schema via protocol buffers. Queried with log search, filtered timecharts, and SQL in a warehouse.
- Mapping: STRONGER for the post's build-time claim ("had the application layer logged the number of DNS lookups, the strongest signal would have been at Layer 1"). Resource counts and fan-out counters are the category of signal the post says should be default.
- Skill use: a `signal-registry` checklist for new features: for every fan-out edge (DNS answers resolved, backends contacted, retries, queries, bytes) add a counter to the canonical event; default per-feature "control equivalence" fields (flag state, build) in the same event.

### 4.4 Existing observability skills for agents [P/S]
- Boris Tane's `logging-best-practices` (MIT): wide events per request per service, high cardinality, business context, **environment characteristics (commit, version, region, instance)**, one logger, middleware pattern. https://github.com/boristane/agent-skills/tree/main/skills/logging-best-practices [P] (A third-party skills index flagged it with an automated medium-risk warning; unverified, review before installing.)
- Addy Osmani's `observability-and-instrumentation`: "define working before instrumenting": write 2-4 questions an on-call will ask; every signal must answer one. https://github.com/addyosmani/agent-skills/tree/main/skills/observability-and-instrumentation [P]
- Honeycomb's own `agent-skill` repo exists (not read). https://github.com/honeycombio/agent-skill
- Mapping: Tane = SAME as the post's default data collection. Addy = CONTRADICTS the "collect as much as possible by default" stance in emphasis (question-first), though both agree on fan-out counters. Reconcile: wide events by default; use the on-call questions to decide which counters are mandatory.

### 4.5 OpenTelemetry semantic conventions as vocabulary [S]
- DNS conventions currently define only the metric `dns.lookup.duration` (opt-in, Development) with `dns.question.name` and `error.type`. No answer-count attribute. https://opentelemetry.io/docs/specs/semconv/dns/dns-metrics/ [P]. So the post's decisive signal (5 vs ~400 resolved addresses) has no standard name: a gap to fill locally.
- GenAI conventions moved to their own repository in June 2026; one source says still Development as of 21 Aug 2026, another claims stable in June 2026 (unreliable, AI-summarised). Agent spans: root `invoke_agent`, child model-call spans, `execute_tool` spans. https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/ (moved notice). [S] Treat stability as unconfirmed.
- OpenTelemetry Weaver: `registry check` validates convention definitions; **`live-check` validates emitted telemetry against a registry** (missing required fields, wrong types, deprecated names), usable in CI, with coverage stats and a non-zero exit on violations. https://opentelemetry.io/blog/2025/otel-weaver/ [S]
- Observer effect: Google's SRE troubleshooting chapter warns that verbose logging can itself worsen a latency problem and confuse results. https://sre.google/sre-book/effective-troubleshooting/ [P] This qualifies "collect everything by default": budget it and make it sampled or tail-triggered.
- Mapping: EXTENDS the post's build-time argument with an enforcement mechanism: a project signal registry (extends OTel names) plus a live-check gate in CI that fails when a required signal is not emitted.
- Skill use: for the post's "bake signals into gates": (1) registry entry for the signal; (2) Weaver-style check that it is emitted in the integration run; (3) a parity assertion on its value against the last good run (see section 5).

---

## 5. Deploy gating, canary analysis, differential, golden, metamorphic

### 5.1 Automated canary analysis (Netflix/Spinnaker Kayenta; Google) [S/P]
- Kayenta compares a canary against a **baseline that is a newly deployed instance with the same code and configuration as production**, rather than against the long-running production fleet; metrics are compared with statistical tests such as Mann-Whitney U. Netflix's own blog returned HTTP 403 in this session, so this is secondary: https://devops.com/google-taps-netflix-for-open-source-canary-analysis/ ; https://arxiv.org/pdf/1905.04648 (ChAP paper describes baseline/canary clusters); sequential testing for faster decisions: https://arxiv.org/pdf/2205.14762
- Google SRE Workbook, "Canarying Releases" [P] https://sre.google/workbook/canarying-releases/ :
  - Metrics must indicate problems, be **attributable** to the change, be **low-noise**, and have windows no longer than the canary.
  - **Compare concurrently** with a control (before/after comparisons import time-of-day noise).
  - **Split metrics by population**: a 20% canary error rate shows as 1% fleet-wide.
  - Also check absolute SLOs because both arms can degrade together.
  - Pitfalls: canary too small or short, unrepresentative traffic, imperfect isolation (a failing canary check does not always mean the canary is at fault), synthetic load missing state-dependent behaviour.
- Mapping: SAME as the post's control/variable and "repurpose the framework for canary analysis". STRONGER on control construction (fresh baseline, concurrency, population split) and an independent statement of "aggregation hides the signal". SHARPENS one point: Google recommends SLIs as canary metrics, the post calls SLIs weak. Both hold: SLIs are good **detectors** (is something wrong) and poor **localisers** (what). A gate should be two-tier: detector metrics for pass/fail, plus diagnostic parity signals (fan-out counts, DNS answer counts, cache hit ratios) that are cheap to compare and narrow the hypothesis space when the detector trips.
- Skill use: `gate-design.md` rules: fresh baseline, concurrent window, per-population split, tolerance derived from the within-baseline noise (5.3), absolute-threshold backstop, and a diagnostic bundle attached to the gate failure (the same cohort-diff output as 4.2).

### 5.2 Twitter Diffy: primary / secondary / candidate [P]
https://github.com/opendiffy/diffy
- Requests are multicast to three instances: candidate (new code), primary (last good), secondary (same last-good code as primary). Primary-vs-secondary disagreement is **noise** (nondeterminism); primary-vs-candidate disagreement is compared against it.
- Mapping: EXTENDS the post's "noise is a data point present in both control and variable" with a way to *measure* noise before blaming anything. This is an A/A test.
- Skill use: before ranking signals, collect a second control (or a second variable run). Any signal whose within-control spread is comparable to the control-vs-variable gap is noise. The same rule appears in the local profiling skill (variance envelope, 5.6).

### 5.3 GitHub Scientist [P]
https://github.blog/engineering/infrastructure/scientist/
- Run old (control) and new (candidate) code paths in production in randomised order, record result and duration for both, always return the control result, publish mismatches, allow ignoring known differences, sample with `enabled?`, restrict to side-effect-free code.
- Mapping: EXTENDS to *behavioural* parity at the function level: signals can be the equality of outputs and also of counts/durations. "Ignore known differences" is the MATCH/STATE axis idea (5.6).

### 5.4 Trace-based testing as pre-prod signal parity [S]
https://opentelemetry.io/blog/2023/testing-otel-demo/ (Tracetest example)
- Send a request, wait for the trace, assert on spans (attribute values, durations, dependencies, error propagation). Treat the project status as unverified.
- Mapping: the practical embodiment of the post's "pre-production would have caught it if it compared the client's DNS lookups to the previous successful run". Asserting an answer-count or distinct-backend count on a span is trivial once the attribute exists.

### 5.5 Differential, golden and metamorphic testing as parity checks
- Differential testing against a reference (McKeeman 1998; not re-verified here) and Metamorphic testing (Chen et al.; Segura et al. IEEE TSE 2016 survey) https://hdl.handle.net/11441/38271 [S]. Key point: metamorphic relations let you assert *relationships* without knowing the correct value.
- Local skill `testing-golden-artifacts` [L]: freeze known-good outputs, canonicalise nondeterminism (timestamps, UUIDs, addresses), human review of the golden, commit, diff forever; every diff is a bug or an intentional change needing approval; a "Golden Confidence Matrix" (volatility >=4 means scrub or fuzzy-match) to stop test rot. File: /home/pascal/projects/skills-private/skill_archived/jeffreys-skills/testing-golden-artifacts/SKILL.md
  - Mapping: EXTENDS. The post's gate compares *signals*, not outputs. Output goldens would not have caught the latency bug (outputs identical). The skill's scrubbing/canonicalisation is the technique for turning a run's telemetry into a stable **signal fingerprint** (distinct DNS answers, distinct backends per key, retry counts, cache hit ratio) that can be diffed with tolerances. Its weakness is rubber-stamped regeneration (`UPDATE_GOLDENS=1`); a signal fingerprint update should require citing the changed signal and the reason.
- Local skill `testing-metamorphic` [L]: MR strength matrix (fault sensitivity x independence / cost, implement only if score >= 2.0), property-based generation, and **mutation testing to prove each MR can fail** ("otherwise the MR is decorative and should be removed", kill-rate >= 80%).
  - Mapping: EXTENDS: applies the severity principle (2.3) to gates. The post says bake past signals into gates; this skill says prove each gate can go red. For signal-parity gates the mutation is "reintroduce the original bug and confirm the gate fails".
  - Candidate relations for the latency bug [inf]: "distinct shard targets contacted per key == 1"; "addresses resolved in feature-on run == addresses resolved in feature-off run (same topology)".
- Local skill `testing-conformance-harnesses` [L]: differential testing against a reference, golden fixtures, spec-clause coverage matrix, `DISCREPANCIES.md` for every intentional deviation, regenerate fixtures when the reference updates.
  - Mapping: the "STATE" axis of a comparison (intentional differences) needs a documented home so that a gate does not train people to ignore diffs.
- obra `verification-before-completion` [P] regression rule: "Write -> Run (pass) -> Revert fix -> Run (MUST FAIL) -> Restore -> Run (pass)". That is the gate-mutation test in one line.

### 5.6 Control construction rules (local) [L]
/home/pascal/projects/skills-private/skill_archived/jeffreys-skills/profiling-software-performance/references/APPLES-TO-APPLES-MATRIX.md
- For every comparison, classify each axis **MATCH** (must be identical, fail if not), **STATE** (differs by design, name it, publish both) or **RANDOMIZE** (irrelevant, vary it to show insensitivity; interleave A/B/A/B). The build-the-table-before-running rule.
- Also in the same skill: environment fingerprint attached to every run (CPU, kernel, toolchain, cold/warm cache, git SHA); baseline of >= 20 runs; variance envelope (<=10% p95 drift is noise, >10% investigate, >20% or three consecutive >10% escalate); "one lever per run".
- Mapping: STRONGER than the post on what makes a control valid. The post says a control is only as good as your confidence it is not broken the same way; this gives the checklist that produces that confidence.
- Skill use: `control-checklist`: a table of axes (code version, config, flags, data, topology, host class, time window, load, tool versions) with MATCH/STATE/RANDOMIZE and the evidence for each; the agent may not label a data point "signal" until the table exists.

---

## 6. Metastable failures, multi-cause failures, Five Whys, "no root cause"

### 6.1 Bronson et al., HotOS 2021 [P]
https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf
- Definition: a trigger causes the system to "enter a bad state that persists even when the trigger is removed", kept there by a **sustaining effect** (typically work amplification or reduced efficiency, usually tied to resource exhaustion). Lifecycle: stable -> **vulnerable** (healthy, but one of many triggers can tip it; many production systems run vulnerable on purpose for efficiency) -> metastable. "It is common for an outage that involves a metastable failure to be initially blamed on the trigger, but the true root cause is the sustaining effect." Failures that resolve when the trigger is removed (DoS, limplock, livelock) are not metastable. Recovery needs a "strong corrective push" (reboot, shed load). The feedback loop can be contagious to parts never exposed to the trigger.
- Follow-up: Huang et al., OSDI 2022 "Metastable Failures in the Wild" (22 failures across 11 organisations; at least 4 of 15 major AWS outages in a decade; retry-driven load increase reported in over 50% of cases per the slides, denominator unverified). https://www.usenix.org/conference/osdi22/presentation/huang-lexiang [S]
- Mapping: SAME as the post's retry-after-capacity-drop example, but SHARPENS the role structure. The post treats the two causes as symmetric ("each strictly necessary"). Bronson says they differ: the trigger is one of many interchangeable events; the sustaining loop and the vulnerable state are what to fix. Persistence after trigger removal is itself a discriminating fact.
- Skill use: in a combined hypothesis, tag each component TRIGGER / SUSTAINING / VULNERABILITY / MISSING-BARRIER and recommend the fix target by role (break the loop, add the barrier). Add two standard facts to collect on any outage-shaped bug: "did the symptom persist after the trigger was removed?" and "did it spread to components not exposed to the trigger?".

### 6.2 Cook, "How Complex Systems Fail" [P]
https://how.complexsystems.fail/
- #3 "Catastrophe requires multiple failures - single point failures are not enough." #4 complex systems contain latent failures (a shifting mix). #5 they run in degraded mode. #7 "Post-accident attribution to a 'root cause' is fundamentally wrong" because "there is no isolated 'cause' of an accident". #8 hindsight bias "remains the primary obstacle to accident investigation".
- Allspaw, "Each necessary, but only jointly sufficient" https://www.kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/ [S], and "The Infinite Hows" https://www.kitchensoap.com/2014/11/14/the-infinite-hows-or-the-dangers-of-the-five-whys/ [P]: Five Whys "locks you into a causal chain, which is not how the world actually works"; the root cause is constructed ("We've 'found' a root cause when we stop looking"); human error is "a starting point, not a conclusion"; ask "how" to expose local rationality; look for multiple contributing conditions.
- Mapping: SAME on multi-cause (the post's "each cause strictly necessary" is Cook's "each necessary, only jointly sufficient"). SHARPENS the stopping rule: a skill that ends with "root cause found" is making Allspaw's point for him. CONTRADICTS the post's framing "in most cases a bug has a single root cause" only for incident-shaped failures; for deterministic code defects the single-chain view usually holds.
- Where Five Whys is still fine [inf]: descending a *deterministic* infection chain in code (obra and Addy both use it). Rule: every "why" answer must cite a fact; when the answer is "because A and B" the chain branches and the node becomes a combined hypothesis.
- Skill use: report format = "contributing factors with roles and evidence" plus the **intervention boundary** (what we can change) and a decision list for the human, matching the post's "present the options" instruction. Record hindsight risk: store what was known when each decision was made (timestamps in the experiment log).

### 6.3 Formalising "necessary" and where it breaks [S]/[inf]
- Mackie's INUS condition: a cause is an Insufficient but Necessary part of an Unnecessary but Sufficient condition. https://www.webpages.uidaho.edu/~morourke/442-phil/Fall%202004/Handouts/Philosophical/INUS-Analysis.htm (course handout, unreachable on 2026-10-13) This is the precise name for the post's combined hypotheses.
- Failure of the "remove each cause" test [inf]: with **overdetermination** (two independent causes, each sufficient, e.g. two leaks) removing one leaves the symptom, so a reviewer applying the test would wrongly call that cause unnecessary. Define necessity per **fact** ("does removing this component leave some fact unexplained?") not per **symptom** ("does the bug go away?"), and after any fix re-measure the strong signal: a residual means another cause exists (Agans: fix one first; the local deadlock skill's "Fourth Instance" rule).

### 6.4 Independent multi-bug (the third case) [P/S]
- Liblit et al., "Scalable Statistical Bug Isolation" (PLDI 2005): targets programs with several undiagnosed bugs at once; ranks instrumented predicates by how much their truth raises failure probability over the surrounding context, then performs redundancy elimination (explain the runs the top predictor covers, remove them, recompute). https://pages.cs.wisc.edu/~liblit/pldi-2005/pldi-2005.pdf [S: formula not confirmed here]
- ITBench-AA scores SRE tasks by precision **at full recall**: missing any ground-truth root cause scores 0, and extra submitted entities (upstream mechanisms, co-occurring symptoms) cost precision. https://artificialanalysis.ai/articles/itbench-aa-launch [S]
- Mapping: EXTENDS the post's single-vs-multi taxonomy with: single / conjunctive (INUS, metastable) / **disjunctive-independent** (different failing instances have different causes). The post's "same type of data from many instances" is exactly the input needed to cluster failing instances before ranking signals.
- Skill use: when instances disagree, cluster them by signal profile first, run the matrix per cluster, and report one causal story per cluster. The "stop at the strong signal" rule applies per cluster.

### 6.5 Google SRE postmortem conventions [S]
https://sre.google/workbook/postmortem-analysis : Google's template records **root cause and trigger** as separate fields; trigger breakdown from thousands of postmortems (binary pushes 37%, configuration pushes 31%). The SRE book's troubleshooting chapter lists pitfalls: irrelevant symptoms, spurious correlations, "assuming a past cause must be the cause again". https://sre.google/sre-book/effective-troubleshooting/ [P]
- Mapping: SAME as Bronson's trigger/cause split in institutional practice. The "past cause is not necessarily this cause" pitfall is directly relevant to the post's "give Claude previous postmortems": useful as a hypothesis source, dangerous as an anchor.

---

## 7. Existing agent skills for debugging and verification

### 7.1 obra/superpowers (adopted widely: ~298k stars, last push 2026-10-10 [P]) [P]
Files read: skills/systematic-debugging/{SKILL.md, root-cause-tracing.md, defense-in-depth.md, find-polluter.sh, CREATION-LOG.md}, skills/verification-before-completion/SKILL.md, skills/diagnosing-superpowers/SKILL.md.
https://github.com/obra/superpowers/tree/main/skills/systematic-debugging

What it does well (better than the post):
- Iron law: "NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST", plus rationalisation tables and "red flags" lists, and pressure scenarios (`test-pressure-*.md`) used to harden the skill against agent shortcuts. The post argues skill issues must become infrastructure; this is infrastructure for *compliance*.
- **Circuit breaker**: 3 failed fixes means stop and question the architecture, no fix #4. The post's memory-leak story is a 4-attempt run where the human re-steered at attempt 4.
- Layer-by-layer instrumentation at component boundaries for multi-component systems (a proto progressive-signal-discovery), and `root-cause-tracing.md` (trace backward through callers) and `find-polluter.sh` (bisect over tests).
- `defense-in-depth.md`: after the fix, validate at every layer so the bug is structurally impossible: the fix-side twin of the post's gating.
- `verification-before-completion`: "evidence before claims", with the red-green-revert regression check.
- `diagnosing-superpowers`: "Every finding cites `path:line`. No citation, no finding" and discard any analyst finding without a citation. Same mechanism the post credits with culling a third of the agent's claims.

Where it is weaker or contradicts the post:
- **Single hypothesis**: "Form Single Hypothesis ... Test Minimally." The post and Heuer/Platt/Chamberlin say competing hypotheses. CONTRADICTS.
- **"95% of 'no root cause' cases are incomplete investigation."** CONTRADICTS Cook/Allspaw/Bronson and pushes agents to invent a root cause. SHARPENS: its own section "When Process Reveals No Root Cause" (handle with retry/timeouts/monitoring) is the right terminal state; the 95% claim has no cited evidence in the file.
- Reproduce first, read recent changes and code, then instrument. No factual tier, no control/noise distinction (Phase 2 "list every difference" has no strength ranking), no multi-cause, no adversarial protocol, assumes you can add logging (the hang could not).
- Skill use: take the circuit breaker, the citation-or-discard rule, the rationalisation/pressure-test authoring method, defense-in-depth and the red-green-revert check; replace Phase 3's single hypothesis with the slate and matrix.

### 7.2 Matt Pocock `diagnosing-bugs` (~290k stars, pushed 2026-10-13) [P]
https://github.com/mattpocock/skills/tree/main/skills/engineering/diagnosing-bugs
- Phase 1 "Build a feedback loop ... This is the skill." A catalogue of ten loop types (failing test, curl script, CLI + snapshot diff, headless browser, **replay captured trace**, throwaway harness, property/fuzz loop, **bisection harness**, **differential loop** (old vs new, two configs), human-in-loop script). Loop must be **red-capable** (asserts the user's exact symptom), deterministic (or a pinned high reproduction rate), fast, agent-runnable. For nondeterminism, raise the reproduction rate (loop 100x, stress). If no loop: stop and ask for an environment, redacted artifact, or permission for instrumentation; "Do not proceed to hypothesise without a loop."
- Phase 2: confirm the loop reproduces **the failure the user described, not a different failure nearby**; minimise until every remaining element is load-bearing. Phase 3: **3-5 ranked hypotheses, each with a prediction** ("If X is the cause, changing Y will make the bug disappear"); show the list to the user before testing. Phase 4: each probe maps to a prediction, one variable at a time, tagged debug logs, never "log everything and grep"; perf branch: baseline then bisect. Phase 5: regression test written before the fix **only at a correct seam** (the real bug pattern at the call site); "if no correct seam exists, that itself is the finding". Phase 6: cleanup, state the winning hypothesis in the commit.
- Mapping: STRONGER on repro engineering, minimisation, regression seams, hygiene and prediction-bearing hypotheses. SAME on "match the user's failure" (Phase 2), which the post makes rigorous with signal parity: Pocock's check is symptom-level, the post's is signal-level. CONTRADICTS the post when no repro is possible (see verdict 8). Weaker: no control/noise, no diagnosticity, no multi-cause, no layered data discovery.
- Skill use: adopt "red-capable" as the acceptance test for a probe harness, add "signal parity" as the acceptance test for *this-bug-ness*, keep the show-the-slate-before-testing checkpoint, adopt "no correct seam is a finding".

### 7.3 Addy Osmani `agent-skills` [P]
https://github.com/addyosmani/agent-skills/tree/main/skills
- `debugging-and-error-recovery`: Stop-the-line rule; reproduce -> localise -> reduce -> fix -> guard -> verify; decision tree for non-reproducible bugs (timing, environment, state, truly random); bisect; "Ask 'Why does this happen?' until you reach the actual cause". Mapping: a competent default, weaker than the post on evidence (no hypothesis set).
- `doubt-driven-development`: a **fresh-context reviewer biased to disprove** is spawned on non-trivial claims; the claim is extracted as artifact + contract with **reasoning stripped**; findings reconciled against the artifact text; stop after trivial findings or 3 cycles; cannot be nested from a subagent. Mapping: SAME as the post's reviewer-as-eliminator, and the stripped-reasoning idea matches Agans "report symptoms, not theories" and mitigates framing effects. EXTENDS the post's reviewer design on operations. It still hands the reviewer an *artifact*, not the **factual tier**, so by the post's argument the reviewer cannot detect a missing constraint. Improvement: hand over the fact table and control, ask "which fact contradicts this row; which fact is missing that would discriminate?".
- `observability-and-instrumentation`: see 4.4.

### 7.4 Others seen (shallow)
- `mr-karan/pi-sre-mode` `sre-methodology`: 4-step loop (observe, hypothesise, test with "one command that distinguishes hypotheses", evaluate), "avoid command carpet-bombing", "compare against baseline when possible", read-only posture; short and generic. https://github.com/mr-karan/pi-sre-mode/blob/main/skills/sre-methodology/SKILL.md [P]. Its phrase "one command that distinguishes hypotheses" is Platt's Question in one line.
- Many other skills exist (error-detective, bug-investigation, incident); not read.

### 7.5 Local archived skills (Jeffrey Emanuel set) [L]
Root: /home/pascal/projects/skills-private/skill_archived/jeffreys-skills/

| Skill | What it does | Better than the post | Worse than the post |
|---|---|---|---|
| `gdb-for-debugging` (63 KB) | Tool manual and 8-step loop (triage -> relax ptrace -> attach -> analyse -> targeted dive -> diagnose -> fix -> verify) for hangs, crashes, races, deadlocks, containers, core dumps; `--batch`, `timeout`, save output; bug-class decision tree | Supplies the **how** for layer 3-4 collection that the post only draws; "Kill process to debug it destroys the evidence" is the post's restart-wiped-the-evidence problem; "Guess at deadlock -> build lock graph, read `__owner`, prove the cycle"; considers TSAN/rr before GDB for races | Step 6 "Map symptoms to root cause" is exactly the unconstrained inference the post warns about; no hypothesis set, control, or fact/hypothesis separation; assumes a live process |
| `multi-pass-bug-hunting` | Audit -> fix -> rescan cycle using a bug scanner (`ubs`) plus "fresh eyes" re-read; convergence = clean scan, tests pass, no new findings on re-read | Recognises fixes create bugs (pass 3 integration); written convergence criteria; per-pass documentation | Not root-cause analysis. "No new findings on re-read" by the same agent is a low-severity test (Mayo); no falsification step; "Review fellow agents' code ... first-principle analysis" has no evidence structure |
| `multi-model-triangulation` | Generates prompts for a human to paste into other models and synthesises; "Consensus = confidence"; manual copy-paste flow | Different providers do give partly different blind spots; the synthesis table separates consensus/divergence | **CONTRADICTS** the post and Kim et al. (agreement-when-wrong 60%; "Nine Judges, Two Effective Votes"): agreement is not verification. Use other models only to attack, never to vote. The manual relay is also obsolete next to subagents/headless CLIs |
| `brenner` (Brenner Bot) | Research-session CLI built on Sydney Brenner's method: 7-section artifact (hypothesis slate **3-6 with a mandatory third alternative**, predictions table, discriminative tests with **potency check**, assumption ledger with **scale check**, anomaly register, adversarial critique); linter with ~40 rules, e.g. EH-003 no third alternative, **WP-001 a prediction does not discriminate**, WT-001 test without potency check; operators: Exclusion-Test, Theory-Kill (KILL needs a reason), **Chastity-vs-Impotence** ("distinguish won't from can't before accepting a negative"), Exception-Quarantine, Scale-Check | The closest prior art in spirit: enforces exclusion-over-confirmation structurally; third alternative; a potency check on negatives (= Heuer 1.5 / Mayo 2.3); anomaly quarantine; kill-with-reason | Heavy infrastructure (Agent Mail, ntm, Bun CLI, corpus); no factual tier (hypotheses and anchors mix), no control/variable, no layers; research-oriented rather than runtime-evidence-oriented |
| `profiling-software-performance` | 7-step loop (define, environment, baseline, instrument, profile, interpret, hand off); scenario + environment fingerprint, >= 20-run baseline with variance envelope, one lever per run, **hypothesis ledger (supports/rejects + evidence)**, hotspot table where every row cites an artefact, honest-gate 14-question checklist, apples-to-apples MATCH/STATE/RANDOMIZE matrix, triangulation recipe (3 orthogonal angles; "two signals can collude"), CI regression gates | Quantified noise handling and control fairness; evidence-cited ledger; `perf.profile.hypothesis_evaluated` structured log; gates | Perf-only; "3 of 3 agree -> act" is consensus-based (mitigated by orthogonality); no multi-hypothesis matrix |
| `deadlock-finder-and-fixer` | Taxonomy of 9 concurrency classes, static audit, fix catalogue, five-step validation loop; **Universal Rule "The Fourth Instance"**: after fixing the three you can see there is almost always another, search the hazard class exhaustively; **False-Positive Rule**: a pattern match is not a bug until you can construct a concrete interleaving | Post-fix hazard-class sweep (residual check); a concrete-witness requirement that doubles as an eliminator; 10x stress after the fix; deterministic regression test | Assumes repro and source access; single-cause framing; grep audits |
| `reality-check-for-project` | Project status vs README/plan: phased "where are we really" prompts, bridge plan, bead creation, refinement rounds; "Code = ground truth for current state; docs = measuring stick for vision" | Periodic steering to prevent drift in long multi-agent efforts | Not a debugging skill. Its "code = ground truth" is about project state, not runtime causality, so it does not conflict with the post. Low value for RCA |
| `testing-golden-artifacts`, `testing-metamorphic`, `testing-conformance-harnesses` | See 5.5 | Gate mechanics: scrubbing, MR strength scoring and mutation validation, discrepancy ledger | Output-oriented; need a signal-fingerprint layer for the post's gates |
| `modes-of-reasoning-project-analysis` | Evidence-first analysis with **atomic claims in a JSONL ledger, stable `E###` evidence IDs, an independent auditor for every material claim ("an author may not certify its own claim")**, checked nulls count as success, no finding/disagreement quotas, "headcount never multiplies one evidence path", unsupported challenges are rejected not preserved for balance; **correlated evidence list** (same grep, paraphrase, inherited false premise, several static analyses of the same runtime behaviour) and "independence requires a route that could fail separately" | Best available rules for what counts as independent corroboration and for keeping the reviewer honest; claim-level audit; ID discipline | General project analysis, not a debugging loop; heavy NTM orchestration; exhaustive paperwork risks ceremony |
| `running-the-gauntlet-on-your-rust-port` | Parity certification for a Rust port; **negative ledger with load-bearing retry-condition predicates** (8 verbatim forms such as "Retry only if a profiler attributes a clearly-above-noise share to X on workload Y"); "Deep Hypothesis Review" scoring `(expected mind-change x downstream option value) / (time x cost x ambiguity x infrastructure-dependence)` to pick the next probe ("the one that kills more candidate hypotheses per token wins"); pass-over-pass ratchet gates; "honesty is encoded in the harness, not the reviewer" | Concrete probe-ranking formula; dead hypotheses stored with reopen conditions; ratchet | Port-specific; very large |
| `just-say-no-to-process-porn-and-ceremony` | Detects ceremony and reward hacking; **creation gate**: a process artifact may exist only if it names a concrete consumer, the gate it enforces, the observed defect class that justifies it, and a deletion condition; **boundary test: "does running code branch on this artifact?"** | Design guardrail for our own skills: the matrix and ledgers must drive probe selection or a gate, or they are process theatre | Not a debugging method |
| others skimmed by description only | `codebase-archaeology` (code-first mental models; fine for onboarding, opposite of the post's order for RCA), `ubs`/`codebase-audit`/`mock-code-finder` (static scanners), `testing-fuzzing` (input generation), `rust-undefined-behavior-exorcist` (Miri/sanitizers/loom, "prove, fix"), `beads-compliance-and-completion-verification` (audit that closed work was really done), `cass` (mine past sessions; used by the gauntlet to find prior failures) | `cass`-style retrieval of past failures is a hypothesis source (but see 6.5 anchoring caution) | |

---

## 8. Agent-driven RCA research and failure-mode evidence (2023-2026)

### 8.1 Benchmarks show low absolute performance and process-level failure [S]
- **OpenRCA** (Microsoft, ICLR 2025): 335 failures, 68 GB telemetry; best result 11.34% (Claude 3.5 with a purpose-built RCA agent). https://iclr.cc/virtual/2025/poster/32093 Traversal's critique: the benchmark lacks deployments, config changes and feature flags (often the real disambiguators), supplies telemetry as files, and can be hill-climbed without addressing causation. https://www.traversal.com/blog/openrca-isnt-root-cause-analysis-why-that-matters (vendor).
- **ITBench** (IBM, ICML 2025): SRE scenarios resolved 11.4% in the final version (13.8% in arXiv v1). https://arxiv.org/abs/2502.05352 **ITBench-AA** (Artificial Analysis + IBM, May 2026): top 47% (Claude Opus 4.7), all frontier models under 50%; **more turns did not help** (83 turns -> 30%, 31 turns -> 46%); over-investigation flags upstream mechanisms and co-occurring symptoms as false positives; any missed root cause zeroes the run. https://artificialanalysis.ai/articles/itbench-aa-launch
  - Mapping: SAME as the post's "stop descending when a strong signal emerges"; STRONGER evidence that unbounded tirelessness is not a strength. Co-occurring symptoms flagged as causes is the failure the control/variable step exists to prevent.
- **"Why Do AI Agents Systematically Fail at Cloud Root Cause Analysis?"** (arXiv 2602.09937): 1,675 runs on OpenRCA across five models; 12 pitfall types in three areas (intra-agent reasoning, inter-agent communication, agent-environment interaction); most prevalent: **hallucinated data interpretation** and **incomplete exploration**, present at every capability tier; prompt engineering alone does not fix the dominant pitfalls; a richer inter-agent protocol cuts communication failures by up to 15 points. https://arxiv.org/abs/2602.09937
  - Mapping: SAME as "agents build baseless narratives"; supports architecture over prompting ("skill issue to infrastructure issue").
- **"Beyond Fault Localization: A Trajectory-Level Study of LLM Agents for Microservice RCA"** (arXiv 2608.21310): 5,000 trajectories; failure families: drift to unrelated services, repeated shallow querying, omitted evidence, misinterpreted evidence, unsupported reasoning. Successful runs use retrieved evidence to steer later queries, hold broader diagnostic intents, go deeper. A lightweight defence raised Acc@1 by 3.5-35.1 points across all configurations. Recommends process-level evaluation ("correct, well-grounded, open to improvement"). https://arxiv.org/abs/2608.21310
  - Mapping: EXTENDS. Gives a lintable taxonomy for investigation logs and a reason to evaluate our skill on grounding, not final answer only (correct localisation can hide weak causal reconstruction).

### 8.2 Evidence curation beats evidence volume [S]
- **EviRCA** (arXiv 2609.19825): a deterministic extraction stage turns raw metrics/traces/logs into compact "evidence cards"; the LLM reasons only over the cards through read-only tools and never sees raw telemetry. 40.6-43.9% correct vs <=15.2% for earlier OpenRCA baselines, 15-26x fewer tokens, 3-20x faster; the remaining bottleneck is *judging* evidence, not finding it. https://arxiv.org/abs/2609.19825
  - Mapping: SHARPENS "fat factual tier". The tier should be fat in the store and thin in the context, and deterministic extraction is the strongest form of "facts the agent cannot alter".
- **Datadog Bits AI SRE**: hypothesis loop with sub-hypotheses; each hypothesis ends **validated / invalidated / inconclusive**; failure modes found: summarisation prompt grows linearly with tool calls, **distraction by noise** (Kafka lag incident misled by upstream application errors), **stopping at the symptom** (reported OOM, missed the oversized payloads behind it); improvements: hypothesis-scoped queries, recursive deepening, benchmark-driven iteration on human-labelled incidents with an LLM judge aligned to human labels. https://www.datadoghq.com/blog/building-bits-ai-sre/ ; docs https://docs.datadoghq.com/bits_ai/bits_ai_sre/investigate_issues
  - Mapping: SAME (hypothesis-scoped evidence is the post's matrix by another name); EXTENDS with "inconclusive" as a legitimate terminal state and a tree structure (validated hypotheses spawn sub-hypotheses) for the "stopping at the symptom" failure that a flat matrix can hide.

### 8.3 Scientific-debugging loops with LLMs [S]
- **AutoSD** (Kang, Chen, Yoo, Lou; arXiv 2304.02195; EMSE 2024): the LLM proposes a hypothesis and a concrete experiment; a debugger/executor runs it and returns the real output; the LLM decides verified/not. Competitive repair results; a 20-person study found explanations improved patch-correctness judgement on 5 of 6 bugs. An ablation reported by a secondary source: removing real execution made plausible predictions ~11% less likely. https://arxiv.org/pdf/2304.02195
  - Mapping: SAME as Zeller and the post's immutable-facts principle; the design point worth stealing is that **observations come from execution, not from the model**.
- **debug-gym** (Microsoft, arXiv 2503.21557): giving agents `pdb` and similar tools; strongest models only partly use the tools and remain far from proficient debuggers; authors suspect scarce sequential-debugging data in training. https://arxiv.org/pdf/2503.21557
  - Mapping: SAME as the post's claim that agents do not set up controls or gather lower-layer facts until told; justification for a skill that names the probes.
- **Self-repair** (Olausson et al., arXiv 2306.09896): the bottleneck is the quality of the model's own feedback on its code; stronger-model feedback helps substantially. https://arxiv.org/abs/2306.09896. Supports spending effort on the diagnosis (factual tier) rather than on more repair attempts.

### 8.4 Anchoring and failure to recover [S]
- **"LLMs Get Lost in Multi-Turn Conversation"** (Laban et al., arXiv 2505.06120): average -39% over six tasks in 200k+ simulated conversations; models make assumptions early, attempt final answers prematurely, over-rely on their earlier attempts; "when LLMs take a wrong turn ... they get lost and do not recover". https://arxiv.org/abs/2505.06120
- **"Root-Cause Attribution Is a Search Problem"** (arXiv 2609.13463): one-shot LLM judges settle on a plausible diagnosis early and miss sparse, distant evidence in long traces; a "Continual Search" loop that keeps looking for unresolved evidence before committing raised F1 by 29% (0.471 to 0.608) on a 50-trial testbed; lower-tier models sometimes beat higher-tier ones with better search. https://arxiv.org/abs/2609.13463
- Mapping: STRONGER evidence for the post's anchoring concern (memory-leak story: three failures before the fourth attempt, which succeeded only after the human supplied the facts as constraints). Concrete mitigations: after a hypothesis is retracted, restart from the fact table in a fresh context with the retracted hypotheses held in a negative ledger, not live in the conversation; require an explicit "unresolved evidence" list before any conclusion.

### 8.5 Confirmation bias and falsification in LLM hypothesis testing [S]
- **"Failing to Falsify"** (ICLR 2026, arXiv 2604.02485): eleven LLMs on a rule-discovery task tend to propose tests that confirm their current hypothesis; prompting with counterexample interventions raised average discovery from 42% to 56%; the behaviour can be distilled. https://arxiv.org/abs/2604.02485. **FalsifyBench** (arXiv 2606.04751; search snippet only) reports a strong negative correlation (Spearman -0.937) between confirmation-biased testing and conclusive falsification.
- **Framing in automated code review** (arXiv 2603.18740): contextual bias injected via PR metadata against Claude Code and CodeRabbit pipelines succeeded in 32 of 33 CVE cases after LLM-assisted refinement (template attacks failed). https://arxiv.org/abs/2603.18740
- Mapping: STRONGER for the post's adversarial-review section and the exact mitigations. (a) Make the reviewer's task "produce a test that would falsify" and require it to output a contradiction or a checked null. (b) Never put the author's conclusion or justification in the reviewer's prompt; treat narratives, commit messages and PR text as untrusted framing. (c) Human cognitive-forcing training showed no effect in a controlled trial (2.4), so these must be structural.

### 8.6 Correlated reviewers [S]
- Kim, Garg, Peng, Garg, ICML 2025 "Correlated Errors in Large Language Models": 350+ models; on one leaderboard models agree 60% of the time when both are wrong; more correlation for same provider, architecture or size, and for more accurate models; LLM judges overstate weaker same-family models. https://arxiv.org/abs/2506.07962
- "Nine Judges, Two Effective Votes" (arXiv 2605.29800): nine frontier judges from seven families behave like about two independent voters; the best single judge matches or beats the whole panel; aggregation closes at most 11% of the gap; "scaling up panels cannot substitute for genuinely independent evaluation". https://arxiv.org/abs/2605.29800
- Mapping: STRONGER quantification of "two agents concurring is one opinion counted twice". Rule: independence must come from a different **evidence path or method** (see modes-of-reasoning in 7.5), not from a different persona or another instance of the same model.

---

## Top 10 borrowings (ranked by value to an agent skill system)

1. **Pre-registered discrimination before every probe** (Platt's Question; Zeller's prediction step; Google SRE "mutually exclusive alternatives"; Brenner lint WP-001; Pocock's falsifiable predictions; the gauntlet's mind-change-per-cost formula).
   - Skill: before running any command, write for each live hypothesis what outcome it predicts. Refuse or flag a probe where all predictions are equal. Rank probes by hypotheses split per unit cost. Turns the post's retrospective column-reading into the choice of the next action. Maps as STRONGER/EXTENDS.

2. **A tri-state, cited, disconfirmation-first matrix** (Heuer ACH steps 3-7; Zeller's UNRESOLVED; Brenner's third alternative).
   - Skill: cells are C / I / N-A / ? with a fact ID each; "?" cells are the next probes; rank by weighted inconsistencies when no row is clean; always include a "none of these / something not on the list" row; unproven hypotheses stay LIVE until a cited fact kills them; keep the post's hypotheses-as-rows layout (supported by the 2024 experiment); cap the live slate around 3-7.

3. **Anti-anchoring machinery: negative ledger, restart-from-facts, circuit breaker, honest "inconclusive"** (gauntlet's retry-condition predicates; Laban "lost in conversation"; Continual Search; obra's 3-failed-fixes rule; Datadog's inconclusive state).
   - Skill: a retracted hypothesis moves to a ledger with the killing fact and a retry condition; after a retraction or three failed fixes, rebuild the working set from the fact table in a fresh context; conclusions require an empty "unresolved evidence" list or an explicit inconclusive verdict. Addresses the most documented agent failure mode.

4. **Step 1 toolkit: valid control, noise floor, bidirectional automated diff** (Kayenta fresh baseline; Google concurrent/split-by-population; Diffy A/A; local MATCH/STATE/RANDOMIZE; BubbleUp; differential flame graphs; Liblit; delta debugging over axes).
   - Skill: build the axis table first; measure within-control spread before calling anything signal; compute `cohort-diff` in both directions across all attributes; if control and variable differ on many axes, `ddmin` over the axis set to construct intermediate controls; cluster failing instances before ranking (independent causes).

5. **Expected-evidence and potency check on every negative** (Heuer "can I realistically expect to see evidence of it?"; Brenner chastity-vs-impotence; Mayo severity; Agans check the plug).
   - Skill: store each negative with channel, host, window, tool version and whether the thing would have shown up. A validation that could not have failed is logged "not tested". This would have caught the auth team's "no logs, not us" and the cert-reload theory surviving a blind subagent.

6. **Evidence cards, thin working set, citation-or-discard** (EviRCA; AutoSD's execution-sourced observations; Heuer ch. 5; obra `diagnosing-superpowers`; the post's citation rule).
   - Skill: facts are produced by deterministic scripts into ID'd cards with provenance; only the cards (and the matrix) enter the reasoning context; any claim without a fact ID is dropped; confidence is derived from the matrix, not from the amount of data.

7. **Reviewer independence rules** (Kim et al.; Nine Judges; framing-effect paper; Agans "report symptoms, not theories"; Addy's stripped-context reviewer; local modes-of-reasoning correlated-evidence rules; Failing to Falsify).
   - Skill: the adversarial reviewer receives facts, control and hypothesis rows only (no narrative), must return a contradicting fact, a missing discriminating fact, or a checked null; independence = a method that could fail separately; the author cannot certify its own claim; unsupported objections are rejected too; cross-family models are used for elimination only, never for votes.

8. **Cause-role taxonomy and residual checks for multi-cause failures** (Bronson trigger/sustaining/vulnerable; Cook and Allspaw; INUS; Liblit; ITBench-AA full-recall scoring; the deadlock "Fourth Instance").
   - Skill: label each component TRIGGER / SUSTAINING / VULNERABILITY / BARRIER; collect "persisted after trigger removal?" and "spread to unexposed components?"; define necessity per fact (not per symptom) to survive overdetermination; after the fix, re-measure the strong signal and sweep the hazard class for other instances; report contributing factors and the intervention boundary instead of "the root cause".

9. **Build-time default signals with a registry and a live check** (Stripe canonical log lines; Majors wide events; Tane's logging skill; OTel semantic conventions and Weaver live-check; Google's observer-effect warning).
   - Skill: when adding a feature, add fan-out counters (resolved addresses, backends contacted, retries, queries) and deployment metadata to one canonical wide event; register the signal name (extend OTel where absent, e.g. DNS answer count); CI fails if a registered signal is not emitted; budget the cost (sampling or tail-triggered).

10. **Gate construction rules plus a gate mutation test** (Kayenta and Google canary rules; Diffy; Scientist; Tracetest-style span assertions; golden-artifact scrubbing; metamorphic mutation validation; obra red-green-revert; gauntlet ratchets).
    - Skill: two-tier gate (detector SLIs plus diagnostic parity signals), fresh concurrent baseline split by population, tolerances from the measured noise floor, signal fingerprints with scrubbing and an approval note on change, and a required step: reintroduce the original bug on a branch and prove the gate goes red.

### Honorable mentions (not in the ten)
- **Repro as a probe generator**: Pocock's ten loop types and "red-capable" criterion plus the post's signal-parity test; "no correct regression seam is itself a finding"; Agans "if you didn't fix it, it ain't fixed" as interventional verification.
- **Fixed cheap layer playbooks**: Gregg's USE/60-second checklist per target type; Gregg's anti-methods (streetlight, drunk man, blame-someone-else) as a lintable list of agent behaviours; local `gdb-for-debugging` batch recipes for layers 3-4 with `--batch` and `timeout`.
- **Creation gate for process artifacts** (`just-say-no-to-process-porn-and-ceremony`): every artifact must name its consumer, gate, defect class and deletion condition, and running code must branch on it; apply to the matrix and ledgers so they steer probes instead of decorating reports.
- **Cognitive stop points** (first10em): pause before the first probe, when no row is clean, when a fix fails, and at handoff.
- **Process-level evaluation of the skill itself**: grade grounding and coverage of an investigation (2608.21310), not just the final answer; build a labelled incident set as Datadog did.
- **Pressure-testing skills with adversarial scenarios** (obra `test-pressure-*.md`, `CREATION-LOG.md`).

---

## Reliability notes and gaps

- Not read in primary form: Netflix's Kayenta blog (HTTP 403; baseline-design claim is from DevOps.com and the ChAP paper), McKeeman 1998, Chamberlin's original (scan), Huang et al. OSDI 2022 full text (percentages unverified), Halloway's talk, Liblit's formulas (described, not confirmed), AIOpsLab / RCAgent / RCACopilot (not searched in depth), FalsifyBench (search snippet only).
- Several 2026 arXiv papers cited here (2602.09937, 2604.02485, 2603.18740, 2605.29800, 2608.21310, 2609.13463, 2609.19825) were verified against their abstract pages only; per-category numbers inside the papers were not read.
- The only first-hand quantitative claim about ACH effectiveness in the sources I checked is mixed; ACH is a structure that forces disconfirmation, not a validated debiaser. Keep the enforcement mechanical.
- Debiasing-by-instruction has weak human evidence (Sherbino trial; First10EM) but nonzero LLM evidence (Failing to Falsify). Build both structural and prompt layers; measure.
- Where the post says something with no counter-evidence found: "read the code last" is conditional. Pocock, obra and Addy begin with a repro or error text; AutoSD and SWE-style work use code heavily; the post's order assumes telemetry exists. A skill should state the precondition: collect available facts first, then read code to generate hypotheses *constrained by those facts*.
