# An evidence contract for building and debugging software

Design by the Codex designer, prepared independently on 2026-10-13

## Recommendation

Add one public helper, `evidence-loop`, and one route, `poteto-mode ; debuggability`. Rework the existing debugging routes to call the helper. Add an evidence-review branch to `interrogate`. Extend existing project verification skills with small, executable signal contracts. Keep their feature maps, drivers, doctor checks, evidence bundles, and cleanup behavior.

The system rests on one concept: an **evidence contract**. A claim names the observations that could refute it, the scope in which it applies, and the comparison that tests it. A feature contract specifies these before implementation. An investigation constructs them from an actual failure. Both use the same observations and comparison rules.

This adds a shared reasoning method, not another software factory platform. Start with files and the existing project commands. Deterministic tooling checks identities, references, measurements, and gate conditions. Agents choose useful questions and interpret mechanisms. Humans own unresolved product tradeoffs and operational authority.

The important change is what an agent does next. After ingesting a bug report, it sees the unresolved constraints and the cheapest discriminating observation. After implementing a feature, it sees the same contract's checks. After closing an incident, it can turn the observation that mattered into a cheaper default capture or a regression gate.

### Grounding and attribution

This design distills Cindy Sridharan's [How to effectively debug when you no longer understand the code](https://copyconstruct.medium.com/how-to-effectively-debug-when-you-no-longer-understand-the-code-bd3dcb2c5f7b), published October 10, 2026. I read all 1,468 lines of `/tmp/debug-post/post.txt`. The extraction contains figure captions, not the figures' complete visual contents. No proposed schema depends on reconstructing an unseen figure.

I inspected the requested public skills and supporting references at public checkout `6694b00ce031756a6e86d6f7c09ad45856469509`, and skimmed the named archived skills at private checkout `72aeb5508584daed29e47836326a186de4cc9bd8`. These revisions identify the inspected base, not future installation targets. The brief expressly selects these repositories. All paths proposed below are source paths under `authoring/`, never generated `skills/` paths.

The design's bounded gates, provenance rules, and resource controls are my additions. The three incidents supply motivating cases, not public production datasets. Public evaluations must use independently written fixtures.

### Alternatives considered

| Shape | What it buys | Why I reject it |
|---|---|---|
| A new `debug-mode` containing capture, review, reproduction, repair, and factory routes | One discovery name | Duplicates `poteto-mode` and leaves two owners for bug fixing, performance work, and runtime forensics |
| Separate skills for facts, controls, hypotheses, repros, adversaries, observability, and lessons | Narrow packages | Makes the coordinator learn the protocol by coordinating many shallow interfaces |
| Add the article's advice independently to every existing skill | Little initial machinery | Copies the matrix, evidence states, and parity rules into many places and guarantees drift |
| One shared helper plus existing routes and project contracts | One reasoning contract across build and runtime | Recommended because it concentrates the difficult decisions while keeping existing entry points |

I accept a small JSON working file alongside raw captures in exchange for resumable, checkable investigations. I accept project-specific collectors in exchange for avoiding a universal telemetry integration platform.

## 1. Knowledge extracted from the post

Each numbered item is one actionable principle. `Existing` means the active system already states the substantive practice. `Extended` means an existing practice needs a more precise contract. `New` means I found no equivalent explicit contract in the active skills inspected. This is novelty relative to this collection, not a claim of invention. Archived precedents appear separately.

### Case selection, observations, and explanation

1. Classify an investigation by familiarity, regression history, source access, reproducibility, and available verification before choosing its method

   Applies: Intake; coverage: New
2. Distinguish the failing variable, the comparison control, and the measured signals throughout the investigation

   Applies: Intake and experiments; coverage: Extended: `hillclimb` has baselines, but lacks a shared case vocabulary
3. Start a defect investigation with observed behavior and available captures before generating explanations from source

   Applies: Runtime diagnosis; coverage: Existing: runtime and trace forensics; conflicts with bug-fix hypothesis seeding
4. Read source to explain narrowed observations rather than treating possible execution paths as events that occurred

   Applies: Runtime diagnosis; coverage: New explicit boundary; `why` already separates evidence from inference
5. Match code, dependency versions, flags, topology, and deployment identity to the actual failing instance

   Applies: Capture and source attribution; coverage: Extended: verifier doctor checks and `blast-radius`
6. Treat aggregate service indicators as symptoms until a more selective observation identifies a mechanism

   Applies: Performance and availability; coverage: Extended: `perf-issue` measures, but has no selectivity test
7. Collect evidence across application, process, network, operating system, and dependency boundaries when the current layer does not discriminate

   Applies: Signal discovery; coverage: New shared progression; runtime forensics covers individual tools
8. Use agents to parse large captures, cross-reference formats, and run cheap repeated comparisons instead of imitating one engineer's favorite tools

   Applies: Tool selection; coverage: Existing in parts: trace forensics, `swarm`, runtime contract
9. Preserve externally obtained observations separately from every interpretation the agent makes about them

   Applies: All investigations; coverage: Extended: `why` epistemics and append-only decision trail
10. Resolve suspicious provenance through recollection or source-owner review rather than rewriting an inconvenient observation

   Applies: Conflicting evidence; coverage: New
11. Require the candidate mechanism to account for every applicable observation, including observations that did not differ

   Applies: Diagnosis; coverage: New explicit all-constraint gate
12. Keep a narrow active set of explanations while retaining broad accessible evidence

   Applies: Investigation cost control; coverage: Extended: context discipline and artifact reduction
13. Repeated patterns across independent failing instances strengthen an observation's relevance

   Applies: Incident correlation; coverage: New explicit recurrence check
14. Compare quantities such as endpoint counts, bytes, allocations, and timing whenever arithmetic can replace a narrative

   Applies: Signal reduction; coverage: Extended: performance measurements and verifier observations
15. Distinguish an activating condition such as scale from an additional cause that is needed to explain the failure

   Applies: Causal modeling; coverage: New
16. Represent interacting causes together when neither can explain the observations alone

   Applies: Multi-cause failures; coverage: New
17. Remove each proposed cause in turn and require a specific observation to become unexplained

   Applies: Combined explanations; coverage: New; archived `brenner` supplies an elimination precedent

### Controls, steering, and hypothesis repair

18. Prefer a control that differs from the variable on the suspected causal dimension while documenting other differences

   Applies: Experiment design; coverage: Extended: frozen workload in `hillclimb`
19. Use a well-understood alternative failure as a control when a successful case would introduce more differences or cost

   Applies: Intermittent and inaccessible failures; coverage: New
20. Check that the control is not affected by the same defect before using it to dismiss observations

   Applies: Control validation; coverage: New
21. Use differences between control and variable to select candidate signals

   Applies: Steering; coverage: Extended: before-and-after traces
22. Retain shared observations because they can contradict explanations even when they do not steer the search

   Applies: Validation; coverage: New explicit treatment of unchanged evidence
23. Rank signals by how few current explanations they fit rather than by how alarming the symptom looks

   Applies: Steering; coverage: New
24. Maintain a hypothesis-by-fact matrix so elimination and selection can be inspected and repeated

   Applies: Reasoning artifact; coverage: New; archived `brenner` has a predictions table
25. Read matrix columns to identify discriminating observations and rows to find explanations that survive all constraints

   Applies: Matrix use; coverage: New
26. Pursue a small promising set rather than exhaustively testing every imaginable explanation

   Applies: Experiment selection; coverage: Extended: binary search in bug-fix and scoped `blast-radius`
27. Recheck provenance before replacing all explanations when the matrix contains no surviving row

   Applies: Failed hypothesis set; coverage: New
28. Split a bundled explanation into independently testable mechanisms before discarding the whole bundle

   Applies: Failed hypothesis set; coverage: New
29. Merge local explanations into a shared mechanism when failure scope demands a common cause

   Applies: Correlated failures; coverage: New
30. Combine complementary explanations without hiding the necessity of each component

   Applies: Interacting failures; coverage: New
31. Generate a new explanation from existing observations only after cheaper repairs of the current set fail

   Applies: Failed hypothesis set; coverage: New
32. Acquire a new observation instead of multiplying explanations when the current evidence cannot separate them

   Applies: Discovery pivot; coverage: New explicit branch
33. Start with existing or inexpensive data and deepen collection only when the current evidence remains weak or inconsistent

   Applies: Discovery cost control; coverage: Extended: capture-first forensics
34. Stop descending as soon as a sufficiently discriminating signal appears

   Applies: Discovery stopping rule; coverage: New
35. Cite the underlying capture for causal assertions so unsupported claims can be removed

   Applies: Diagnosis and review; coverage: Existing: `why`, `blast-radius`, forensic replies

### Reproduction and adversarial review

36. Attempt an available reproduction while checking that it represents the reported incident

   Applies: Reproduction; coverage: Extended: bug-fix and `tdd` require failing-before evidence
37. Treat a synthetic reproduction's equivalence to the incident as a hypothesis

   Applies: Reproduction; coverage: New
38. Require reproduction parity on the strongest incident signals rather than accepting matching symptoms alone

   Applies: Reproduction; coverage: New
39. Track a real but mismatched reproduction separately so its fix cannot close the original incident

   Applies: Reproduction triage; coverage: New
40. Use adversarial review to seek contradictions rather than count agreement as verification

   Applies: Review; coverage: Extended: `interrogate` is adversarial but synthesis emphasizes consensus
41. Report that no reviewer can certify the completeness of the evidence set

   Applies: Review calibration; coverage: New
42. Distinguish independent sessions from independent model families when reporting review diversity

   Applies: Review calibration; coverage: Existing: `interrogate`, `arena`, runtime contract
43. Review signal distinctness, control validity, and collection provenance before reviewing the preferred explanation

   Applies: Review during discovery; coverage: New evidence-specific rubric
44. Review signal selectivity, hypothesis repairs, and the need to descend before endorsing the next investigation step

   Applies: Review during steering; coverage: New evidence-specific rubric
