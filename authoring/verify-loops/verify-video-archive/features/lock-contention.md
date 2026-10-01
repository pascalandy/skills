# Lock contention

The archive command refuses a second active run with exit `75`. It keeps the
source byte-identical and creates no operation.

## Sub-features

- `lock-contention.exit` checks exit `75`
- `lock-contention.reported` checks the active-run error
- `lock-contention.source-retained` checks the source hash
- `lock-contention.not-published` checks the absence of an operation

## How to get to it (user POV)

Start `just convert-video` while another archive run owns the same archive lock.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature lock-contention
```

## Gotchas

- The driver owns the competing lock through a live file descriptor
- The driver does not infer lock ownership from a retained process ID
