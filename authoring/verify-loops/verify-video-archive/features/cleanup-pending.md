# Cleanup pending

The archive command keeps a verified publication when source removal fails. It
reports `cleanup pending`, retains the source, and exits `1`.

## Sub-features

- `cleanup-pending.exit` checks exit status `1`
- `cleanup-pending.operation` checks the durable operation state
- `cleanup-pending.source-retained` checks the source hash
- `cleanup-pending.pty-output` checks the durable outcome and reason
- `cleanup-pending.archive.*.reopened` checks the verified publication

## How to get to it (user POV)

Run `just convert-video` when the archive can publish but cannot remove the
source from its input directory.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature cleanup-pending
```

## Gotchas

- The driver changes permissions only on its disposable input directory
- The driver restores those permissions before evidence collection
- Cleanup pending is unresolved even though the archive reopens and decodes
