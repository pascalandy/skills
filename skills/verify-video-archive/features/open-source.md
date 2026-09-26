# Open source

The archive command detects a source held open by another process, keeps the
source byte-identical, and exits `1` without publishing it.

## Sub-features

- `open-source.exit` checks the nonzero result
- `open-source.detected` checks the actionable reason
- `open-source.retained` checks the source hash
- `open-source.not-published` checks the absence of an operation

## How to get to it (user POV)

Run `just convert-video` while another process holds a source open.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature open-source
```

## Gotchas

- The driver holds only its generated source open
- The check uses the platform's resolved `lsof` executable
