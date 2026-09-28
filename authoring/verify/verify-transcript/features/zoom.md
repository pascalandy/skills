# Zoom

Zoom mode selects a meeting folder that contains an `.m4a` recording, transcribes the recording, and can create a meeting summary.

## Sub-features

- `diagnostics.zoom` checks the default Zoom directory and Deepgram credential without paid calls
- `zoom.dry-run` resolves a disposable meeting, audio file, and Zoom summary defaults without network calls or output writes
- `dry-runs.transcript-only` resolves the disposable meeting with summary generation disabled

## How to get to it (user POV)

- Run `transcript run zoom --latest --json` for the latest meeting under `~/Documents/Zoom`
- Run `transcript run zoom --path <folder> --json` for one meeting folder
- Pass the meeting folder to `--path`, not its `.m4a` file

## Driving it with verify-transcript

Preconditions:

- `verify-transcript doctor --json` locates `transcript` and `uv`
- Diagnostics can read the real default Zoom directory but never write to it
- The dry run creates its meeting fixture only under the eval scratch directory

- **Diagnostics.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.zoom --json`. Require a consistent JSON report and inspect `readiness_ok`
- **Source plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature zoom.dry-run --json`. Require the disposable folder and `.m4a` path, the Codex `synthese-rencontre` summary plan, `side_effects: []`, and a planned output path that remains absent
- **Transcript-only plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature dry-runs.transcript-only --json`. Require the disposable source, disabled summary fields, a timeout override, and no output creation

## Gotchas

- The eval does not upload a private Zoom recording
- The Zoom default prompt must exist in the categorized source or flat applied `distill-prompt` skill
- `doctor --no-summary` still checks the Deepgram credential
- Scratch cleanup removes the empty Zoom fixture after evidence is written
