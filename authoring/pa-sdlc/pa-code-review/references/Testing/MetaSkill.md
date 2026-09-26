---
name: Testing
description: Review whether tests or checks give meaningful confidence for the implementation and its important failure modes.
---

# Testing

Use this lens for test adequacy, check coverage, and verification gaps.

## Investigator Evidence Focus

1. Identify tests/checks touched by the diff and tests/checks that should cover the changed behavior.
2. Compare implementation intent against assertions, fixtures, snapshots, mocks, and manual validation notes.
3. Look for missing critical cases, especially regressions, boundaries, error paths, and contract behavior.
4. Detect brittle tests that assert implementation details instead of behavior.
5. Note whether relevant checks appear runnable from project tooling, but do not run them unless parent explicitly allowed it.
6. Flag gaps that materially reduce review confidence.

## Subject Adaptation

- For bug fixes, look for a regression test that fails before and passes after.
- For new behavior, look for happy path plus at least one meaningful edge/error case.
- For docs/workflow/template changes, look for validation commands, render/apply checks, or distribution checks.
- For CLI changes, look for command examples, exit-code behavior, and stderr/stdout expectations.

## Parent Synthesis Hints

Missing tests are usually `P1` only when the change is risky, public, or difficult to verify manually. Use `P2` for important but non-blocking confidence gaps and `P3` for small coverage improvements.
