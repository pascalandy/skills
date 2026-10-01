# Deterministic ordering

The archive command processes the older source before a newer source whose
normalized path sorts first.

## Sub-features

- `ordering.exit` checks the Just exit status
- `ordering.source-timestamp` checks the durable operation order
- `ordering.archive.*.reopened` checks both published archives

## How to get to it (user POV)

Run `just convert-video` with sources that have different source timestamps.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature ordering
```

## Gotchas

- macOS supplies the birth time
- Linux supplies the modification time when birth time is unavailable
- Unit tests cover the normalized path tie-breaker without depending on filesystem timestamps
