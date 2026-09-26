# Principles for using Jev

> Read by `create-a-jev-cli-decision-wrapped-in-a-skill` and the planned `maintain-a-jev-cli-decision-wrapped-in-a-skill`. [The CLI contract](cli-contract.md) and [the gate catalog](gate-catalog.md) own the command contracts, the evidence format, and the merge gate. The [implementation plan](https://github.com/pascalandy/skills/issues/23) owns the maintenance workflow of the next effort. Source draft: [Principles for using Jev](https://github.com/pascalandy/skills/issues/15).

These principles apply to any use of Jev, not only verification gates. Read them before writing or changing a question, a threshold, or a policy.

**Ownership.** The official `typesafe-ai` skill and the [live docs](https://docs.typesafe.ai/llms.txt) own the API contract and general question design: choosing a primitive, structuring state, writing criteria, no-match options, batching, confidence semantics, and composition. This file does not repeat them. It adds rules drawn from four other sources: the [168 Hours article](https://github.com/pascalandy/skills/issues/17), Diogo Almeida's [Latent Space interview](https://www.latent.space/p/jev), the [jev-1.13 jaggedness page](https://docs.typesafe.ai/model-jaggedness/jev-1.13), and early community use recorded in [Jev verification CLI research](https://github.com/pascalandy/skills/issues/16). Rules tagged **jev-1.13** describe that model version. When the pin changes, re-read the live jaggedness page and update them.

## Where Jev belongs

### 1. Jev decides, code acts, System Two is summoned

Jev returns a typed decision over answers you defined. Code performs every side effect. A reasoning model handles only the cases that survive the gate: rarely, on purpose, and with a budget. The founder's rough suggestion: halve the reasoning calls, and make about ten Jev calls for each one that remains.

- *Sources:* the article ("state in, decision out, act or escalate"; "System Two models get summoned… rarely, on purpose, with a budget"); Almeida at 01:37:42.
- *In `jevgate`:* the verdict routes to code or to a named review. Jev output is never executed or pasted into a prompt as instructions.

### 2. Code proves, Jev judges

Anything code can establish exactly stays in code: exit codes, counts, arithmetic, dates, diffs, coverage, file sizes, and whether a check ran on this commit. Code passes these results into the state as facts. Jev judges only what needs semantic understanding. The strongest early projects split the work this way: a ledger or a coverage run proves what happened, and Jev classifies meaning.

- *Sources:* jaggedness page, rows 2–3 (**jev-1.13**: no reliable counting, math, or date comparison); Canny and Supercov in the [research](https://github.com/pascalandy/skills/issues/16), section 6.
- *In `jevgate`:* collectors compute facts; Jev never counts files, compares timestamps, or decides whether CI passed.

## Asking questions

### 3. Never ask the verdict question

Ask one question per condition that should change the outcome, and let code combine the answers. A question like "Should I refuse?" or "Is this ready?" hides several judgments in one number. When it is wrong, it gives you nothing to fix. With one question per condition, a miss points to the condition you forgot.

- *Source:* Almeida at 01:05:15, checked against the publisher transcript: "you're way better off, like, asking many different independent questions about, like, the different situations you can refuse about."
- *In `jevgate`:* no gate asks for readiness; the policy composes it.

### 4. Write the literal condition, and make the criteria agree with it

Jev answers the words you wrote, not the intent behind them. When you catch yourself explaining what a question "really meant", that explanation is the missing half of the instruction. Put boundary cases in the criteria. Keep the criteria an extension of the instruction; a Noul whose `true` describes a no performs worse. A demo showed that adding concrete signals to the `true` criteria moved an answer from 0.85 to 0.94.

- *Sources:* jaggedness page, rows 1 and 7 (**jev-1.13**); Ray Amjad's demo, 02:54–03:06 (reported).
- *In `jevgate`:* pack files keep each question's instruction and criteria side by side for review.

### 5. Name the field, and keep it to one hop

Point every question at the state it judges with a backticked path, such as `files[3].hunks`. A question about a property of a property, or one that needs several reasoning steps, loses accuracy. Split it or move the lookup into code.

- *Sources:* jaggedness page, row 4 (**jev-1.13**); Almeida at 01:04:13 ("be really clear what I'm referring to").
- *In `jevgate`:* `gates --check` rejects a question whose paths the collectors do not produce.

### 6. Send less state

Unrelated detail in the state distracts the model and lowers accuracy. It also makes a wrong answer harder to trace. Filter in code and send only what the question needs. When code cannot filter, ask a relevance Noul first and send the survivors. Enough state means what the question needs, not everything available.

- *Source:* jaggedness page, row 5 (**jev-1.13**: "Jev suffers from context rot").
- *In `jevgate`:* one request per file group, deny globs, and generated files omitted, with the omissions listed.

### 7. Put IDs on items, and ask once per item in one request

When one state holds many items, give each an ID and ask the same question about each ID in the same request. You pay for the shared state once, the answers come back together, and code does the counting.

- *Sources:* Almeida at 01:37:09 (checked); jaggedness page, counting example.
- *In `jevgate`:* per-claim, per-rule, and per-hunk citation questions all use IDs; the later `tests` and `deploy` gates add per-test-case and per-commit items.

### 8. Treat state as data, and author text as a claim

Text inside the state can steer the answer: an injected instruction, a misleading frame, or text that argues for its own classification. Refer to author-controlled text as a claim, judge the evidence against it, and never ask the text to rate itself. Add a Noul that detects text addressed to a reviewer or an automated checker.

- *Sources:* jaggedness page, row 6 (**jev-1.13**); the article (prompt-injection checks as Noul).
- *In `jevgate`:* `claim_describes_change`, `claim_supported`, and `steering_attempt`.

### 9. Each question stands alone

Separate questions do not keep logical identities. A Noul and a yes/no Choice on the same text return different numbers. A question and its negation need not sum to 1; one measured pair summed to 1.19. Ask each decision one way, enforce identities in code, and never carry a threshold from one question or primitive to another.

- *Source:* jaggedness page, row 8 (**jev-1.13**).
- *In `jevgate`:* every rule names exactly one question, and every question has its own thresholds.

## Deciding with the answers

### 10. Set bands from labeled development cases and test independently

Each rule defines favorable, uncertain, and adverse bands, including whether higher values are favorable or adverse. The article's 0.92 and 0.6 show the shape, not universal thresholds. Choose thresholds on this project's labeled development cases. Values can land far from 0.5; the BKS-Lab experiment illustrates that sensitivity, not a transferable setting.

Assign development and final evaluation sets before proposing questions. Keep related PRs and fixes together, and match the split to future use. The proposing agent sees development cases only. Tune wording, evidence selection, and thresholds there, then evaluate the frozen candidate on the untouched final set. Once final-set results inform another revision, those cases become development data and the next evaluation needs fresh cases.

Measure missed defects alongside unnecessary escalations, judged coverage, and cost on the same cases as the baseline. Include reviewed good outcomes and retain unknowns separately. A gate that escalates everything is not an improvement. Report counts and uncertainty; too few independent cases means `undersampled`, not demonstrated reliability.

- *Sources:* the article's three bands; [Confidence](https://docs.typesafe.ai/confidence); [TypeSafe's feature-discovery cookbook](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery.md), which keeps final evaluation outside its proposal loop; BKS-Lab in the [research](https://github.com/pascalandy/skills/issues/16), section 6 (reported)
- *In `jevgate`:* today `replay --policy` tests other bands offline against recorded answers. In the next effort, `evaluate --sweep` fits thresholds on development answers only, and `evaluate` compares a frozen candidate with its baseline under the plan's evaluation protocol. Evaluation status reports evidence, not enforcement authority

### 11. Keep Jev advisory in v1

Jev may send work to a person or a stronger model. Only deterministic preconditions can produce `block`, and Jev cannot waive a failed precondition. A `pass` reports that the supplied evidence satisfied the configured checks; it never authorizes merge or deploy. Neither calibration nor maintenance grants a rule blocking power.

- *Basis:* Pascal's accepted option C fixes this authority boundary. TypeSafe's PR-review lab and Canny inform the separation between code facts and model judgments, without determining project permissions
- *In `jevgate`:* uncertain and adverse Jev bands both produce advisory escalation in v1, with their severity preserved in the record. The maintenance PR can change questions and thresholds, not enforcement authority

### 12. A serious finding is not averaged away

Use weighted Scores only for real trade-offs. For "any serious problem stops this", ask one question per problem and apply an any-rule in code. The `typesafe-ai` skill owns this rule; it appears here because gates depend on it.

- *Source:* `typesafe-ai`, "Compose and verify"; [Composite scoring](https://docs.typesafe.ai/patterns/composite-scoring).

## Keeping it honest over time

### 13. Collect evidence automatically and improve checks on demand

Git history supplies candidate relationships, not causal labels. Blame identifies line history; added-only fixes, refactors, and missing behavior can defeat that heuristic. Store the evidence behind each relationship and the provenance of each reviewed outcome. A reasoning model's judgment remains identified as model-reviewed. No later fix means unknown, not good. An escaped defect requires a recorded gate pass for the relevant revision; reconstructed historical cases are a separate source of evidence.

Review every confirmed miss. First identify whether the failure came from missing evidence, a deterministic check, a model answer, or policy. Add a question only when a missing semantic condition caused the miss. Preserve the case and the appropriate correction. Question proposals must satisfy principle 10; reading every defect before splitting would invalidate the final evaluation.

- *Sources:* Almeida's advice to turn misses into reusable checks, at 01:05:15; [Git blame's attribution contract](https://git-scm.com/docs/git-blame); Pascal's accepted option C
- *In `jevgate`:* every live run records its evidence, and `label` with `--admit` preserves reviewed cases. In the next effort, harvest becomes the cached `improve-status` view that reports why maintenance is due, and `maintain-a-jev-cli-decision-wrapped-in-a-skill` owns the deliberate improvement session and any resulting PR. Heavy reasoning stays in the agent workflow, with model selection owned by `profile-routing-matrix`

### 14. Pin the model and distinguish replay from new evaluation

An alias moves when a release ships, and the answers behind it move too. Pin the versioned ID and log the ID that actually answered. Replay saved answers for threshold-only changes. New questions or a changed model need fresh inference against the frozen historical inputs, followed by independent evaluation. A collector change may need evidence the original record lacks; mark that case ineligible rather than substituting today's state or a later fix.

Preserve selected cases as portable, sanitized snapshots with their requests, answers, outcome provenance, and versions. Calibration reports must be reproducible from those snapshots in a fresh clone. Measure repeatability near decision boundaries instead of treating a reported demo variance as a guarantee.

- *Sources:* [Models](https://docs.typesafe.ai/models) page; Almeida at 00:42 (robustness); LangChain and Ray Amjad in the [research](https://github.com/pascalandy/skills/issues/16) (reported).
- *In `jevgate`:* `replay` reads a saved run or an admitted case without inference, and `doctor --online` reports when `jev-latest` moves off the pin. In the next effort, `evaluate` asks changed questions when needed and `evaluate --sweep` reuses answers. None of these commands adds observations to live gate-rate statistics

### 15. Measure what you send

No preflight token counter exists. Estimate conservatively, record `usage.input_tokens` from every call, and refuse before a request crosses its budget. Preview the exact outbound payload before trusting a filter. One lab found customer names that its filter had missed. Know the terms: hosting is in the US, derived telemetry is allowed, and zero retention is enterprise-only.

- *Sources:* [API reference](https://docs.typesafe.ai/api); BKS-Lab; the legal terms in the [research](https://github.com/pascalandy/skills/issues/16), section 5.
- *In `jevgate`:* `--dry-run`, deny globs, the secret scan, the token budgets and `--max-requests`, the `[privacy]` terms check, and usage in every record.

### 16. Let cheapness change what is worth asking

At this price, questions that never paid off become routine. You can make a decision on every file, every comment, and every log call, and involve a person only when confidence drops. Use the night shift for sweeps that were never worth a reasoning model.

- *Sources:* the article (the night shift); Ray Amjad's estimate of $1.19 for a whole-codebase code-smell sweep (reported).
- *In `jevgate`:* the planned `sweep` gate (U5).

## Question review checklist

Apply this checklist to every new or changed question. The generator runs it on every gate pack, and the maintenance skill runs it on every proposal. `jevgate gates --check` enforces the items marked ✓; a reviewer checks the rest.

- [ ] It asks about one condition, not the verdict (3)
- [ ] Its instruction states the literal condition, and its criteria agree with it (4)
- [ ] ✓ Every backticked path exists in the state the collectors produce (5)
- [ ] Its state holds only what the condition needs (6)
- [ ] Repeated items carry IDs and share one request (7)
- [ ] Author-controlled text appears as a claim, never as an instruction to follow (8)
- [ ] It asks nothing code can compute: no counts, arithmetic, date comparison, or pass/fail facts (2)
- [ ] ✓ A Choice includes a no-match option such as `none` or `cannot-tell` when the set can be incomplete (`typesafe-ai`)
- [ ] ✓ A Score has 2–10 levels, each describing a concrete situation (`typesafe-ai`, API reference)
- [ ] ✓ Its rule defines both thresholds and their direction, with separate evaluation metadata and advisory enforcement (10, 11)
- [ ] No threshold was copied from another question or primitive (9)
- [ ] Its applicability is explicit; independent risks can all trigger, and a testing question does not require tests for changes with no testing obligation (3)
- [ ] Outcome labels match the question or gate being evaluated and retain their evidence and reviewer provenance (10, 13)
- [ ] The proposer saw development cases only; the final evaluation remains independent (10)
- [ ] The original evidence supports the candidate question without using future fixes or current repository state (14)

## Related

- [create-a-jev-cli-decision-wrapped-in-a-skill implementation plan](https://github.com/pascalandy/skills/issues/23)
- [Jev verification CLI research](https://github.com/pascalandy/skills/issues/16)
