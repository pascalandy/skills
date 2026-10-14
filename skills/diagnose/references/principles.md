# Principles

The rules the steps come from. Read them when a step does not fit the case, and decide by the rule rather than by the step's wording. Rules marked *(survey)* correct or extend the post from prior work.

## Stance

1. Start from facts, not code. Code says what can happen, not what did. Read code only to explain a named signal
2. Play to agent strengths: reading large raw data, joining sources across layers, knowing obscure tools and formats, rerunning checks, and writing throwaway probes
3. Guard against agent weaknesses with structure, not exhortation. Required fields, citations, and checks work; reminders do not *(survey)*

## Facts

4. Facts are append-only. A suspect fact is gathered again, never edited or argued away
5. An absence is a fact only with its coverage. "No logs" counts against a hypothesis only if the logs would have shown it *(survey)*
6. Keep the store fat and the working set thin. Raw artifacts stay on disk; the case file holds one short row per fact with a pointer *(survey: more data raises confidence, not accuracy)*
7. Prefer arithmetic to narrative: counts, sizes, durations. 26 queries per request against 2 settles what a paragraph cannot

## Controls and signals

8. No control, no signal. Pick a control that differs from the failing case in the suspected factor only, and write why it is not broken the same way
9. A louder failure that fails differently is often the cheapest good control
10. A signal is any reading that differs between the failing case and the control, in either direction. A reply the control receives and the failing case never gets is a signal *(survey)*
11. Measure the noise floor before calling a difference a signal: read two controls when readings vary *(survey)*
12. A signal is strong when few hypotheses explain it, ideally one. Service aggregates such as P99 are detectors, not locators

## Hypotheses

13. Every hypothesis cites the fact it starts from and states the prediction that would kill it
14. Keep a "none of these" reservation. One surviving row does not prove the list was complete, so every claim holds only among the hypotheses listed *(survey)*
15. Before each probe meant to tell hypotheses apart, write what each live hypothesis predicts. Skip it when the predictions all agree *(survey)*
16. One cited contradicting fact eliminates a hypothesis. Lack of support does not
17. When no row survives, repair the set before inventing: reverify facts, split coarse hypotheses, merge per-instance ones, combine complementary ones, and only then draw a new one from existing facts
18. When every signal is weak or the repairs fail, gather one layer down instead of guessing. Stop at the strongest signal, not the deepest
19. A combination is valid only when each member is needed to explain some fact. In an incident, the loop that sustains the failure matters more than the trigger *(survey)*
20. When failing instances disagree, they may be separate bugs. Cluster them and run one matrix per cluster *(survey)*

## Repros, review, and claims

21. A repro is a hypothesis. Keep it only if it shows the report's strongest signal
22. Adversarial review eliminates. It never confirms, because no reviewer can see a missing fact. Give the reviewer facts, not the story, and use another model family
23. After a retraction, generate the next hypotheses in a fresh context from the case file alone *(survey)*
24. State the claim level: consistent, confirmed, or fixed. Confirmed needs a test that no other live hypothesis passes. Fixed needs, after merge and where the bug was seen, the reading that exposed it back at the control's value, the reported symptom gone, and no residual failure

## The verify loop and accretion

25. Choose a feature's readings and their normal values before writing its code, and record them by default at the shallowest layer
26. A check that never failed proves nothing. The planted bug must fail a new check's first run
27. Every human intervention is a gap. The retros file each one as an issue for a reading, a probe, a check, or an eval, so the next case does not need it. A recurring gap becomes structure, never a prose reminder
28. People make the accountable calls. They do not relay commands or paste output for the agent
