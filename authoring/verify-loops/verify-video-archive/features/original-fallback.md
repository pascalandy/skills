# Original fallback

The archive command preserves the generated original when its real conversion
is not smaller.

## Sub-features

- `fallback.operation` checks the durable `original` outcome
- `fallback.byte-identical` checks the original size and SHA-256
- `fallback.archive.*.reopened` probes and decodes the preserved media
- `fallback.source-removed` checks cleanup after verification
- `fallback.no-color-pty` checks explicit labels and original-preservation stage without color

## How to get to it (user POV)

Run `just convert-video` with a tiny, efficiently encoded source whose archive
profile cannot reduce its size.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature original-fallback
```

Require `kind: original` in the copied operation record.

## Gotchas

- The fixture's intent does not prove fallback
- A changed FFmpeg build can change the size decision, which makes this feature fail
- The archived file must match the pre-run source hash, not only its byte count