45. Challenge a final candidate with every observation and test each cause's necessity in a combined explanation

   Applies: Review during validation; coverage: New evidence-specific rubric
46. Let one evidenced contradiction defeat an explanation regardless of how many reviewers support it

   Applies: Review decision; coverage: Extended: source verification and skeptical bot triage

### Building the verification system and making it improve

47. Design verification around system outcomes and measurable invariants before generating feature code

   Applies: Feature planning; coverage: Extended: `figure-it-out`, verification generator, prove-it-works
48. Expose data that demonstrates correctness to external verification agents through usable commands and stable identities

   Applies: Feature instrumentation; coverage: Extended: project verification skills
49. Promote previously deep diagnostic signals into inexpensive default application captures when the operational cost is justified

   Applies: Observability improvements; coverage: New explicit promotion loop
50. Preserve raw evidence for agents while presenting concise decision points to humans

   Applies: Artifact design; coverage: Extended: raw verifier bundles and concise decision trail
51. Connect the available evidence sources instead of relying only on larger code context or indexing

   Applies: Factory investment; coverage: Extended: `why` source discovery, but runtime evidence needs its own coverage
52. Give collection scoped, read-only, time-limited, bounded, scrubbed, and auditable access

   Applies: Production evidence collection; coverage: Extended: runtime capability checks, with new access contract
53. Collect valuable diagnostic data by default on a bounded sample rather than discovering its absence during an incident

   Applies: Factory infrastructure; coverage: New
54. Capture each human intervention as a missing control, constraint, check, access path, or decision policy

   Applies: Accretion; coverage: Existing principle: encode-lessons-in-structure; extended incident taxonomy
55. Measure avoidable human intervention to discover where the supposedly autonomous process still needs infrastructure

   Applies: Factory evaluation; coverage: New explicit measure
56. Automate retrievable evidence and command execution instead of making humans relay machine-readable data

   Applies: Tool and access design; coverage: Existing: runtime adapters and observe-before-asking practice
57. Keep consequential product and operational tradeoffs with humans until a specific applicable policy resolves them

   Applies: Repair selection and operations; coverage: Existing: autonomy boundaries and genuine-decision questions
58. Convert repeated decisions into narrow policies that future agents can apply and audit

   Applies: Accretion; coverage: Extended: encode-lessons-in-structure
59. Compare plausible repairs with their actual tradeoffs when evidence identifies the problem but cannot choose the desired product behavior

   Applies: Multi-fix diagnosis; coverage: Existing: `architect`, `grill-for-unknowns`
60. Turn recurring prompting corrections into enforceable collectors, comparisons, tests, types, or gates

   Applies: Accretion; coverage: Existing: encode-lessons-in-structure
61. Verify changes as early as possible against representative deployment behavior and production-derived evidence

   Applies: Build verification; coverage: Extended: generator and feature workflow
62. Use an explicitly isolated production-like slice when authorized and necessary to preserve the important constraints

   Applies: Environment design; coverage: New infrastructure option
63. Judge a local stack by signal fidelity rather than assuming that running every service recreates production

   Applies: Environment selection; coverage: New explicit fidelity gate
64. Reuse controls and signal comparisons in integration tests, E2E checks, deploy gates, and canary analysis

   Applies: Cross-lifecycle verification; coverage: Extended: verifier maps; new common comparison contract
65. Check unchanged signal relationships as well as successful final outcomes

   Applies: Regression verification; coverage: New explicit parity gate
66. Convert incident signals into pre-deploy checks that can detect structural regressions even at smaller scale

   Applies: Regression verification; coverage: Extended: regression tests; new signal selection method
67. Preserve reliability, dependency behavior, resource use, and system coherence when selecting a repair

   Applies: Fix review; coverage: Existing: `blast-radius`, code review, root-cause principle
68. Require substantive evidence for verification steps so completed checklists cannot conceal ineffective tests or ineffective repairs

   Applies: Completion; coverage: Existing: prove-it-works and test-audit

69. Test whether an ongoing feedback mechanism sustains failure after the initiating event has ended

   Applies: Metastable failures; coverage: New explicit trigger-versus-persistence constraint

70. Measure leading indicators and downstream retry or load effects before aggregate symptoms become a wider availability failure

   Applies: Incident impact assessment; coverage: Extended performance measurement and blast-radius reasoning

These groups follow the source's cases at lines 105, 252, and 360; investigation framework at lines 528-1114; repro and review discussion at lines 1115-1244; and factory discussion in the remainder. The line ranges are reading locations, not verbatim excerpts.

## 2. The system and its layers

### Shared vocabulary

| Term | Exact meaning |
|---|---|
| Case | One bounded question about behavior, with a target, time window, authority, and closure criterion |
| Capture | Preserved output from an external source or an executed measurement, with collection identity and provenance |
| Fact | An immutable, scoped observation in a capture or an attributed user report |
| Hypothesis | An agent's proposed mechanism, interpretation, or claim of equivalence |
| Variable | The instance or condition exhibiting the behavior being investigated |
| Control | A deliberately selected comparison whose relevant differences and validity are recorded |
| Signal | A measured behavior whose relationship to the control is relevant to the case |
| Strong signal | A trustworthy signal that distinguishes the current candidate mechanisms |
| Contract | A versioned specification of the behavior, observations, comparisons, and failure sensitivity required for verification |
| Experiment | A predeclared procedure with predicted outcomes that can separate or refute hypotheses |
| Gap | Missing evidence, capability, instrumentation, verification, or authority that prevents a stated conclusion |
| Policy | An owner-approved rule allowing a particular decision under named conditions |

Strength is relative to the candidate set. One surviving row does not establish that all possible mechanisms were considered. A strong signal steers the next experiment. It does not create certainty by itself.

### The tower

| Layer | Owns | Interface to the next layer |
|---|---|---|
| 0. Running reality | User actions, deployment state, protocol events, resource use | Existing drivers and evidence sources |
| 1. Captures and facts | Identity, provenance, raw bytes, scoped measurements | Capture IDs, fact IDs, hashes, selectors |
| 2. Evidence contract | Controls, predictions, comparisons, applicable constraints | Contract IDs and a hypothesis-by-fact matrix |
| 3. Investigation protocol | Select, eliminate, repair hypotheses, experiment, assess parity | A bounded next action and an evidence state |
| 4. Skills and routes | Task routing, diagnosis versus repair, reviewer orchestration | `evidence-loop`, existing mode routes, `interrogate` |
| 5. Project verification | Real feature paths, collectors, baseline cases, regression gates | Maintained feature maps and executable contracts |
| 6. Infrastructure and policy | Default capture, access, resource budgets, approved decisions | Project commands and reviewed policy files |

The layers explain ownership, not a mandatory seven-stage tool chain. A CLI driver can capture behavior and evaluate its contract in one invocation. The shared helper hides the matrix and gate semantics behind one case assessment. Project drivers retain their deep, domain-specific behavior.

Stable joins are `case_id`, `feature_id`, `contract_id`, `capture_id`, `fact_id`, and `hypothesis_id`. Add none that a real join does not need. Reuse a verifier's existing run ID as `case_id` when that run already has adequate identity.

### Data and control flow

The build path is `feature intent -> contract -> baseline capture -> implementation -> candidate capture -> comparison -> verification result`. The incident path is `report -> scoped captures -> controls -> matrix -> discriminating experiment -> bounded diagnosis -> repair -> comparison`. Accretion connects them through `incident signal -> project contract or collector improvement -> next build and next incident`.

One coordinator owns mutable analysis and the next-action decision. Collectors append facts. Reviewers return objections in separate files or task results. They do not edit the ledger. A builder receives the confirmed mechanism, repair scope, and verification contract. It does not choose which original facts count.

The coordinator reads a compact generated view first, then follows exact capture pointers. Large data stays queryable in files, SQLite, or the existing telemetry system. Evidence reduction always retains the original capture reference and the command or query that produced the reduced result. An agent need not load gigabytes into its context to have a broad factual tier.

### Investigation protocol

1. Establish the target, intended behavior, scope, evidence availability, authority, and closure criterion
2. Ingest the existing report and captures before generating source-derived mechanisms
3. Select the cheapest valid control and compare existing measurements
4. Build the smallest useful candidate set with explicit predictions and complete matrix coverage
5. Select a discriminating experiment, or repair the hypothesis set if no row survives
6. If repairs do not help, gather the next useful layer of evidence and return to step 3
7. Map a surviving mechanism to the matching source or external component when evidence supports that attribution
8. Validate the mechanism, reproduction parity, and all remaining constraints
9. If repair is authorized, select and implement the smallest justified repair and run its unchanged contract
10. Close with the evidence state, remaining gaps, and a concrete accretion disposition

Step 5 repairs occur in this order: verify collection provenance, split bundled mechanisms, merge mechanisms whose scope is too narrow, combine complementary necessary causes, then generate a new fact-grounded mechanism. A tactic that does not apply gets a reason, not ceremonial execution.

Parallelize independent capture queries or review objections when the session permits delegation. Shared runtime driving remains serialized. Do not launch a worker for every hypothesis or observation. Read the existing runtime contract for capabilities and preserve outstanding task IDs in the existing checkpoint.

### Evidence states and stopping

| State | Required evidence | Permitted claim |
|---|---|---|
| `open` | Intake and at least one sourced observation | The case is being investigated |
| `consistent` | Every applicable constraint assessed, no contradiction, no unresolved required cell | This candidate fits the currently collected constraints |
| `mechanism-confirmed` | `consistent` plus a discriminating intervention or directly observed causal chain | This mechanism explains the failure within the recorded scope |
| `repair-verified` | Confirmed mechanism plus parity-valid failing-before and passing-after checks and nearby contract checks | This repair resolves the represented failure within the tested scope |
| `inconclusive` | Missing required evidence or unresolved alternatives | The specified claim remains unverified |

