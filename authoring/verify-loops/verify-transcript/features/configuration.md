# Configuration

Configuration resolves source selectors, summary settings, timeouts, and output paths before transcript work starts.

## Sub-features

- `configuration.prompts` verifies prompt discovery
- `configuration.profiles` verifies the ordered profile registry and default
- `configuration.models` verifies low-level model discovery for both providers
- `interface.structured-recovery` verifies invalid configuration guidance and structured error output
- `dry-runs.transcript-only` verifies disabled summary fields and timeout overrides for both sources
- `youtube.dry-run-summary` verifies provider, model, effort, prompt, timeout, and output resolution
- `zoom.dry-run` verifies the Zoom source and its distinct summary defaults

## How to get to it (user POV)

- Run a leaf command with `--help` to see its accepted flags and defaults
- Run `transcript list profiles --json` before changing inference
- Run `transcript list prompts --json` or `transcript list models --provider <provider> --json` for low-level discovery
- Run a source with `--dry-run --json` to inspect the resolved plan

## Driving it with verify-transcript

Preconditions:

- Use the Feature Map IDs exactly
- Keep custom output under the eval-created scratch root

- **Prompt values.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature configuration.prompts --json`. Require all three bundled prompt names and input kinds
- **Profile values.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature configuration.profiles --json`. Require complete profiles with unique names, including the default and the test profile
- **Model values.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature configuration.models --json`. Require Claude, Codex, and OpenRouter defaults inside non-empty model lists
- **Recovery.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature interface.structured-recovery --json`. Require the current `transcript list models --provider codex` guidance on `stderr`
- **Transcript only.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature dry-runs.transcript-only --json`. Require disabled summary fields and the configured timeout for both sources
- **Resolved settings.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.dry-run-summary --json`. Require the configured provider, model, effort, prompt, timeout, and isolated output path
- **Zoom defaults.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature zoom.dry-run --json`. Require the Zoom folder, audio file, Claude model, effort, `synthese-rencontre` prompt, timeout, and isolated output path

## Gotchas

- The transcript CLI has no configuration file
- Credentials come from the macOS keyring or `DEEPGRAM_API_KEY` but never appear in eval evidence
- Invalid flags exit `2` before output creation or paid work
- `features[].id` contains the exact values accepted by `verify --feature`
- The verifier builds output flags itself and does not accept a transcript output override
