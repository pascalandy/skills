# Publication recovery

The verifier stops its own process group after the archive command writes a
durable `prepared` operation. A second real Just invocation completes that
same operation without publishing a duplicate.

## Sub-features

- `recovery.owned-group-stopped` records scoped process-group signals
- `recovery.durable-prepared` checks the stopped durable state and candidate
- `recovery.source-retained` checks the interrupted source hash
- `recovery.resumed-exit` checks the second Just invocation
- `recovery.same-operation` checks durable identity across recovery
- `recovery.no-duplicate` checks the final destination count
- `recovery.archive.*.reopened` checks the recovered archive

## How to get to it (user POV)

Run `just convert-video` again after a prior archive process stopped after
writing its operation record. The command reconciles operations before it
discovers new work.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature recovery
```

Inspect `interrupted-operation.json`, both invocation transcripts, and the
final copied operation record.

## Gotchas

- The pause environment variable is verifier-only and inactive by default
- The verifier sends signals only to the process group created by its live `Popen` handle
- Cleanup never trusts a retained PID or sends a later signal
- A fresh operation or a second destination fails the feature