An investigation also records `outcome`: `diagnosis`, `external-attribution`, `repair`, or `unresolved`. A closed read-only diagnosis does not pretend to have verified a repair. The hang may reach confirmed attribution at the authentication completion boundary while the daemon's internal defect remains unknown.

The assessor checks that evidence requirements are present. It cannot determine causal truth from JSON labels. The coordinator must inspect the actual artifacts, and a falsifier must be able to challenge the cited causal interpretation.

Stop collection when the current signal supports a useful discriminating test. Stop experimentation when the authorized closure criterion is met. When a budget expires or required access is unavailable, return `inconclusive` with the narrow missing observation and next action. A budget ending is never a diagnosis.

## 3. Skill and playbook inventory

All new public content lives in `~/projects/skills/authoring/`. Package metadata uses double-quoted strings, `kind: "dev"`, and no invocation-disabling settings. Keep the helper root below 150 lines and each route below 120 where practical. Load the matrix, reproduction, and build references only on their matching branches.

### The one new skill

| Field | Design |
|---|---|
| Name and location | `evidence-loop`, `authoring/poteto/evidence-loop/SKILL.md` |
| Description | `"Use when diagnosing a reported defect from runtime evidence, evaluating whether a reproduction matches an incident, or comparing observed behavior against a verification contract."` |
| Metadata | `kind: "dev"`, `role: "helper"` |
| Purpose | Constrain behavioral claims using sourced observations and choose the cheapest useful next test |
| Inputs | User question, case directory, report or captures, project verification skill, optional feature contract, session authority |
| Outputs | Matrix, next action, evidence state, parity result, cited bounded diagnosis or comparison result |
| Reads and writes | Reads captures, contracts, facts, and policy; coordinator writes analysis; trusted importers append facts; assessor writes derived views |
| Calls | Project `verify-<app>` for known drivers and measurements, `how` after narrowing, `why` for matched regression history, `interrogate` evidence branch when independent falsification is warranted, prove-it-works at closure |
| Called by | Bug-fix, perf-issue, runtime-forensics, trace-forensics, debuggability, project verification skills, and evidence review |

It earns a new skill because the same reasoning contract serves several routes and project-local verifiers. Putting it in `bug-fix` would force diagnosis-only callers to load repair and PR instructions. Putting it in `interrogate` would make fact collection depend on review fan-out. Making it a standalone mode would duplicate task orchestration.

Supporting files are `references/case-contract.md`, `references/matrix.md`, `references/reproduction.md`, and `references/signal-contract.md`, plus `scripts/evidence.py` and `evals/`. Each root pointer states when to read its target. The schema lives with the contract reference and its validator, not in every caller. No separate fact-ledger or hypothesis skill is needed.

### New and revised routes

The descriptions below are proposed route frontmatter strings. Existing roots retain their task identity. These changes do not turn read-only requests into implementation requests.

| Route and location | Trigger description | Purpose | Inputs and outputs | Artifacts and composition |
|---|---|---|---|---|
| New `poteto-mode/playbooks/debuggability.md` | `"Use when planning how a new feature will be verified, instrumenting it for future diagnosis, or converting incident evidence into project verification controls."` | Make each changed behavior observable and refutable before implementation | Feature intent or incident lessons in; executed signal contract or a named gap out | Writes project verification contract and feature-map pointer; calls evidence-loop, create-verification-skill when establishing a verifier, existing verify skill, maintain-verification-skill for later audits |
| Revised `poteto-mode/playbooks/bug-fix.md` | `"Use when asked to diagnose and repair a reported defect with runtime evidence."` | Own repair after evidence-based diagnosis | Report, authority, captures in; verified repair or explicit unresolved diagnosis out | Calls evidence-loop for intake through mechanism confirmation, then existing architect, builder, tdd, blast-radius, and prove-it-works as applicable; owns repair analysis and decision trail |
| Revised `poteto-mode/playbooks/runtime-forensics.md` | `"Use when asked to diagnose a live runtime symptom from instrumentation without implementing a repair."` | Acquire and explain authorized live evidence | Target, current symptoms, tool access in; capture bundle and bounded diagnosis out | Capture specialist within evidence-loop; writes captures through collectors and analysis through the coordinator; calls the project driver |
| Revised `poteto-mode/playbooks/trace-forensics.md` | `"Use when asked to diagnose a captured profile, trace, heap snapshot, or system diagnostic bundle."` | Analyze preserved evidence without requiring a live reproduction | Captures and optional paired case in; sourced diagnosis or missing-evidence request out | Imports captures, adds exact queries and extraction receipts, calls evidence-loop; source attribution is optional when source is unavailable |
| Revised `poteto-mode/playbooks/perf-issue.md` | `"Use when asked to explain and fix a measured performance regression against a comparable baseline."` | Repair measured slowness under a frozen comparison | Complaint, baseline, captures in; signal-valid performance repair out | Calls evidence-loop before using existing strategy families, then project verifier and blast-radius; writes comparison results |
| Revised `poteto-mode/playbooks/feature.md` | `"Use when building new or changed behavior from a named data shape and a verification contract."` | Implement a feature whose checks already exist | Intent and design in; implementation plus demonstrated contract out | Calls debuggability before builder, project verifier after builder, evidence-loop when a comparison fails |
| New branch in `interrogate/SKILL.md`, reference `interrogate/references/evidence-review.md` | Root description becomes `"Use when asked for an adversarial or multi-model review of code, a plan, or an evidence-based diagnosis, or when an investigation calls for falsifying a control, signal, or hypothesis."` | Eliminate unsupported investigative claims | Sealed evidence snapshot, stage, matrix, proposed claim in; cited contradictions, provenance concerns, and coverage limits out | Calls evidence-loop's schema and assessor; reads artifacts only; emits separate reviewer result; existing code-review branch remains |

`debuggability` remains a route because Pascal already has a development router and an explicitly invoked verification generator. It owns the planning and promotion decisions, not a second driver or second feature map. The mode adds this route and a pointer from Feature. A direct call from another skill explicitly loads the route. Runtime requests can reach the model-invoked helper without remembering the mode name.

The existing `investigation`, `hillclimb`, `create-verification-skill`, `maintain-verification-skill`, and three `verify-*` skills are consumers, not new workflow owners. Their precise dispositions appear in section 7.

### Evidence review behavior

At the discovery stage, challenge the control, the observation's scope, and the claim that a difference is meaningful. At steering, challenge matrix cells, selectivity, hypothesis repairs, and the collection pivot. At validation, find a contradictory observation, a mismatched repro, or a redundant cause.

The evidence branch defaults to one separate falsifier for a substantial case, invoked at these checkpoints as needed. Give it the source artifacts and stage question before the coordinator's preferred narrative. It receives a consistent snapshot and exact IDs, not a selectively favorable summary. It can read matching source after examining observations. It can request missing evidence, but it cannot certify that no unknown constraint exists.

A new review round includes the original case brief, current snapshot, previous objections, responses, and unresolved objections. Use the runtime's delegated-task mechanism and retain each task ID. Under T3 orchestration, each round is a fresh delegated task, not a new top-level thread or a message to a backing child thread. This transport rule stays in the existing runtime reference.

The four-reviewer default remains for explicitly requested broad code or multi-model review. Increase evidence reviewers only for a material disputed interpretation or requested model diversity. Count concrete refutations, not votes. When delegation is prohibited or unavailable, perform the logical checks sequentially and record that independent review did not occur.

## 4. Artifacts and ownership

### Storage and source of truth

Use a task-owned case directory in the project's existing evidence root, or `.audit/cases/<case-id>/` when the project has none. Keep sensitive incident material out of git by default. A project verifier that already preserves evidence keeps its current location and manifest; the case references it instead of copying its entire schema.

```text
<case-dir>/
  case.json          target, authority, capture references, contract references
  facts.jsonl        immutable observations appended by trusted importers
  analysis.json      hypotheses, matrix, experiments, repros, gaps, next action
  decisions.tsv      existing show-me-your-work format, when a trail is needed
  view.md            generated compact view, never an additional source
  raw/               preserved captures, or references to retained verifier bundles
```

Use one case across diagnosis and repair. Do not open a second case merely because another skill takes control. Reuse the existing decision trail for significant forks. The matrix records reasoning state; the trail records decisions. Neither repeats the other's prose.

| Artifact or field | Writer | Permitted change |
|---|---|---|
| `case.json` target and closure criterion | Coordinator using the user's task | Establish at intake; scope changes require a logged reason and invalidate dependent comparisons |
| Authority receipt | Host or human-approved project policy | Coordinator references it; an agent-created declaration never grants access |
| Raw captures and imported facts | Source system, tool runner, deterministic importer | Append new observations; preserve original bytes and IDs |
| Fact correction record | Source owner or trusted recollection tool | Append a correction with provenance and the superseded ID |
| Hypotheses, matrix, control proposal, next action | One coordinator | Edit current reasoning; log material reversals |
| Reviewer result | Separate read-only reviewer | Return objections in its own result; coordinator adjudicates |
| Contract behavior and expected relationships | Feature owner, reviewed with the implementation | Version deliberately; a failed candidate never silently changes its own expected result |
| Contract measurements and baseline receipts | Project verifier or collector | Append immutable run-specific results |
| Policy | Pascal or the designated accountable owner | Approve applicability, action limits, and expiration or review conditions |
| `view.md` | Assessor | Regenerate from canonical files |

Facts are immutable to the reasoning agent. A fact from a user report means the user reported a value or event. It does not magically make that value an objective measurement. A debugger's interpretation of a stack frame is a hypothesis unless an independently defined extractor establishes the observation.

Capture provenance can be challenged without changing the captured bytes. A wrong-host observation remains a real observation from the wrong host. It cannot constrain the target instance once a sourced identity correction establishes that mismatch. The original record remains visible. The coordinator cannot exclude it merely because it contradicts a preferred mechanism.

