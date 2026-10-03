---
description: "Test how a skill, structure, or prompt change affects agent behavior before promoting it."
---

### Eval

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

**You own the experiment design. Plan, blind, run, synthesize.**

**Non-negotiables for blinding:**

- No `eval`, `test`, `judge`, `experiment`, `rubric`, `score`, `compare`, `benchmark`, `candidate`, or `arena` in any directory, file, or prompt the candidate sees.
- The candidate prompt looks like an organic user request. State the goal, not the meta.
- No chain-eliciting cues. Don't ask the candidate to list which skills, principles, or files they applied. Ask for design notes generally and grade chain-following from code shape, not self-report.
- Sanitize directory and slug names. Use project-shaped names a user might pick.
- Don't tell the candidate other candidates exist.
- The judge can know it's judging but sees outputs by sanitized label only, never by model name.
- Comparing two variants: one judge scores both sets in a single pass on one scale, blind to which set each came from.

**Steps:**

1. **Frame.** State what variant is under test and what behavior counts as success. Write the rubric (3-6 concrete criteria) for the judge only. Hold it back from candidates.
2. **Set up sanitized environments.** Per-candidate working dir with the variant in place. Plant any context an organic task would have: a project skeleton, the skills the candidate would naturally read.
3. **Author one organic prompt.** What a user would type. No leakage of what's being measured.
4. **Run N independent candidates** per the **arena** skill's Phase B. Use parallel sessions and distinct available models when supported; otherwise run independent sessions serially and report reduced parallelism or model diversity. Each works in its own sanitized dir. Same prompt to each. Without independent sessions, report that the comparison cannot supply independent candidate evidence.
5. **Spawn one blinded judge** in an independent context per the **arena** skill's Phase C. Prefer a distinct available model family; if unavailable, report the missing model diversity. If no independent context is available, leave the independent verdict blocked rather than substituting self-review. Judge sees outputs by sanitized label and the rubric, never a model name.
6. **Verify the chain from transcripts, not self-report.** Read project-scoped candidate transcripts or tool-event exports through the harness's supported interface. If file-open events are not exposed, mark chain-following unverified and grade only observable artifacts; never infer tool use from a candidate's claims. Look at which files each candidate actually opened. Grade chain-following from the files it really read plus the shape of the code, never from the candidate's own claims.
7. **Read every candidate output yourself** end to end. Compare to the judge's verdict. Disagreement means a model is biased or the rubric is ambiguous. Synthesize.

**Reply:** variant under test, rubric, per-candidate notes, judge's verdict, your synthesis, and a recommendation for whether to promote the variant.
