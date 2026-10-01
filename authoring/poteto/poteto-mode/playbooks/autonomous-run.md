### Autonomous run

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

**You own the exit condition. Define done, then drive to it without stopping.**

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero).
2. Pick the wake mechanism using the watcher protocol in the agent-runtime reference. For an event (CI, a merge, a ref advancing), use a watcher subagent only when delegation and completion delivery exist. Otherwise run a local watcher process and supervise its output in bounded waits from the active session. For time-based checks, record the next useful check time and use the same supported supervision. A separate heartbeat is optional only if its wake delivery is verified. Without an idle-session wake mechanism, keep checking while the session is active and checkpoint the exact next check before ending; report that unattended continuation is unavailable.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride.
   Sequence the work via the **sequence-verifiable-units** principle skill, verifying each unit before the next instead of batching checks at the end.
4. Mid-run discoveries are yours. Address broken skills, related bugs, flaky verifiers, review noise, tooling failures, orphaned follow-ups, and fixable drift yourself via poteto-mode. Put out-of-band fixes in their own PR. Do not park reversible work for the human for routine implementation choices. Surface only irreversible actions, genuine product or preference calls no experiment can settle, or a real dead end. Keep the predicate as the main drive, and return to it after each side fix.
5. Checkpoint every iteration via the **show-me-your-work** skill, a row for what changed and whether the predicate moved.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