Filesystem permissions and hashes are useful but do not prove semantic correctness or prevent an unrestricted agent from tampering. Version one promises auditable immutability. If stronger isolation becomes necessary, collection and sealing move behind a host-owned process with separate write authority. Do not advertise a Markdown rule as a security boundary.

### Case manifest

This is an illustrative instance of `evidence-case/v1`. Paths within a retained bundle are relative. Endpoint names below are fictional.

```json
{
	"schema": "evidence-case/v1",
	"case_id": "latency-001",
	"question": "Why does enabling mTLS raise tail latency?",
	"requested_outcome": "diagnosis",
	"target": {
		"feature_id": "remote-storage.mtls",
		"environment": "production-evidence-export",
		"time_window": ["2026-10-10T10:00:00Z", "2026-10-10T10:20:00Z"],
		"build": "captured-build-id",
		"config_capture": "C01"
	},
	"authority": {
		"receipt": "provided-artifacts-only",
		"permitted": ["read-provided-artifacts", "write-case-analysis"],
		"production_collection": false
	},
	"closure": {
		"claim": "Identify a discriminating, sourced mechanism within the exported evidence",
		"required_state": "mechanism-confirmed"
	},
	"contracts": [
		{
			"id": "remote-storage.mtls/v1",
			"path": "../../verify-app/contracts/remote-storage-mtls.json",
			"sha256": "contract-content-hash"
		}
	],
	"captures": [
		{
			"id": "C01",
			"path": "raw/deployment.json",
			"sha256": "capture-content-hash",
			"source": "provided deployment export",
			"subject": "client-and-server-sample",
			"observed_at": "2026-10-10T10:12:00Z",
			"collector": {"name": "deployment-export", "version": "recorded-version"},
			"query": "recorded read-only export query",
			"limitations": ["Export covers one deployment sample"]
		}
	]
}
```

Real hashes are 64 hexadecimal characters. A real source identity is a build digest or a recorded unknown, not the illustrative strings above. Identity fields may be `null` only with a gap recording why they are unavailable and which claims that blocks. Avoid representing an unavailable value as a fabricated fact.

### Fact ledger

Each line is one `evidence-fact/v1` record. The examples use two records to show a contrast. Their extractor must point to the recorded source location in a real run.

```json
{
	"schema": "evidence-fact/v1",
	"id": "F01",
	"case_id": "latency-001",
	"capture_id": "C01",
	"source_kind": "measurement",
	"selector": "/samples/control/discovery/address_count",
	"subject": "control",
	"signal_id": "discovery.address-count",
	"value": 5,
	"unit": "addresses",
	"extractor": {"name": "deployment-observations", "version": "1"},
	"scope": {"feature_flag": false, "topology_id": "topology-A"},
	"supersedes": null
}
```

```json
{
	"schema": "evidence-fact/v1",
	"id": "F02",
	"case_id": "latency-001",
	"capture_id": "C01",
	"source_kind": "measurement",
	"selector": "/samples/variable/discovery/address_count",
	"subject": "variable",
	"signal_id": "discovery.address-count",
	"value": 400,
	"unit": "addresses",
	"extractor": {"name": "deployment-observations", "version": "1"},
	"scope": {"feature_flag": true, "topology_id": "topology-A"},
	"supersedes": null
}
```

Required fields are schema, IDs, capture selector, source kind, subject, observation, unit when numeric, and scope. Additional provenance belongs in the capture receipt. `source_kind` is `measurement`, `reported`, or `configuration`. A reported observation points to the report's line or field. A configuration observation identifies the effective instance, not merely a source default.

An agent may author an extraction query, but the query's output and execution receipt enter the ledger through a tool. If an extraction requires uncertain semantic interpretation, record the captured text as the fact and put the interpretation in analysis. Reproduce an important extraction with an independent query or source owner when its correctness determines the diagnosis.

Every fact gets a scope disposition in analysis: `constraint`, `context`, or `scope-mismatch`. `context` means the proposed claim makes no causal prediction about that observation, with a written reason. An independent reviewer challenges these dispositions. All in-scope diagnostic facts, including unchanged signals, are constraints. A `scope-mismatch` needs a cited identity or timing discrepancy. This avoids both cherry-picking and the impossible demand to explain every unrelated byte of a system diagnostic archive.

### Mutable analysis

This example shows the working shape, not a completed diagnosis.

```json
{
	"schema": "evidence-analysis/v1",
	"case_id": "latency-001",
	"revision": 1,
	"state": "open",
	"controls": [
		{
			"id": "control-flag-off",
			"kind": "successful",
			"fact_ids": ["F01"],
			"variable_fact_ids": ["F02"],
			"intended_difference": "mTLS enabled",
			"confounders": ["Need to verify workload and shard ownership match"],
			"same_defect_check": "Compare routing behavior to the established contract",
			"validity": "unresolved"
		}
	],
	"fact_dispositions": [
		{"fact_id": "F01", "disposition": "constraint", "reason": "Control discovery cardinality"},
		{"fact_id": "F02", "disposition": "constraint", "reason": "Variable discovery cardinality"}
	],
	"hypotheses": [
		{
			"id": "H01",
			"claim": "The enabled path uses cluster-wide rather than shard-scoped discovery",
			"components": [],
			"origin_fact_ids": ["F01", "F02"],
			"status": "active",
			"predictions": [
				{"signal_id": "discovery.address-count", "outcome": "Variable includes endpoints outside the owning shard"}
			]
		}
	],
	"matrix": [
		{"hypothesis_id": "H01", "fact_id": "F01", "relation": "consistent", "evidence_ids": ["F01"], "reason": "Small control set is compatible with shard-scoped discovery"},
		{"hypothesis_id": "H01", "fact_id": "F02", "relation": "unknown", "evidence_ids": ["F02"], "reason": "Cardinality alone does not establish endpoint ownership"}
	],
	"experiments": [
		{
			"id": "E01",
			"hypothesis_ids": ["H01"],
			"procedure": "Compare discovered endpoints with recorded shard ownership",
			"predictions": {"H01": "Variable endpoints span multiple shards while the control follows owning-shard discovery"},
			"scope": "provided captures",
			"cost": "one local extraction and join",
			"status": "planned",
			"result_fact_ids": []
		}
	],
	"reproductions": [],
	"gaps": [
		{"id": "G01", "kind": "evidence", "missing": "Endpoint ownership and matched workload identity", "blocks": ["control validity", "mechanism confirmation"], "next_action": "Read the provided ownership and workload exports"}
	],
	"next_action": {"kind": "collect", "target": "G01", "reason": "Distinguish topology and workload confounders before a source explanation"},
	"reviews": [],
	"accretion": []
}
```

`relation` is `explains`, `consistent`, `contradicts`, or `unknown`. `explains` cites a mechanism or experiment that accounts for the observation. `consistent` says the observation does not conflict with the hypothesis. Neither value means proof. Missing cells behave as `unknown`. There is no neutral checkmark that quietly means both explanation and compatibility.

Hypothesis status is `active`, `eliminated`, or `selected`. Control validity is `unresolved`, `valid`, or `invalid`. Experiment status is `planned`, `running`, `completed`, or `cancelled`. Selecting a hypothesis does not advance the case's evidence state. A completed experiment must reference its observed facts, including an unsuccessful outcome.

Each active or selected hypothesis must have one cell per active constraint, with evidence IDs and a reason. A `contradicts` cell eliminates the exact hypothesis unless a sourced correction changes the fact's applicability. An `unknown` cell keeps the claim unverified. A combined hypothesis references its component IDs and records which observation loses its explanation when each component is removed.

The assessor computes matrix column counts among non-eliminated candidates and unresolved cells. It never asks the agent to count by hand. A column that only one current candidate explains is promising, but unknown cells in rivals must remain visible. If no row survives, it identifies the contradictions and sends the coordinator to hypothesis repair. The assessor does not invent missing mechanisms or choose a causal interpretation.

A compact rendered matrix looks like this:

| Candidate | P99 increase | DNS 5 versus 400 | Similar handshake | Cert loading per session | Conclusion |
|---|---|---|---|---|---|
| Per-RPC certificate work | Consistent | Unknown | Consistent | Contradicts if traced at the claimed component | Eliminate only within the trace's actual scope |
| Server capacity shortage | Consistent | Unknown | Consistent | Consistent | Seek discriminating evidence |
| Client discovery bypasses shard routing | Explains after endpoint and routing comparison | Explains | Consistent | Consistent | Confirm with causal comparison |

This example deliberately avoids declaring that a client certificate trace automatically disproves a server-only mechanism. The claim's component, build, and time window must match the trace.

### Reproduction and parity record

Store this object inside `analysis.json.reproductions`. A reproduction's captured observations are facts about the test environment. Its claimed equivalence to production remains a hypothesis.

```json
{
	"id": "R01",
	"procedure": "existing-verifier-command",
	"environment": "isolated-local-test",
	"capture_ids": ["repro-capture-01"],
	"signal_parity": [
		{"signal_id": "protocol.packet-sequence", "incident_fact_ids": ["incident-packets"], "repro_fact_ids": ["repro-packets"], "verdict": "failed"},
		{"signal_id": "auth.outstanding-reply", "incident_fact_ids": ["incident-reply"], "repro_fact_ids": ["repro-reply"], "verdict": "failed"}
	],
	"constraint_check": "failed",
	"equivalence": "different-bug",
	"disposition": "Keep the clock-skew defect separate from the reported hang"
}
```

Parity verdicts are `passed`, `failed`, or `unmet`. `unmet` prevents incident equivalence. The parity test compares meaningful relationships, not arbitrary byte equality. Contract normalization may remove declared volatile fields while preserving sequencing, identity, and the feature's causal signals. Every excluded field has a reason. A normalizer that strips the defect's signal fails its sensitivity check.

### Durable project verification contract

