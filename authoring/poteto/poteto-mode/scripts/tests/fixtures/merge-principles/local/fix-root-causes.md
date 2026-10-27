# Fix Root Causes

When debugging, do not fix symptoms. Trace every problem to its root cause and fix it there. To find the root cause of a runtime failure, run the **diagnose** skill.

**Why:** Symptom fixes accumulate. Each workaround makes the system harder to reason about, and the real bug remains. Root-cause fixes are slower upfront but reduce total debugging time.

**Pattern:**
- Facts and a control first, then reproduce with parity
- The root cause is the hypothesis, or the minimal combination of hypotheses, that explains every signal and that no fact contradicts
- Do not add guards (adding a nil check to silence a crash is a symptom fix)
- If a workaround needs a paragraph-long comment to justify it, the code is wrong (fix the code, not the comment)
- Check for the pattern, not just the instance (grep for the same pattern, fix all instances)
- When stuck, descend one layer: gather the same readings one level down the stack, against the same control. Don't guess

**Restart bugs: suspect state before code**

When something "fails after restart," suspect stale persistent state first: config files, caches, lock files, serialized state. If clearing a state file restores behavior, prioritize state validation as the fix.
