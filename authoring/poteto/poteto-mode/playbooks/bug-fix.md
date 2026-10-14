---
description: "Diagnose and fix a reported defect with runtime evidence."
---

### Bug fix

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

**You own this task. Plan, review, verify.** Delegate investigation and the fix to subagents, stay in the lead.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix. It does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more.

1. Load the **diagnose** skill and start it on the report, with requested outcome `fix`, before you open any source file. Gather its facts yourself on the matching surface via the available driver and project verification recipe (Non-negotiables). `diagnose`'s `references/parity.md` sets the environment a repro and the step-4 proof run in. Don't hand the repro to the user. A debug or instrumentation protocol that says to ask the user does not override this. You drive the instrumented runtime. Ask the user only with a stated, specific reason the control surface cannot reach the target, and only after driving it as far as it goes.
2. Run `diagnose` through its step 7. Open source files and code diffs only once it isolates a signal, then fan out `how` and the **why** skill as parallel subagents, scoped to that signal. A `confirmed` cause continues at step 3, and steps 3 to 5 are `diagnose`'s step 8. Any other claim level goes straight to the reply.
3. Plan the fix. If it crosses a function boundary, `architect` first. Delegate implementation to a subagent with the `Builder` role with a specific scope. Review the diff.
4. Verify on the same surface. The reading that exposed the bug passes `diagnose`'s fix parity. "Inconclusive" or wrong-surface is not a pass. Flag it. Unit tests show branch behavior, not bug absence.
5. Stage the commits so the failing repro lands before the fix in git history. See the **tdd** skill for the failing-test-first cadence when the bug has a cheap local test path. Skip it when the test would be expensive, integration-heavy, or unclear.
   This is the canonical **Sequence Work into Verifiable Units** principle, the failing test first and the fix on top.
6. Run **Opening a PR**.

**Reply:** what was broken, root cause and its claim level, fix, how you verified, and what the field re-read after the merge must show. Paste the step-4 proof's failing-then-passing output verbatim.