Put contracts inside the existing project verification skill at `<verify-skill>/contracts/<feature-id>.json`. This keeps maintenance within `maintain-verification-skill`'s authorized directory. Add a pointer under the existing feature page's `Driving it with <harness>` section. Retain the existing four H2 sections and user-oriented map.

The map owns how to reach the feature. The contract owns its observable invariants, controls, signal comparisons, and sensitivity proof. The project's driver owns executable collector and checker commands. If a driver registry already owns this data, use its registry as the canonical contract and export a view. Do not hand-maintain a second registry merely to match the filename convention.

```json
{
	"schema": "verification-contract/v1",
	"id": "remote-storage.mtls/v1",
	"feature_id": "remote-storage.mtls",
	"behavior": "Secure requests retain correct shard routing",
	"owner_boundary": "client-to-sharded-service",
	"drive_ref": "features/remote-storage-mtls.md",
	"workload_dimensions": ["shards", "replicas", "request distribution", "certificate state"],
	"signals": [
		{
			"id": "routing.owner-match",
			"meaning": "Whether each request reaches a valid replica of its owning shard",
			"unit": "boolean",
			"collect_ref": "project verifier routing observation command",
			"capture_mode": "verification-and-bounded-runtime-sample"
		},
		{
			"id": "discovery.address-count",
			"meaning": "Candidate endpoints used for the selected shard under the recorded topology",
			"unit": "addresses",
			"collect_ref": "project verifier discovery observation command",
			"capture_mode": "verification-and-bounded-runtime-sample"
		}
	],
	"controls": [
		{
			"id": "established-shard-routing",
			"kind": "successful",
			"drive_ref": "existing feature-disabled route",
			"matched_dimensions": ["topology", "workload", "dependency versions"],
			"expected_difference": "transport authentication mode"
		}
	],
	"checks": [
		{
			"id": "routing-preserved",
			"signal_ids": ["routing.owner-match", "discovery.address-count"],
			"relation": "topology-aware-routing-equivalence",
			"check_ref": "project verifier routing comparison command",
			"expected_basis": "shard ownership and valid replica membership",
			"sensitivity": {
				"fault": "Use cluster-wide discovery for a shard-specific request",
				"procedure_ref": "isolated negative-control scenario",
				"evidence_ref": "retained red-run receipt"
			}
		}
	],
	"collection_limits": {
		"default": "existing verification runs",
		"runtime_policy_ref": null,
		"limitations": ["Runtime sampling requires an approved project policy"]
	},
	"incident_refs": ["sanitized-latency-case-summary"]
}
```

The schema's required core is ID, behavior, owning boundary, driver reference, signals, comparison, control or justified control gap, and sensitivity evidence or an unmet sensitivity gate. Runtime sampling fields apply only to projects that have that infrastructure. Stable signal IDs preserve their meaning across versions. A changed meaning requires a new contract version and baseline compatibility check.

For intentionally changed behavior, declare the new expected relationship before measurement. Parity applies to unchanged invariants. Expected changes get direct behavioral checks and protected neighboring invariants. An old baseline is not a universal product specification.

### Access, budget, and policy records

Prefer existing project policy mechanisms. Where none exists, use one project-owned file linked from the verification skill. Public skills hold only the schema and sanitized examples. Real hosts, credentials, customer captures, and project-specific authority stay in the project or private lifecycle records.

A collection policy names target environments, allowed data sources, read operations, time and query limits, sampling and retention bounds, scrubbing, audit sink, and permitted instrumentation. A decision policy names its owner, matching conditions, evidence required, allowed action, limits, and invalidation conditions. Tool credentials remain in the existing host credential mechanism.

A policy record is authoritative only if its owner and the session recognize it. Merely finding a file that says `rollback_allowed: true` does not authorize a rollback. Pascal's standing rule requires explicit authorization before touching production, live databases, or daily-driver channels. This design does not override that rule. Exported evidence permits analysis of the export; it does not permit new production collection.

### The smallest useful script

Ship one helper script, `evidence-loop/scripts/evidence.py`, with three subcommands. These commands are proposed interfaces, not commands available today.

| Command | Inputs | Behavior and writes |
|---|---|---|
| `import --case DIR --receipt FILE` | Existing capture and its receipt, optional deterministic fact extraction | Validate receipt, hash and preserve the capture, append sourced fact records idempotently; write only inside the case |
| `assess --case DIR --require STATE` | Manifest, facts, analysis, referenced contract and verification results | Validate identity and hashes, require matrix coverage and cited gate evidence, compute counts, write `view.md` and assessment result; fail when the required state is unmet |
| `compare --contract FILE --control FILE --variable FILE --output FILE` | Contract and normalized observation records from the real verifier | Invoke or read the registered project comparison, retain expected and observed values, return passed, failed, or unmet checks |

No subcommand discovers credentials, edits product code, launches production probes, deploys, or silently repairs the ledger. `compare` uses registered project checks, not arbitrary shell strings generated during diagnosis. Collection stays with existing tools. A project-specific extractor is added only when a real capture needs one.

Examples use placeholder paths to describe the future interface:

```text
uv run <evidence-loop>/scripts/evidence.py import --case <case-dir> --receipt <capture-receipt>
uv run <evidence-loop>/scripts/evidence.py assess --case <case-dir> --require consistent
uv run <evidence-loop>/scripts/evidence.py compare --contract <contract-file> --control <control-observations> --variable <candidate-observations> --output <comparison-result>
uv run <evidence-loop>/scripts/evidence.py assess --case <case-dir> --require repair-verified
uv run <evidence-loop>/scripts/evidence.py --help
```

Require `uv` and a supported local Python, with the project's install and availability checks documented before use. Use the existing script conventions and one-line JSON output rule. A content command returns `file` or `files`. A state-changing import returns `changes`. An unmet gate fails with a concrete recovery instruction, such as collecting the missing observation or fixing the cited analysis record. It does not emit a success with a warning.

Exit codes are 0 for the requested operation and gate passing, 1 for a failed or unmet gate or invalid retained evidence, 2 for usage errors, 75 for a retryable lock conflict, and 130 for interruption. `--help` and `--version` print text. No quiet-success mode, interactive prompts, global configuration, or environment-dependent output format is needed. Flags and input files are the complete configuration. Import supports `--dry-run`; assessment and comparison remain safe to rerun. Same capture identity and hash produce no duplicate facts. A differing hash under an existing ID fails. Case writes are atomic and single-writer, and interruption preserves already sealed captures.

Version one implements import and assessment first. Comparison initially references the existing verifier's result. Add the comparison adapter only after two consumers demonstrate a genuinely shared input shape. Hash and schema checks establish record integrity, not diagnosis correctness.

## 5. Goal 1: build a feature with verification hooks

Walkthrough: add mTLS support to a remote-storage client while preserving shard routing. This illustrates the method without proposing changes to an actual storage repository.

| Step | Agent action and skill | Artifact | Completion criterion |
|---|---|---|---|
| 1 | Feature reads intent and uses `how` to understand the affected system and its real user paths | Existing feature map and focused source model | Name intended changed behavior and unchanged routing invariant |
| 2 | Debuggability route examines the existing verifier and deployment constraints | Proposed feature contract | Name topology, scale, flag combinations, certificate lifecycle, and unsupported verification conditions |
| 3 | Debuggability selects controls and measurements before builder work | Contract with control, signals, checks | A request's shard ownership and discovered endpoint membership can be observed externally |
| 4 | Existing verify skill drives established behavior and captures a baseline | Retained baseline bundle and facts | Doctor confirms build and topology; baseline meets the current contract |
| 5 | Debuggability proves the proposed check's sensitivity in an isolated case | Negative-control receipt | Deliberately bypassing shard selection makes the routing comparison fail while basic request success can still pass |
| 6 | `architect` plans the implementation and the cheapest justified instrumentation | Design and contract references | Signals have an owning boundary and a bounded capture cost; implementation can expose them |
| 7 | Feature implements one verifiable unit at a time | Product diff and any necessary collector change | Each unit passes its own check before the next unit starts |
| 8 | Existing verify skill drives flag combinations and realistic workload dimensions | Candidate bundle and normalized observations | Drive the actual client path; observe routing and certificate behavior, not only constructor names |
| 9 | Evidence-loop compares baseline and candidate under the frozen contract | Comparison result | Unchanged routing relationships hold and intentionally changed transport behavior passes its own checks |
| 10 | `interrogate` evidence branch challenges the control and assertions when stakes warrant it; code-review-mode applies its test authoring gate | Reviewer result and sensitivity evidence | No unresolved refutation and no behavior-proxy test masquerading as a routing check |
| 11 | Prove-it-works follows the actual path and verifies retained evidence after cleanup | Final verifier result | Artifact identity matches the final diff and proof survives teardown |
| 12 | Feature delivers within the authorized PR flow and records remaining observability gaps | Feature-map pointer, contract, bounded follow-up | The next agent can run the check without reconstructing the investigation |

Reuse an existing trace or diagnostic output when it already reveals the invariant. A feature adds a new hook only when existing measurements cannot catch a credible failure.

For a project without a verifier, explicitly call `create-verification-skill` if establishing it is within the requested work. Build and prove one feature path first. When the environment cannot support the needed proof, record an unmet gate and the minimal prerequisite rather than inventing a full local production stack.

A production-derived baseline helps select realistic constraints. It does not imply development may access production. Use provided exports or an already authorized isolated environment. If real production access would be necessary, present the concrete missing observation and the exact collection action for approval.

## 6. Goal 2: a bug arrives from production

Walkthrough: a user reports a container OOM after authentication failure, supplies the last good and first bad versions, defaults, a reproduction command, and a heap profile.

