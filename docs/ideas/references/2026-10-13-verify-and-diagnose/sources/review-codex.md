# Eliminator review of design.md and plan.md

Reviewer: Codex GPT-6.1-Sol, high effort, 2026-10-13. Brief: eliminate, never confirm; return only contradictions, false claims, vocabulary collisions, dropped high-value ideas, method holes, and machinery without a reader. Line numbers refer to the reviewed version, before the fixes.

Every finding below was checked against the files and the post, and all 19 were applied.

1. **P1, method hole.** design.md:221. Diagnosis-only callers reach repair and promotion unconditionally, although `investigation`, QA, and claim audits are read-only entry points. Fix applied: a requested outcome recorded at intake; a `diagnosis` stops after step 7 and lists repairs and promotions as follow-ups
2. **P1, false confirmation.** design.md:129. Surviving one killing prediction does not separate a cause from alternatives that predict the same result. Fix applied: `confirmed` needs a test no other live hypothesis passes, such as toggling the cause or an observed causal chain
3. **P1, false fixed.** design.md:221. Restoring one strong signal can close a case while the reported failure persists. Fix applied: `fixed` needs the signal back at the control's value, the symptom gone, and a residual check
4. **P1, method hole.** design.md:122. A candidate had to explain every signal, including lab facts from a rejected repro, so the hang's clock-skew repro could block the right diagnosis. Fix applied: the `in scope` term
5. **P1, method hole.** design.md:119. `H0` had no mechanism, no killing prediction, and an unspecified role in counts. Fix applied: `H0` is a reservation, never marked, counted, or a candidate, and it limits every claim
6. **P1, contradiction.** design.md:217. "Skip probes whose predictions agree" also skipped validation and re-gathering. Fix applied: the rule covers discrimination probes only
7. **P1, dropped detail.** design.md:120. The difference between "insufficient alone" and "contradicts" was missing, which would block combining a trigger with a sustaining cause. Fix applied: precise mark definitions and derived combination marks
8. **P1, counting hole.** design.md:121. Parents of a split or a merge stayed live and inflated strength. Fix applied: status `replaced`, and a combination counts once with its members
9. **P1, endless loop.** design.md:219. No exit when the ladder is exhausted, no control exists, access is refused, or progress stops. Fix applied: exits that return `open` with the missing observation
10. **P1, caller contradiction.** design.md:282. poteto-mode's `how` trigger and bug-fix's closing `how` and `why` fan-out still sent agents to source first. Fix applied: both qualified in the changes table
11. **P2, dropped idea.** design.md:232. Dropping aggregate gauges removed detectors from the gate. Fix applied: two-tier gate, detectors decide pass or fail, gauges localize
12. **P2, impossible check.** plan.md:33. "Every scenario above baseline" fails a scenario already at 100 percent. Fix applied: mandatory behaviors, no regression, improvement on the targeted behaviors
13. **P2, phase contradiction.** plan.md:33. Phase 1 gated on the build-time scenario, which Phase 4 implements. Fix applied: Phase 1 and 2 gate on diagnosis scenarios only
14. **P2, method hole.** design.md:192. A wrong `x` could never be corrected without replacing the fact. Fix applied: a later judgment for the same hypothesis and fact supersedes the earlier one, with a reason
15. **P2, dropped rule.** design.md:235. The gate had no procedure for intended changes. Fix applied: declare the gauges a change should move before the run
16. **P2, source contradiction.** design.md:238. "Replicas per shard" gives 80, not the post's 5, and the claim that a count would fail at 2 by 1 did not follow from the post. Fix applied: the gauge records the lookups themselves
17. **P2, inline-path contradiction.** design.md:224. The small-bug path came after step 0 opened a case and step 3 required a slate. Fix applied: the path is chosen at step 0
18. **P2, repository convention.** plan.md:16. Phase 0 fixtures under a package with no `SKILL.md` fail compilation. Fix applied: Phases 0 and 1 share one PR
19. **P2, vocabulary.** design.md:103. `candidate`, `layer`, and `route` each named two things. Fix applied: `new run` for builds, `level` for the tower, `destination` for where an intervention lands
