# Output contracts

Redirected, the archive command prints each archived path on standard output
and keeps standard error quiet. In JSON mode it writes one batch document to
standard output; `-v` adds plain progress and outcomes on standard error. The
journal remains plain text.

## Sub-features

- `output.redirected` checks one archived path on standard output and an empty
  standard error
- `output.json` parses one `video-archive.batch/v1` document
- `output.json-stderr` checks that `-v` adds plain progress and the outcome on
  standard error
- `output.journal-plain` rejects terminal controls in the journal

## How to get to it (user POV)

Redirect `just convert-video` to a file, or run `just convert-video --json -v`
with standard output and standard error separated.

## Driving it with verify-video-archive

Run this after Launch and Doctor.

```bash
uv run --no-project python "$VERIFY_DIR/scripts/verify_video_archive.py" \
  drive --manifest "$MANIFEST" --feature output-contracts
```

## Gotchas

- JSON standard output must contain no progress prefix or trailing document
- The driver uses a new generated source for each invocation
- `NO_COLOR` does not remove outcome symbols, labels, stages, counts, or reasons
