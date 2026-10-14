# Lead design (written before reading the delegates)

## Kernel
Facts constrain hypotheses. Facts are observed by instruments, carry provenance, and are append-only for the agent. Hypotheses are cheap, derived, and valid only when no fact contradicts them. A control turns facts into signals (present in variable, absent in control). A signal's strength is how few hypotheses it admits.

Unification: debugging and verification are the same operation at opposite ends of time.
- Build time: the change is the variable, the baseline (flag off, previous build) is the control. The feature's author pre-registers the expected diff (intended effects) and the invariants (must stay equal). Verification = signal parity check. Unexplained diff = a bug found before prod
- Run time: the bug is the variable. Find the hypothesis that explains the diff between variable and control
- So the build-time "signal contract" IS the factual tier pre-registered for the future bug. Same vocabulary, same artifacts, both directions

## Tower
L0 vocabulary: variable, control, fact, signal, noise, strong/weak, hypothesis (single, combined), constraint, layer, parity, intervention
L1 artifacts: case file (fact ledger + matrix + log) per investigation; signal catalog per project (lives in the project's verify-<app> skill: layers ladder, controls, signals per feature, known noise, parity gates, policies)
L2 operators: gather (cheapest layer first; broad diff when blind, discriminating probe when 2-3 survivors), diff (control vs variable), steer (column counts), refine (5 tactics in order), validate (every fact incl. noise, three-valued cells, no "?" left), repro parity, refute (adversarial elimination only), close (interventions -> infrastructure)
L3 workflows/routes: investigate (goal 2), refute (audit a claimed cause/repro/PR), instrument (goal 1: signal contract + default emission + parity check)
L4 integrations: poteto-mode bug-fix/feature/forensics/perf, verify-<app> skills + create/maintain-verification-skill, interrogate, feel-me for decisions, html-mode for matrix visual, fleet for read-only prod access

## Packaging
One mode, auto-triggered like code-review-mode: provisional name `debug-mode`, routes `investigate`, `refute`, `instrument`. SKILL.md holds vocabulary + route picker (one place per meaning). Close/retro is the last step of investigate, not a route. Gate is part of instrument.

## Case file (Markdown first, script later only if evals show bookkeeping errors)
Facts table: id, statement (arithmetic preferred), source (command/query/file, host, time window, tool version), layer, variable/control presence, class (signal/noise/unclassified), raw artifact path. Append-only; dispute = flag + re-gather request
Hypotheses: id, statement, parts (combined), derived-from signal ids, status (candidate/eliminated/validated/split/merged/combined)
Matrix: cells ✓ / ✗ (with fact citation) / ?. Column count = strength. Valid row = no ✗; Step 3 requires no ? either
Log: gathering actions with cost, tactics tried, layer descents, interventions (category: control, constraint, check, pushback, access, decision)
Next-action rule deterministic from state

## Refute (adversarial)
Different model family; receives facts + matrix, not the narrative. Allowed outputs: ✗ with fact citation, provenance challenge, control challenge (broken same way?), process checks (tactics before new hypothesis, descent only when warranted), remove-one test for combined, and "discriminating probes": facts that would split survivors. Never "confirmed"

## Accretion
- New strong signal -> feature file Signals + emit at layer 1 (issue/PR)
- Control recipe, layer ladder commands, known noise -> verify-<app>
- Parity gate -> verify-<app> + just recipe
- Human decision -> policy in project AGENTS.md or verify skill
- Method gap (agent needed a nudge) -> debug-mode eval scenario + skill fix
- Intervention count per case = agent-native score

## Conflicts
- poteto bug-fix step 2 seeds from `how` (code first) -> seed from signals; `how` targeted by the strong signal
- poteto bug-fix step 1 "force the repro" -> repro is derivative; requires signal parity with the factual tier
- interrogate as confirmation -> elimination only; add "missing facts that could falsify"
- fix-root-causes "ask why until root cause" -> hypothesis consistent with every fact; combinations with each cause necessary
- create-verification-skill full local launch -> fine for local tools; for services, prod facts outrank local repro

## Evals
Three paper scenarios with layer-gated fact files (the agent must request each layer): latency (cert reload red herring, DNS 5 vs 400), memory leak (split + combine), hang (sad-path control, kernel IPC, coworker's clock-skew repro fails parity)

## Phases
1 debug-mode with investigate + refute, case template, vocabulary, layer ladders; poteto bug-fix edits; 3 evals
2 instrument route + feature-file Signals/Control sections in create/maintain-verification-skill; poteto feature step
3 case.py if needed, bug-report issue template, parity just recipes per project, html matrix view
