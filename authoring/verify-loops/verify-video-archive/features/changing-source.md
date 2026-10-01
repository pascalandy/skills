# Changing source

The archive command detects a generated source changed during conversion,
keeps that source, and publishes no archive.

## Sub-features

- `changing-source.exit` checks the nonzero result
- `changing-source.detected` checks the source-change reason
- `changing-source.retained` checks source retention
- `changing-source.not-published` checks the absence of a durable publication

## How to get to it (user POV)

Run `just convert-video` while the source recorder is still changing the file.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature changing-source
```

## Gotchas

- The driver changes the source only after the terminal reports `encoding`
- The changed source is retained as evidence
