# Vision Lenses

A small library of reframing tools for direction-setting. Pick the one or two lenses that fit the situation. Running every lens mechanically is a failure mode, not thoroughness.

These lenses are tuned for deciding where work should go. They apply across the domains `pa-vision` serves: software, content or websites, PM systems, knowledge systems, and personal decisions.

---

## How Might We (HMW)

Reframe the problem as an opportunity. Forces clarity on who it serves, the outcome, and the constraint.

Format: *How might we [desired outcome] for [specific beneficiary] without [key constraint]?*

**Good HMW traits**
- Narrow enough to be actionable.
- Broad enough to allow more than one solution.
- Contains a real tension or constraint.

**Bad HMW traits**
- Too broad: "How might we make things better?"
- Solution-embedded: "How might we add a sidebar?"
- No constraint, so any answer qualifies.

**Best for:** a vague or solution-anchored ask at the start of `DirectionCheck`.

---

## First Principles

Strip to fundamental truths, then rebuild.

1. What do we know is actually true, not assumed and not convention?
2. What are we assuming, including the obvious things?
3. Which assumptions are laws of physics versus "how it has been done"?
4. If only the truths remained, what would we build?

**Best for:** breaking out of incremental thinking when every candidate direction feels like a small variation on the current state.

---

## Jobs to Be Done (JTBD)

People hire a product, workflow, page, note, or habit to do a job. Separate three layers:

- **Functional job:** task to complete.
- **Emotional job:** how they want to feel.
- **Social job:** how they want to be perceived.

Format: *When I [situation], I want to [motivation], so I can [outcome].*

The real competitor is whatever they do today, which is often not in the same category.

**Best for:** `AlignmentDraft` when the beneficiary or the actual problem is still fuzzy.

---

## Constraint Injection

Deliberately impose a constraint to cut ambiguity.

- Time: "What if we had one week?"
- Surface: "What if it could only do one thing?"
- Tooling: "What if we couldn't use the obvious tool?"
- Cost: "What if it had to stay free or trivial to maintain?"
- Audience: "What if the beneficiary had never done this before?"
- Scale: "What would it look like for ten people? For ten thousand?"

**Best for:** any mode where scope is sprawling or the direction keeps widening instead of sharpening.

---

## Pre-Mortem

Imagine the direction already failed. Work backward.

1. It is six to twelve months from now and this direction flopped. What happened?
2. List every plausible failure, including technical, adoption, maintenance, timing, and external.
3. For each, mark it as preventable or fatal.
4. Which failures are acceptable risk? Which would kill the work?

**Best for:** `DirectionCheck` when the direction feels good but has not been tested. Also feeds the assumption audit directly.

---

## Analogous Inspiration

Look for structural analogs, not surface-level ones.

- What domain has already solved a version of this?
- What would a known reference org, product, or system do here?
- What natural or historical system works this way?

Surface-level: "Uber for X."
Structural: "A two-sided marketplace that solves a trust problem between strangers."

**Best for:** expanding a narrow direction into meaningfully different options worth comparing.

---

## Inversion

Flip the default assumption.

- What if we did the opposite?
- What if the user did the work the system does today, or vice versa?
- What if the thing we are optimizing for is the wrong target?

**Best for:** a quick sanity check on any settled-feeling direction before moving to `BriefAuthoring`.

---

## Selection heuristic

| Situation | Start with |
|---|---|
| Direction is vague or solution-anchored | HMW |
| Problem framing is unclear | JTBD |
| Every option feels incremental | First Principles, Inversion |
| Scope is sprawling | Constraint Injection |
| Direction feels good but untested | Pre-Mortem |
| Need meaningfully different options to compare | Analogous Inspiration |
