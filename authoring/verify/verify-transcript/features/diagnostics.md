# Diagnostics

Diagnostics reports Deepgram credential availability, commands, browser state, and source paths without calling paid APIs.

## Sub-features

- `diagnostics.youtube` validates YouTube doctor JSON, counts, readiness, and exit code
- `diagnostics.zoom` validates Zoom doctor JSON, counts, readiness, and exit code

## How to get to it (user POV)

- Run `transcript doctor --source youtube --json`
- Run `transcript doctor --source zoom --json`
- Run `verify-transcript doctor --json` to diagnose the verifier layout itself

## Driving it with verify-transcript

Preconditions:

- Diagnostics are read-only and require no paid authorization
- A machine can be unready while still returning a valid diagnostic report

- **YouTube report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.youtube --json`. Require counts that match checks and an exit code that matches `readiness_ok`
- **Zoom report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.zoom --json`. Require the same consistency and inspect failed requirement messages when unready
- **Verifier report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" doctor --json`. Require the expected layout, `uv`, and all Feature Map pages

## Gotchas

- A failed readiness check does not mean the doctor behavior is broken
- `diagnostics.zoom` includes the Pi check to match the command in `transcript`
- Diagnostics can read default browser and Zoom paths but do not mutate them
- Inspect `readiness_ok` before attempting the paid feature
- Doctor does not measure upload bandwidth or prove that an audio file reached Deepgram
- Upload and workflow timeouts return `transcription_timeout`; a stalled write reports a lower bound on bytes sent because the last block may have been partially transmitted
- Use the upload verification loop in [SKILL.md](../SKILL.md) to check timeout behavior without paid calls
