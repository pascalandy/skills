# Successful conversion

The archive command converts a generated lossless video into a smaller,
readable HEVC archive and removes the source after publication verification.

## Sub-features

- `conversion.exit` checks the Just exit status
- `conversion.operation` checks the durable converted operation
- `conversion.smaller` compares source and archive bytes
- `conversion.archive.*.reopened` probes, decodes, and hashes the archive
- `conversion.source-removed` checks final source absence
- `conversion.pty-output` checks measured progress and the green success label
- `conversion.journal-plain-stages` checks canonical stages without terminal controls

## How to get to it (user POV)

Run `just convert-video` with a video in either default input folder. The
verifier provides the isolated home and generated source.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature conversion
```

Require every `conversion.*` check to pass.

## Gotchas

- A zero exit alone does not prove a readable archive
- The verifier checks the durable operation hash and performs a full decode
- The generated source copy in evidence is the pre-run comparison point
