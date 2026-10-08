# Diagnostics

Diagnostics reports Deepgram credential availability, commands, browser state, and source paths without calling paid APIs.

## Sub-features

- `diagnostics.youtube` validates the YouTube doctor's answer, readiness, and exit code
- `diagnostics.zoom` validates the Zoom doctor's answer, readiness, and exit code

## How to get to it (user POV)

- Run `transcript doctor --source youtube`
- Run `transcript doctor --source zoom`
- Run `verify-transcript doctor` to diagnose the verifier layout itself

## Driving it with verify-transcript

Preconditions:

- Diagnostics are read-only and require no paid authorization
- A machine can be unready while still returning a valid diagnostic report

- **YouTube report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.youtube`. Require `{"ok":true}` on exit `0`, or on exit `1` one error per failed YouTube check, each with its fix; `readiness_ok` is whether it exited `0`
- **Zoom report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.zoom`. Require the same for Zoom checks and inspect `failed_checks` when unready
- **Verifier report.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" doctor`. Require the expected layout, `uv`, and all Feature Map pages

## Gotchas

- A failed readiness check does not mean the doctor behavior is broken
- Both diagnostics include the `claude` and `pi` checks; a missing `pi` only warns, because only non-default profiles need it
- Diagnostics can read default browser and Zoom paths but do not mutate them
- Inspect `readiness_ok` before attempting the paid feature
- Doctor does not measure upload bandwidth or prove that an audio file reached Deepgram
- An upload or workflow timeout fails with an error whose fix reruns with twice the `--timeout`; a stalled write reports a lower bound on bytes sent because the last block may have been partially transmitted
- Use the upload verification loop in [SKILL.md](../SKILL.md) to check timeout behavior without paid calls
