# Dry runs

Dry runs validate a source and resolve its plan without reading secrets, calling an API, or creating transcript output.

## Sub-features

- `youtube.dry-run-summary` validates a YouTube summary plan and isolated output path
- `zoom.dry-run` validates a disposable Zoom folder, `.m4a` path, and Zoom summary defaults
- `dry-runs.transcript-only` validates `--no-summary`, timeout overrides, and isolated output paths for both sources

## How to get to it (user POV)

- Add `--dry-run` to a YouTube or Zoom run
- Keep `--output-dir` explicit when checking a non-default plan
- Use a real Zoom meeting folder or an eval-owned fixture folder

## Driving it with verify-transcript

Preconditions:

- The verifier owns the temporary source fixture and planned output paths
- No paid authorization is present or required

- **YouTube plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.dry-run-summary`. Require exit `0`, the expected plan, and an absent output directory
- **Zoom plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature zoom.dry-run`. Require the disposable source paths, Zoom summary defaults, and a planned output path that remains absent
- **Transcript-only plans.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature dry-runs.transcript-only`. Require null summary settings, timeout overrides, and absent output paths for both sources
- **Full free suite.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify`. Require both dry-run features to pass in the retained result

## Gotchas

- YouTube dry-run checks URL syntax but does not download media
- Zoom dry-run resolves an actual folder and `.m4a`, so the eval creates an empty disposable fixture
- A dry run must not create its planned output directory
- Transcript-only dry runs still validate the source before returning the plan
