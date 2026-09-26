---
name: Correctness
description: Review whether the implementation appears to satisfy the intended behavior without logic errors, missed edge cases, or regressions.
---

# Correctness

Use this lens for behavior, control flow, data flow, and edge-case correctness.

## Investigator Evidence Focus

1. Restate the implementation intent from the parent prompt.
2. Inspect the diff and nearby code paths that execute the changed behavior.
3. Check whether the code handles normal, boundary, empty, error, and backward-compatibility cases relevant to the change.
4. Look for mismatches between naming, comments, tests, and actual behavior.
5. Identify likely regressions in adjacent call sites or consumers.
6. Flag only actionable issues with concrete evidence.

## Subject Adaptation

- For UI or content behavior, inspect state transitions, rendering conditions, and user-visible fallbacks.
- For backend code, inspect validation, branching, persistence, serialization, and side effects.
- For scripts/CLIs, inspect argument parsing, paths, shell safety, exit behavior, and idempotency.
- For documentation tooling, inspect source-of-truth paths and generated/applied copies.

## Parent Synthesis Hints

Correctness findings often block readiness when they affect the intended behavior. Escalate to `P1` when a normal user path or explicit requirement is broken; use `P2` for plausible edge-case risk with weaker evidence.
