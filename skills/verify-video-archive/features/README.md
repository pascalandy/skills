# Video archive verification map

This map covers the archive workflow reached by `just convert-video`. It
excludes the separate `video-archive convert` command, Raycast window behavior,
clipboard integration, and personal media.

## Baseline preconditions

- Resolve `verify_video_archive.py` relative to this skill directory
- Launch one unique run and keep the manifest path its answer names in `file`
- Run Doctor before Drive
- Require macOS or Linux, Python 3.11 or newer, Just, FFmpeg, FFprobe, `libx265`, and a resolved `lsof`
- Use only the generated scenario paths recorded in the manifest

## Driving conventions

- Invoke archive behavior only through `just convert-video`
- Let the isolated installed-path link execute the checkout wrapper
- Keep every process handle and process group in the active verifier process
- Use a task-owned PTY for live progress and set width only for layout checks
- Verify archives with FFprobe, full FFmpeg decode, size, and SHA-256
- Keep a failed or unfinished source and verify its hash
- Treat `skipped` and `unmet` as separate from `passed`

## Proof and skip reporting

- Read each check's expected and observed values in `manifest.json`
- Inspect raw standard output and standard error for a failed invocation
- Inspect copied operation records and the journal beside the manifest
- Require the second real Just invocation for recovery
- Run Cleanup, then reopen `manifest.json` and retained media evidence
- A platform-specific skip names the unsupported feature and does not satisfy real-media acceptance for that platform

## Feature entry contract

Each feature page uses these four H2 sections in this order.

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with verify-video-archive`
4. `Gotchas`

## Features

- [Successful conversion](conversion.md) covers a smaller verified HEVC archive and source removal
- [Deterministic ordering](ordering.md) covers source timestamp order before normalized path order
- [Open source](open-source.md) covers required open-file inspection and source retention
- [Changing source](changing-source.md) covers a source modified during conversion
- [Lock contention](lock-contention.md) covers exclusive archive ownership during a concurrent run
- [Dependency preflight](dependencies.md) covers actionable failures before mutation
- [Failure continuation](failure-continuation.md) covers a corrupt file between valid files
- [Original fallback](original-fallback.md) covers byte-identical preservation when conversion is not smaller
- [Destination collisions](collisions.md) covers no-replace suffix selection
- [Publication recovery](recovery.md) covers a durable interruption and second real invocation
- [Cleanup pending](cleanup-pending.md) covers verified publication with failed source removal
- [Graceful interruption](interruption.md) covers SIGINT during encoding and exit 130
- [Output contracts](output-contracts.md) covers redirected paths, JSON streams, and plain journals
- [Backend benchmark](backend-benchmark.md) covers repeated full-command measurements, pre-fallback candidate size, preservation gates, and blinded quality review
- [Parallel batch](parallel-batch.md) covers 100-video serial, normal, maximum, cancellation, lock contention, and recovery runs
