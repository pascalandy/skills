# Graceful interruption

The verifier sends SIGINT to its owned process group after the PTY shows the
encoding stage. The command retains the source, reports `interrupted`, and exits
`130`.

## Sub-features

- `interruption.exit` checks exit status `130`
- `interruption.signal` checks the owned process-group signal
- `interruption.source-retained` checks the source hash
- `interruption.not-published` rejects premature success
- `interruption.pty-output` checks the durable result and summary

## How to get to it (user POV)

Press Ctrl+C while `just convert-video` is encoding a file.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature interruption
```

## Gotchas

- The driver signals only the process group created by its live process handle
- The generated source is long enough to expose a measured encoding stage
- A completed archive or exit status `1` fails this feature
