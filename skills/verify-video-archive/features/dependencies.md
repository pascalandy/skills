# Dependency preflight

The archive command checks every runtime dependency before recovery or archive
mutation. Each missing dependency produces an actionable error and a nonzero
exit while the generated source remains byte-identical.

## Sub-features

- `dependencies.python` checks Python 3.11 or newer
- `dependencies.ffmpeg` checks FFmpeg discovery
- `dependencies.ffprobe` checks FFprobe discovery
- `dependencies.libx265` checks the software x265 encoder
- `dependencies.lsof` checks open-file inspection support

## How to get to it (user POV)

Run `just convert-video` without one required executable or encoder.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature dependencies
```

## Gotchas

- Each case uses a separate task-owned restricted `PATH`
- A skipped case cannot pass the feature
- No case may create an owner record or operation
