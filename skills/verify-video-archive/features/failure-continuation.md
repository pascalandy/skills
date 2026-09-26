# Failure continuation

One corrupt media file fails without blocking a later valid file. The corrupt
source remains byte-identical while the valid sources publish.

## Sub-features

- `mixed.exit` checks the expected nonzero batch result
- `mixed.order` checks valid, corrupt, valid processing order
- `mixed.continues` checks both successful operations
- `mixed.failed-source-retained` checks the corrupt source bytes
- `mixed.successful-sources-removed` checks successful cleanup
- `mixed.narrow-pty` checks counts, stage text, filename suffix, and failure text at 48 columns

## How to get to it (user POV)

Run `just convert-video` with valid media before and after an unreadable MP4 in
the default input folders.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature mixed-batch
```

Inspect the retained corrupt input and the invocation transcript.

## Gotchas

- Exit status `1` is expected because one item failed
- The feature passes only when the later valid file reaches a complete operation
- A retained filename without the original hash does not prove source safety
