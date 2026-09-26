---
name: Reliability
description: Review error handling, retries, timeouts, idempotency, concurrency, background work, external systems, and failure-mode behavior.
---

# Reliability

Use this conditional lens when the diff touches operations that can fail or run over time.

## Investigator Evidence Focus

1. Identify failure modes introduced or affected by the change.
2. Inspect error handling, retries, timeouts, cancellation, cleanup, idempotency, and partial-failure behavior.
3. Look for race conditions, resource leaks, non-determinism, unbounded loops, and unsafe background work.
4. Check observability where relevant: logs, warnings, surfaced errors, and recovery guidance.
5. Note whether validation covers failure paths.

## Subject Adaptation

- For network/external calls, prioritize timeouts, retries, backoff, and error classification.
- For file operations, prioritize atomic writes, backups, permissions, cleanup, and idempotency.
- For automation scripts, prioritize safe re-runs, clear failures, and non-destructive dry-run/apply behavior.
- For agents/workflows, prioritize graceful degradation when tools, files, or delegated investigators are unavailable.

## Parent Synthesis Hints

Reliability findings block readiness when normal failures can corrupt state, hang, silently lose work, or leave users without recovery. Use `P2` for important hardening that can follow soon.