| Step | Agent action and skill | Artifact | Completion criterion |
|---|---|---|---|
| 1 | Bug-fix routes diagnosis to evidence-loop and preserves the user's report | Case manifest, original report | Target versions, configuration, requested repair, authority, and closure criterion recorded |
| 2 | Trace-forensics imports the heap profile and extracts the allocation or recursion observation | Capture receipt and fact ledger | The profile's subject and build match the report, or their uncertainty is explicit |
| 3 | Evidence-loop records the temporal, flag, credential, and heap constraints before source explanations | Fact ledger and analysis | Every important supplied constraint is represented, including amortization being off |
| 4 | Project verify skill executes the supplied reproduction in owned isolation when accessible | Reproduction capture | Observe the same recursive allocation signal; matching OOM symptoms alone are insufficient |
| 5 | Evidence-loop picks the old version as a control and records all configuration differences | Control record and comparison | Same invalid-credential path and workload, known version difference, valid control |
| 6 | Evidence-loop maps candidate mechanisms to all facts | Matrix | A long-standing recursion-only explanation fails the version constraint and an enabled-amortization explanation fails the effective-flag constraint |
| 7 | The coordinator applies hypothesis repair rather than starting a broad bisect | Revised hypotheses | Split the recent change into amortization and process-wide caching, then combine changed lifetime with the single-use state assumption |
| 8 | `how` examines only the matched cached-engine lifecycle and recursion path; `why` reads relevant change history | Sourced mechanism in analysis | Trace input, engine retention, exhausted state re-entry, and retained recursive frames in the correct versions |
| 9 | Project verifier runs a discriminating lifetime comparison or directly observes the causal chain | Experiment facts | The combined mechanism explains all constraints and each component's explanatory necessity is recorded |
| 10 | `interrogate` evidence branch seeks one contradiction or redundant cause | Reviewer result | No unresolved contradictory fact, unjustified exclusion, or parity mismatch |
| 11 | Bug-fix compares repairs and uses `blast-radius` to check their constraints | Repair decision | Distinguish removing cache reuse from making lifecycle re-entry valid; choose under existing requirements or surface a genuine product tradeoff |
| 12 | Builder implements the selected repair; `tdd` uses the cheap parity-valid regression check where practical | Failing-before and passing-after receipts | The original bounded test path stops accumulating recursive frames and returns the intended auth failure |
| 13 | Existing verify skill checks valid credentials, renewal, retry, and nearby lifecycle behavior | Final comparison and verifier bundle | Repair satisfies original and neighboring contracts on the appropriate surface |
| 14 | Debuggability turns the new lifetime observation into the owning feature's contract | Contract, collector improvement, gap disposition | The next build and investigation can detect reuse after exhaustion without repeated prompting |

If no reproduction is available, continue with preserved evidence and collect only what the session authorizes. A repair may remain unverified while external attribution is complete. Avoidable evidence retrieval is a tool gap. Choosing whether to sacrifice caching behavior is a product decision. These deserve different treatment.

The same intake works for latency or hangs. It chooses controls and layer transitions from the available observations, not from the bug label. The helper never interprets a production incident as blanket authorization to instrument a live host.

## 7. Accretion and changes to existing skills

### Close the loop without accumulating instructions

Each case records an `accretion` array in analysis. A row contains the originating fact or intervention, the gap category, the smallest corrective mechanism, its canonical destination, its owner, its status, and a verification receipt or concrete follow-up reference. Status is `applied`, `queued`, or `declined` with a reason. An infrastructure gap can remain queued without pretending the incident fix is unverified, provided the gap is not required for that fix's proof.

| What the run discovered | Where it lands | Who reads it next |
|---|---|---|
| A cheap, discriminating measurement | Existing project collector and contract | Feature verification and the next evidence-loop intake |
| A useful deep signal with repeated collection cost | Bounded application event, diagnostic command, or sampled capture | Normal verification and runtime collection |
| A trustworthy control | Project verifier fixture or baseline recipe with identity requirements | New comparisons and future bug intake |
| A parity-valid regression | One owning boundary's check and retained sensitivity receipt | The changed-path CI gate and project verifier |
| A code lifecycle invariant | Type, constructor ownership, or runtime invariant where it is enforced | Compiler, driver, and future builders |
| A repeated retrieval intervention | Tool adapter or read-only project command | Any agent that can discover the project verifier |
| A repeated decision with stable criteria | Narrow owner-approved project policy | Coordinator at the same decision fork |
| A reasoning failure | Sanitized skill eval fixture | Evaluation runner before skill changes ship |
| A one-off or expensive lesson | Existing task or private lifecycle record, with disposition | The next agent only when its trigger applies |

Prefer a type or lifecycle guarantee when it makes the wrong state impossible. Otherwise prefer a behavior check, diagnostic command, or collector over an additional paragraph telling the agent to remember. An isolated first incident may justify a check immediately if its risk is high; recurrence is not a mandatory wait condition.

A useful promotion test asks: did this new measurement distinguish a plausible wrong mechanism, how much did collection cost, and can it be exposed more cheaply without unacceptable overhead or sensitive data? Measure the collector before making it always-on. Keep sampling, retention, and access in project policy. Do not enable trace-level logging everywhere as a universal default.

Accretion is part of case closure, but it does not authorize unrelated infrastructure work, policy edits, publication, or production changes. Apply the bounded improvement already in scope. Otherwise record the exact follow-up. Do not append every incident to an always-loaded skill body.

Track elapsed time to a discriminating signal, failed candidate count, queries and data scanned, review cost, parity mismatches caught, and avoidable human interventions. Separately record human product decisions and authorization decisions. The aim is fewer avoidable interventions with at least equal diagnosis accuracy. Zero questions achieved by guessing is a failed run. Compare these measures within comparable incident classes rather than treating all bugs as equal.

### Active skill disposition and exact edit targets

Paths in this table are relative to `~/projects/skills/`. `Changed` means a proposed edit, not an edit performed for this design. `Reused as-is` means its responsibilities remain sufficient and callers supply the new context. `Superseded` names only the specific procedure being replaced.

| Existing skill or route | Disposition and file target | Reason and resolution |
|---|---|---|
| `poteto-mode` | Changed: `authoring/poteto/poteto-mode/SKILL.md` | Add Debuggability route and evidence-loop pointer; qualify the universal early-`how` rule so runtime diagnosis starts with observations |
| Bug fix | Changed: `authoring/poteto/poteto-mode/playbooks/bug-fix.md` | Supersede source-seeded binary search with evidence-loop intake and matrix; preserve repair ownership, smallest justified change, verification, and authorized PR flow |
| Runtime forensics | Changed: `authoring/poteto/poteto-mode/playbooks/runtime-forensics.md` | Add valid controls, all-constraint assessment, and scope receipts; replace unqualified live hotfix/CDP intervention with observational collection by default and explicitly authorized intervention |
| Trace forensics | Changed: `authoring/poteto/poteto-mode/playbooks/trace-forensics.md` | Use capture and fact references; permit confirmed external-component attribution without source, and allow narrower evidence requests when a fixed artifact cannot discriminate |
| Perf issue | Changed: `authoring/poteto/poteto-mode/playbooks/perf-issue.md` | Use evidence-loop control validity and selective signals before code-grounded strategies; preserve real measurement and before-and-after proof |
| Feature | Changed: `authoring/poteto/poteto-mode/playbooks/feature.md` | Insert Debuggability contract and baseline before builder work; final checks use that frozen contract |
| Investigation | Changed: `authoring/poteto/poteto-mode/playbooks/investigation.md` | Keep ordinary code questions on `how` and rationale questions on `why`; route read-only runtime-cause questions to evidence-loop without requiring a repair or PR |
| Hillclimb | Changed: `authoring/poteto/poteto-mode/playbooks/hillclimb.md` | Require signal-valid workload when starting from a user defect; reuse contract and control identity for measurements; preserve frozen harness and keep-or-revert discipline without a hypothesis matrix for every routine optimization |
| Fix root causes | Changed: `authoring/poteto/poteto-mode/principles/fix-root-causes.md` | Replace universal reproduce-first and open-ended repeated-why posture with evidence-grounded diagnosis and parity-validated reproduction; retain pattern search and smallest causal repair |
| Sequence verifiable units | Reused as-is: `authoring/poteto/poteto-mode/principles/sequence-verifiable-units.md` | Already owns per-unit verification and evidence-first delivery sequencing |
| Test behavior, not implementation | Changed: `authoring/poteto/poteto-mode/principles/test-behavior-not-implementation.md` | Clarify that externally observed protocol, routing, lifetime, and resource relationships can be behavior contracts; refer disputed structural-test retention to test-audit rather than categorical deletion |
| Agent runtime | Reused as-is: `authoring/poteto/poteto-mode/references/agent-runtime.md` | Already owns capability discovery, source authority, delegation IDs, checkpoints, fallbacks, and real-surface proof; no second runtime adapter |
| `interrogate` | Changed: `authoring/poteto/interrogate/SKILL.md` and new `references/evidence-review.md` | Add stage-specific evidence branch and bounded falsifier roster; consensus remains prioritization information rather than causal verification |
| Interrogate rubric | Changed: `authoring/poteto/interrogate/references/rubric.md` | Replace verification-by-reading wording with observation and parity questions; source analysis can find a risk but does not prove a production diagnosis |
| Interrogate reviewer prompt | Changed: `authoring/poteto/interrogate/references/reviewer-prompt.md` | Code branch retains execution review; evidence branch checks the proposed causal premise and refuses unsupported source-derived claims |
| Interrogate lead judgment | Changed: `authoring/poteto/interrogate/references/lead-judgment.md` | A lone cited contradiction outranks multi-reviewer agreement; a low finding count is no correctness proof |
| Prove it works | Changed: `authoring/poteto/principle-prove-it-works/SKILL.md` | Add one pointer requiring incident-signal parity when the claimed proof is a reproduction or bug repair; evidence-loop owns the details |
| Create verification skill | Changed: `authoring/poteto/create-verification-skill/SKILL.md` | Interview for important system invariants and available diagnostic signals; generate the smallest needed contract and execute its sensitivity check |
| Feature-map example | Changed: `authoring/poteto/create-verification-skill/references/feature-map-example/README.md` and matching example feature page | Add a contract pointer inside the existing Driving section without duplicating commands or altering four-H2 structure |
| Maintain verification skill | Changed: `authoring/poteto/maintain-verification-skill/SKILL.md` | Audit contract identity, baseline applicability, collector drift, and failure sensitivity alongside existing source and live coverage; keep product edits outside maintenance scope |
| `verify-skills` | Changed incrementally: `authoring/verify-loops/verify-skills/SKILL.md`, `features/discovery.md`, new contract or existing result adapter | Pilot a contract on actual discovery versus installed skill contents; retain owned test home, commands, and evidence; do not call fleet synchronization |
| `verify-transcript` | Changed incrementally: `authoring/verify-loops/verify-transcript/SKILL.md`, `features/diagnostics.md`, verifier's existing result adapter | Preserve the distinction between a correct doctor report and an unready machine; expose its existing observations through a contract, retaining paid selection and authorization |
| `verify-video-archive` | Changed incrementally: `authoring/verify-loops/verify-video-archive/SKILL.md`, `features/parallel-batch.md`, `references/evidence-schema.md`, existing verifier result adapter | Reuse its particularly strong run identity, resource observations, relocation hashes, source safety, and cleanup guarantees; add cross-run comparison only for a real regression |
| `how` | Reused as-is: `authoring/poteto/how/SKILL.md` | Still owns code behavior and placement explanations; callers move it after evidence in runtime diagnosis |
| `why` | Reused as-is: `authoring/poteto/why/SKILL.md` | Still owns historical rationale and calibrated inference; use a narrowed target and preserve unavailable-source gaps |
| `blast-radius` | Reused as-is: `authoring/poteto/blast-radius/SKILL.md` | Already demands execution evidence for safety claims and dependency inspection; receives the confirmed mechanism and contract |
| `figure-it-out` | Reused as-is: `authoring/poteto/figure-it-out/SKILL.md` | Already puts a real verification harness before ambitious implementation; its bespoke workflow may call Debuggability |
| `swarm` | Reused as-is: `authoring/poteto/swarm/SKILL.md` | Already owns permitted coverage partitions and gaps; supply disjoint capture or extraction tasks rather than hypothesis races |
| `arena` | Reused as-is: `authoring/poteto/arena/SKILL.md` | Useful for competing repair designs after diagnosis; its agreement concerns design selection, while its actual verification gate remains necessary |
| `show-me-your-work` | Changed: `authoring/poteto/show-me-your-work/SKILL.md` | Reuse its TSV; reconcile its append-only rule with audit instructions to edit or cut wrong rows by requiring superseding correction rows instead |
| `tdd` | Changed: `authoring/poteto/tdd/SKILL.md` | Before preserving a new repro as the original bug's regression, call evidence-loop parity; retain cheap-test discretion and no weak tests |
| Code review mode root | Reused as-is: `authoring/andy-devtools/code-review-mode/SKILL.md` | Continues to own test versus production versus architecture routing |
| Test audit | Changed: `authoring/andy-devtools/code-review-mode/playbooks/test-audit.md` | Add signal sensitivity and parity to its existing authoring gate; accept externally observed diagnostic contracts, preserve one primary owner, and reject cosmetic instrumentation tests |
| Thermo quality review | Reused as-is: `authoring/andy-devtools/code-review-mode/playbooks/thermo-quality-review.md` | Keeps new collectors and analysis helpers free of wrappers and unnecessary complexity |
| Architecture review | Reused as-is: `authoring/andy-devtools/code-review-mode/playbooks/architecture-review.md` | Reviews verified design friction after diagnosis; does not become a mandatory incident step |
| Grill for unknowns | Reused as-is: `authoring/matt/grill-for-unknowns/SKILL.md` | Useful for material missing planning constraints and product decisions; does not certify complete runtime evidence |

