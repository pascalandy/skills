---
name: Maintainability
description: Review local design quality, simplicity, cohesion, readability, and future-change cost.
---

# Maintainability

Use this lens for whether the implementation is understandable, cohesive, appropriately factored, and not overbuilt.

## Investigator Evidence Focus

1. Inspect the changed code and immediate neighbors for unnecessary complexity or duplication.
2. Check whether names, boundaries, and responsibilities match the surrounding module style.
3. Look for deep coupling, hidden side effects, leaky abstractions, or scattered policy.
4. Identify code that is hard to reason about, test, or safely change later.
5. Prefer concrete simplifications over broad style opinions.
6. Avoid nitpicks unless they meaningfully affect comprehension or future edits.

## Subject Adaptation

- For small diffs, focus on whether the simplest local fix was used.
- For new modules, focus on interface size, dependency direction, and ownership clarity.
- For agent/skill workflows, focus on clear parent/investigator responsibilities and source-of-truth boundaries.
- For scripts, focus on idempotency, readable control flow, safe defaults, and clear errors.

## Parent Synthesis Hints

Maintainability rarely blocks QA alone. Use `P1` only for complexity that likely causes defects or unsafe operation. Use `P2` for meaningful cleanup before the pattern spreads; `P3` for nits.
