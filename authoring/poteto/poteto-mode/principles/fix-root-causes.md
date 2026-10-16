# Fix Root Causes

When debugging, fix the fault, not the place where it surfaced. The symptom is where a wrong state became visible. The root cause is the first place the system did something it should not do, or failed to handle a state it should handle. To find it in a runtime failure, run the **diagnose** skill.

**Why:** A symptom fix hides the evidence and leaves the fault free to surface somewhere else. Each one makes the system harder to reason about, because the code now carries a workaround for a bug that nobody named.

**Pattern:**
- Facts and a control first, then reproduce with parity
- Accept as the cause only the hypothesis, or the minimal combination of hypotheses, that explains every signal and that no fact contradicts
- When stuck, descend one layer: gather the same readings one level down the stack, against the same control. Don't guess
- Ask whether the state that triggered the symptom is legitimate. If the system may be in that state, the code that broke on it is the root cause, and handling the state there is the fix. If the state should never exist, a check where it broke hides the bug, so find what produced the state. Guards, retries, swallowed errors, clamped values, and discarded state are the usual ways to hide a bug
- When something fails only after a restart, suspect persisted state first: config files, caches, lock files, serialized state
- Check for the pattern, not just the instance. Find every place with the same fault and fix them all
- If a workaround needs a paragraph-long comment to justify it, the code is wrong. Fix the code, not the comment
- If the deciding fact took a deep dig to find, propose the cheap, always-on reading that would have shown it at first look