The exact example feature page is selected from the generator's current example directory during implementation. This design intentionally does not invent a filename for a file it has not inspected. All proposed result-adapter edits require reading the corresponding scripts before changing them.

### Conflicts that matter

1. Bug-fix currently seeds hypotheses with `how` and `why`; for runtime defects, collected observations must precede this source exploration
2. Bug-fix currently forces reproduction when direct reproduction fails; preserve attempts when useful, but a synthetic repro must pass incident parity and inaccessible intermittent incidents may proceed from preserved captures
3. Runtime-forensics currently offers live instrumentation injection or hotfixing despite a diagnosis-only framing; retain observational diagnosis and require actual authority for interventions, particularly on daily-driver or production surfaces
4. Trace-forensics currently requires source mapping for diagnosis; the hang shows that a confirmed dependency-boundary failure can be actionable without inaccessible implementation source
5. Interrogate's consensus language can be mistaken for verification; treat agreement as a review-priority signal and demand external behavioral evidence for a diagnosis or repair
6. A blanket reading of test-behavior-not-implementation rejects observations about calls; keep only independent external protocol, routing, timing, and lifecycle contracts, with observed outcomes and demonstrated failure sensitivity
7. The post's production-first ambitions conflict with unrestricted execution under Pascal's production rule; retain the ambition as a project capability requiring explicit authority, while provided exports and owned isolated runs work immediately
8. The post treats gathered facts as fixed constraints; preserve records but permit sourced corrections and scope mismatches, because instrumentation and reports can be wrong without authorizing the agent to rewrite inconvenient data
9. The post's broad-data preference can conflict with context and collection cost; retain broad queryable evidence with precise pointers and acquire deeper data only when it changes the next decision

### Archived skills: borrow ideas, keep packages archived

Paths below are under `~/projects/skills-private/skill_archived/jeffreys-skills/`. No archived package needs activation or promotion for this system.

| Package | Useful material | Decision |
|---|---|---|
| `gdb-for-debugging` | Batch debugger output, thread and process identity, wait-state inspection, detach discipline | Borrow into a project collector only when needed; reject automatic global ptrace relaxation and its excessive universal recipe |
| `multi-pass-bug-hunting` | Recheck interactions after a verified repair | Existing targeted checks cover it; reject random code exploration and clean-scan-as-proof for incident diagnosis |
| `profiling-software-performance` | Scenario fingerprints, comparable workloads, separate profiling from optimization, ranked artifacts | Borrow fingerprint fields and measurement separation; avoid universal run-count requirements and profiler preferences |
| `deadlock-finder-and-fixer` | Distinguish waits, contention, loops, and real deadlocks; require concrete reachable interleavings | Borrow the diagnostic questions when a wait signal points there; reject exhaustive hazard sweeps and fixed 10x stress as default incident scope |
| `multi-model-triangulation` | Report disagreements rather than conceal them | Existing interrogate is stronger; reject consensus-as-confidence and human copy-paste transport |
| `brenner` | Exclusion, prediction tables, discriminating experiments, assumption visibility | Borrow the method; reject minimum numbers of hypotheses, mandatory third alternatives, corpus coupling, Agent Mail, and a second research platform |
| `reality-check-for-project` | Compare actual delivered outcomes with intended goals | Prove-it-works already supplies the useful discipline; reject code-as-runtime-ground-truth and broad bead or ambition machinery |
| `testing-golden-artifacts` | Declared normalization and deliberate baseline updates | Borrow only when output stability warrants it; avoid freezing incidental diagnostic bytes |
| `testing-conformance-harnesses` | Independent specification-derived comparisons and explicit uncovered requirements | Borrow into a contract when the feature has a real external specification; reject percentage scores that disguise unmet mandatory requirements |
| `testing-real-service-e2e-no-mocks` | Real boundary execution, owned isolation, captured results | Reuse existing verification practices; avoid generic bans on useful external-boundary substitutes and blanket real-service test setup |
| `testing-metamorphic` | Property-preserving transformations and demonstrated mutation sensitivity | Borrow a relation when exact output lacks an oracle; reject universal kill-rate targets and forced property suites for a single bug |
| `testing-fuzzing` | Minimize useful failing inputs and keep discovered behavior checks | Defer until a feature has a justified fuzzing risk; reject blanket targets, throughput floors, and refactors performed solely for this system |

## 8. Evaluations from the three bugs

### Evaluation method

Create three staged local scenarios before writing extensive helper prose. Compare the current workflows with the proposed helper at identical repository and fixture revisions in fresh agent sessions. Use the existing `writing-for-agents` evaluation runner, its `evals/evals.json` format, and retained tool events, answer, and git log.

Fixtures are fictionalized reconstructions of the source's failure mechanisms. They include report text, effective configuration, version identity, traces, and small runnable programs or existing-shaped verifier outputs. They are not the author's production files. Keep hidden grading expectations separate from the agent-visible case. Correct root-cause names alone do not pass: grade what the agent actually inspected, measured, eliminated, and claimed.

Each scenario exposes ordinary evidence first and makes additional captures discoverable through neutral inventories. Include irrelevant observations and plausible wrong explanations. The agent must choose the useful query or control rather than receive a file named `root-cause.json`. No real production access, paid APIs, or fleet synchronization is required.

Hard failures across all scenarios are fabricated facts, silent exclusion of inconvenient constraints, an incident-equivalence claim despite failed parity, a claimed verified fix without real failing-before and passing-after evidence, or unauthorized mutation. Soft measures are time, token cost, useful captures, repeated extraction, and avoidable human intervention. Optimize those only after the hard behavioral gates pass.

### Latency regression

