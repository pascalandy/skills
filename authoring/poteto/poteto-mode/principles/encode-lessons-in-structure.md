# Encode Lessons in Structure

Encode recurring fixes in mechanisms (tools, code, metadata, automation) instead of textual instructions. Every error, human correction, and unexpected outcome is a learning signal. Capture it, route it, and close the loop.

**Why:** Textual instructions are easy to miss. They require the reader to notice, remember, and comply. Structural mechanisms (lint rules, metadata flags, runtime checks, automation scripts) enforce the rule without cooperation.

**Pattern:**
When you catch yourself writing the same instruction a second time:
1. Ask: can this be a lint rule, a metadata flag, a runtime check, or a script?
2. If yes, encode it. Delete the instruction
3. If no (requires judgment), make the instruction more prominent and add an example of the failure mode

**Pick the strongest mechanism.** When more than one mechanism would work, choose the strongest the situation allows, in this order:
1. An architecture where the mistake has no place: one owner per piece of state, one supported way per task, internals hidden so the wrong import fails, one source of truth instead of hand-synced lists, and no old way or dead code left to copy
2. A type that makes the bad state unrepresentable
3. A lint or banned API that fails the check command with an error naming the file, type, or function to use instead. When the pattern is already common, fail only when a change adds more
4. A canonical helper
5. A runtime check
6. A test of the behavior, per **Test Behavior, Not Implementation**
7. An instruction, only for a judgment call

Agents copy whatever the surrounding code already does, so a weaker guard becomes the next template. When the user invokes `correct`, that skill applies this ladder across a whole repository.

**Corollary:** If the fix is structural, only use the structural fix. The instruction is the symptom.

**Feedback loop:**
- **Capture every correction.** When the human intervenes or tests fail, decide if it's a one-off or a pattern.
- **Route to the right layer.** One-off -> brain note. Recurring fix -> skill or lint rule. Systemic issue -> principle.
- **Close the loop.** Don't just record. Apply now or create a concrete todo.

**Anti-patterns:**
- Acknowledging without recording ("I'll keep that in mind" does not persist)
- Recording without routing (a brain note about a lint rule that should exist is wasted unless the lint rule gets implemented)
- Fixing without generalizing (fixing one instance while leaving the recurring pattern intact)
