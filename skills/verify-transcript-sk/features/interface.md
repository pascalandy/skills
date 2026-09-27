# Agent interface

The agent interface covers command discovery, exact verifier IDs, output streams, exit codes, safe planning, and the public behaviors that the verifier does not execute.

## Sub-features

- `interface.help-version` verifies the full help tree, visible options, command choices, and version output
- `interface.structured-recovery` verifies usage, source, and configuration failures as JSON on `stderr`
- `dry-runs.transcript-only` verifies `--no-summary`, timeout overrides, output isolation, and zero side effects for both sources

## How to get to it (user POV)

- Run `transcript --help` or a nested command with `--help`
- Run `transcript --version`
- Add `--json` for machine-readable discovery, diagnostics, plans, runs, and failures
- Run `verify-transcript-sk features --json` and copy an exact value from `features[].id`

## Driving it with verify-transcript-sk

Run the public-boundary checks:

- Run `uv run "$VERIFY_DIR/scripts/verify_transcript_sk.py" verify --feature interface.help-version --json`
- Run `uv run "$VERIFY_DIR/scripts/verify_transcript_sk.py" verify --feature interface.structured-recovery --json`
- Run `uv run "$VERIFY_DIR/scripts/verify_transcript_sk.py" verify --feature dry-runs.transcript-only --json`

The inventory assigns every public behavior to an executable feature or an explicit exclusion.

| Public behavior | Verifier owner or exclusion |
|---|---|
| `command.run` | `youtube.dry-run-summary`, `zoom.dry-run` |
| `command.list` | `configuration.profiles`, `configuration.prompts`, `configuration.models` |
| `command.doctor` | `diagnostics.youtube`, `diagnostics.zoom` |
| `command.youtube` | `youtube.dry-run-summary` |
| `command.zoom` | `zoom.dry-run` |
| `command.prompts` | `configuration.prompts` |
| `command.profiles` | `configuration.profiles` |
| `command.models` | `configuration.models` |
| `option.help` | `interface.help-version` |
| `option.version` | `interface.help-version` |
| `option.url` | `youtube.dry-run-summary` |
| `option.latest` | Requires reading the user's private Zoom directory |
| `option.path` | `zoom.dry-run` |
| `option.source` | `diagnostics.youtube`, `diagnostics.zoom` |
| `option.no-summary` | `dry-runs.transcript-only` |
| `option.profile` | `youtube.dry-run-summary`, `zoom.dry-run` |
| `option.provider` | `youtube.dry-run-summary` |
| `option.prompt` | `youtube.dry-run-summary` |
| `option.model` | `youtube.dry-run-summary` |
| `option.effort` | `youtube.dry-run-summary` |
| `option.output-dir` | `dry-runs.transcript-only` |
| `option.dry-run` | `dry-runs.transcript-only` |
| `option.json` | `dry-runs.transcript-only` |
| `option.timeout` | `dry-runs.transcript-only` |
| `option.open` | Would open Finder |
| `option.preview` | Would render an interactive preview |
| `option.debug` | Only changes unexpected internal-error tracebacks |
| `stream.text-stdout` | `interface.help-version` |
| `stream.success-json-stdout` | `dry-runs.transcript-only` |
| `stream.invalid-json-stderr` | `interface.structured-recovery` |
| `stream.runtime-json-stderr` | Runtime JSON failures require injected external failures and are covered by unit tests |
| `exit.success` | `interface.help-version` |
| `exit.runtime-failure` | Runtime exit paths require injected external failures and are covered by unit tests |
| `exit.invalid-input` | `interface.structured-recovery` |
| `exit.interrupted` | Requires sending a process signal and is covered by unit tests |
| `transcription.upload-completion` | `youtube.real-summary` |
| `transcription.upload-timeouts` | Slow and interrupted uploads are covered by transcript-sk TestDeepgramContract tests without paid calls |
| `publication.summary-success` | `youtube.real-summary` |
| `publication.transcript-only` | Requires a paid Deepgram call and is covered by unit tests |
| `publication.summary-failure` | Requires a forced provider failure and is covered by unit tests |
| `publication.transaction-and-collisions` | Covered by deterministic unit tests without paid work |

## Gotchas

- Help and version are text on `stdout`
- Successful JSON and diagnostic reports are on `stdout`, including an unready doctor report that exits `1`
- Fatal JSON is on `stderr` with exit `1`, `2`, or `130`
- The verifier detects a new help command or option until this inventory assigns it an owner or exclusion
- The verifier never drives `--open`, `--preview`, private Zoom media, or an unapproved paid path