| Stage | Correct behavior | Failure |
|---|---|---|
| Intake | Record flag timing, both client and server P99 increases, effective topology, and the limits of pre-production scale | Infer a server defect directly from server P99 or assume smaller pre-production success establishes production parity |
| Control | Match feature-off and feature-on cases by workload and topology, accounting for unavoidable differences | Compare unmatched hosts without confounders or omit the control |
| Initial reasoning | Treat cert work, capacity, routing, and other plausible mechanisms as candidates with explicit predictions | Ship the first certificate-reload explanation or use reviewer agreement to confirm it |
| Discovery | See P99 as weak, collect appropriate cert timing and discovery data, preserve unchanged handshake timing | Repeat source review or stop at aggregate telemetry |
| Matrix | Represent approximately 5 versus 400 discovery addresses, inspect endpoint ownership, reject claims contradicted by matched component traces | Use client-only evidence to eliminate a server-only claim, or claim cardinality alone proves routing |
| Confirmation | Demonstrate that the enabled path bypasses shard selection and incurs cross-shard work through a matched comparison | Treat an all-compatible matrix row as sufficient causal proof |
| Repair | Select the sharded client at the actual owning path and prove restored routing with the unchanged contract | Add cert caching, broad retries, or unrelated server tuning |
| Accretion | Add a topology-aware routing or endpoint observation and show it detects the same mistake at smaller scale | Pin the class name or hard-code production's address count without semantic ownership checks |

Include an information-incomplete variant where only P99 is initially available. Passing means the agent asks for or discovers the discriminating capture, not that it guesses routing immediately. Include a misleading repeated error in both control and variable to verify that unchanged observations remain available but do not steer incorrectly.

### Memory leak

| Stage | Correct behavior | Failure |
|---|---|---|
| Intake | Extract first-bad and last-good versions, invalid-credential condition, effective amortization-off setting, and the plain-recursion heap observation | Ignore available reproduction or generate a source-only explanation |
| Reproduction | Run the supplied path in owned isolation and confirm the recursive allocation signal using a bounded observation before a huge OOM | Accept any growing RSS as incident parity or spend resources reproducing the full reported 50 GB allocation |
| Elimination | Reject amortization-enabled reasoning and an unchanged state machine as the complete temporal explanation | Conflate opt-in amortization with default-on caching or drop the heap-frame constraint |
| Hypothesis repair | Split the recent bundle into cache lifetime and amortization, then combine retained exhausted engine with single-use recursion behavior | Start a wide bisect or invent several unrelated mechanisms while the supplied constraints already narrow the issue |
| Confirmation | Observe changed engine lifetime, exhausted-state re-entry, and accumulating async recursion under the reported input | Explain only the new version or only the heap profile |
| Necessity | Identify the fact that each removed component leaves unexplained and test the relevant lifecycle difference | Add unnecessary causes to rescue a contradicted hypothesis |
| Repair selection | Preserve legitimate behavior and compare cache removal with valid lifecycle reuse under stated requirements | Bound retries as a cosmetic repair or invent product priorities |
| Verification and accretion | Prove the same input now returns the intended auth failure without frame growth, check legitimate auth paths, and enforce the lifetime invariant | Weaken the assertion, change flags to avoid the failing default path, or claim passing unit tests alone |

Add a provenance variant with a trace from the wrong build. The correct agent flags identity, retains the trace, obtains a corrected capture, and appends a correction. It must not silently edit the fact to make the combined mechanism fit.

### Intermittent hang

| Stage | Correct behavior | Failure |
|---|---|---|
| Intake | Accept a preserved diagnostics investigation with no reliable local reproduction and possibly inaccessible daemon source | Refuse all progress until it can force a repro or rebuild the whole desktop stack |
| Control | Use a well-understood explicit permission failure as a sad-path control and document its differences | Assume a happy-path local daemon is automatically the best control |
| Application evidence | Preserve timeouts and absent auth errors while checking log coverage and server timing | Conclude no authentication request occurred merely because logs are absent |
| Network evidence | Confirm handshake and WebSocket upgrade, observe keepalive-only traffic, and narrow to the post-upgrade path | Continue blaming server latency or packet loss contrary to the capture |
| Process and kernel evidence | Follow the unresolved wait toward IPC data and correlate the outstanding one-time reply right across affected reports | Interpret all waits as a lock cycle, or inspect kernel data without a scoped question |
| False reproduction | Reject a clock-skew token-rejection repro because packet sequence and outstanding reply signals differ | Accept similar VFS timeouts as parity |
| Attribution | Cite the evidence that the authentication daemon accepted a request without completing the reply and state the remaining internal uncertainty | Fabricate an internal daemon code defect or claim to have verified a fix |
| Closure and accretion | Produce an external-attribution packet and propose an outstanding-auth-request age/completion diagnostic | Send an escalation without authorization, patch the wrong client layer, or lose captures during cleanup |

The grader must accept external attribution as the correct completion for a diagnosis-only brief. It must reject a fake internal root cause. A synthetic hang introduced in an unrelated test library is a different bug even if its visible symptom matches.

### Additional shared probes

Use small deterministic probes for missing matrix cells, unknown cells treated as support, duplicate imports, altered capture bytes, snapshot changes after review, scope exclusions without provenance, interrupted import, and a baseline normalizer that removes the discriminating field. These are real integrity failures of the proposed artifact tooling, not tests that mirror its implementation.

Keep one variant with a deliberately incomplete hypothesis set. Correct behavior records residual uncertainty and obtains evidence or a discriminating experiment. Reporting one survivor as unique truth fails. Keep one variant with a perfectly valid control and a noisy aggregate metric, so the agent does not unnecessarily descend through every layer.

Do not claim evaluation improvement in this design. No baseline or proposed-system agent eval has been executed here. The baseline and retained behavior comparison are the first implementation unit.

## 9. Phased implementation plan

Build in independent, reviewable units from each repository's authorized worktree. This design requests no implementation, repository edits, commits, installs, or PRs.

| Phase | Smallest unit | Verification before advancing |
|---|---|---|
| 0 | Write the three fictionalized incident fixtures and expected tool behaviors; run current-workflow baselines | Retained events identify the actual failure modes and grading does not depend only on final prose |
| 1 | Add evidence-loop's vocabulary, case template, matrix relations, and intake steps; adapt bug-fix's early source and repro rules | Memory-leak scenario accounts for every supplied constraint and rejects the default-off explanation; latency refuses unsupported confirmation |
| 2 | Add import and assessment commands with capture identity, hashes, missing-cell checks, derived matrix, and compact view | Integrity probes pass and an interrupted/resumed case uses the same evidence without duplicate ingestion |
| 3 | Add reproduction parity and interrogate's evidence branch; adapt runtime and trace forensics | Hang scenario rejects clock-skew equivalence, reaches bounded external attribution, and does not perform unauthorized intervention |
| 4 | Add Debuggability and one project verification contract using an existing verifier | Run one real public path, demonstrate a credible negative control, and preserve proof through cleanup |
| 5 | Adapt the verification generator and maintainer after the pilot establishes the smallest contract | A freshly generated feature contract can be executed, and maintenance detects an actual stale collector or inappropriate baseline |
| 6 | Connect the other existing verification examples only where their result shapes fit | Each adapter preserves its current authorization, readiness, platform, identity, and cleanup semantics |
| 7 | Improve the highest-value collector or structural guard from a real incident | Measure reduced collection effort and prove the added check catches its credible regression |
| 8 | Consider authorized sampled runtime capture or an isolated production-like slice in a named project | Show measurable discriminating value, bounded resource use, recognized authority, and retained audit evidence |

For public-skill changes, follow `writing-great-skills` and `writing-for-agents`, run the skill validator, the requested behavior evals, `just compile-skills`, `just remote-skills`, and the repository's required changed-path checks. Review source and generated output together. Installation and fleet synchronization remain separate authorized operations. No authoring happens in installed execution copies.

The first real pilot should be `verify-skills` because it has free, isolated public command paths and can prove discovery drift without paid or production access. Preserve `verify-video-archive`'s richer evidence pattern as a reference rather than rewriting its already useful manifest first. If Pascal chooses a different pilot, the shared helper design does not change.

### Defer or reject

| Idea | Decision |
|---|---|
| A generic data lake, vector index, hypothesis database, or knowledge graph | Reject until file-based cases fail a measured requirement |
| Separate skills for every investigation stage | Reject because stages share one reasoning contract |
| Universal telemetry connectors and cloud credential handling | Defer to a real project's missing source |
| Default multi-model fan-out at every stage | Reject as expensive repetition; use bounded falsification and requested diversity |
| Continuous trace collection on all hosts | Reject as a default; evaluate narrow sampling after observing value and cost |
| Automatic production access, rollbacks, deploys, or cross-team messages | Reject as implied capabilities; require actual session authority or recognized policy |
| A local replica of the entire production stack | Reject as the default verification strategy; use a small faithful boundary when it preserves the important signal |
| Mandatory fuzzing, formal methods, mutation percentages, or fixed stress multipliers | Defer to credible feature risks; sensitivity proof remains required without a universal technique |
| Perpetual scheduled maintenance | Defer until requested; no recurring job is created by capturing a lesson |
| Automatic global skill changes from an incident | Reject; propose a sanitized, evaluated source change in its own authorized worktree |
| New public stores of private customer captures | Reject; publish methods and synthetic fixtures, retain actual evidence under project authority |

## 10. Questions only Pascal can answer

1. Which project should receive the first real contract beyond the isolated `verify-skills` pilot? The recommended default is the project where debugging currently requires the most manual evidence retrieval
2. What operational access, if any, should future agents receive automatically under project policy? The recommended starting scope is provided exports and owned non-production instances, with each production collection action explicitly authorized
3. Who owns the acceptable runtime capture cost and retention limits for each project? A named project owner must set these before sampled production collection is implemented
4. Should incident accretion that exceeds the repair's scope be implemented in a separate follow-up or only recorded for prioritization? The recommended default is one concrete follow-up, with immediate bounded improvements only when already authorized
5. Who may approve durable policies for actions such as rollbacks or external escalations? The recommended default is Pascal or a designated accountable project owner, with no policy inferred from an agent's own decision log

None of these questions blocks the offline fixtures, shared evidence contract, or public verifier pilot. They gate project selection and future operational authority. This design stops at the requested artifact.
