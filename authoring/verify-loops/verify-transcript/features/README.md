# Transcript verification map

This directory maps the public behavior of `transcript` to exact `verify-transcript` commands and observable proof. Run `verify_transcript.py features <query>` to get selectable IDs in `features[].id` and matching pages in `documents[]`.

## Baseline preconditions

- Resolve `verify_transcript.py` relative to the `verify-transcript` skill directory
- Run `verify_transcript.py doctor` when layout discovery or local tools look wrong
- Use the default free verification before a paid feature
- For paid checks, follow the transcript README's `Test videos` rule

## Driving conventions

- Drive only the public `transcript.py` subprocess
- Read the one JSON line transcript answers with for stable assertions
- Pass every transcript run an eval-owned `--output-dir`
- Treat `readiness_ok: false` as a machine-readiness observation when the diagnostic contract itself passes
- Keep paid checks sequential

## Proof and skip reporting

- Require the eval command's exit code, verdict, and `result.json` to agree
- Read captured `stdout.txt`, `stderr.txt`, `parsed.json`, and `process.json` for failed cases
- Verify source actions and resulting artifacts, not only the final JSON field
- Report a paid feature as not run unless the exact paid feature and `--allow-paid` were supplied
- Keep retained evidence after scratch cleanup
- For `youtube.real-summary`, require `Audio upload: complete (N bytes)` in `meta.txt` with positive `N`, retained as `audio_upload` in the artifact manifest and observations
- Use the upload verification loop in [SKILL.md](../SKILL.md) for slow or interrupted uploads; the paid fixture proves successful completion only

## Feature entry contract

Each feature page contains exactly four H2 sections in this order.

1. `Sub-features`
2. `How to get to it (user POV)`
3. `Driving it with verify-transcript`
4. `Gotchas`

The verifier registry owns executable feature IDs and paid classification. The public-surface inventory assigns every command, option group, stream rule, exit rule, and publication state to a feature or an explicit exclusion. Tests check both mappings.

## Features

- [Agent interface](./interface.md) covers help, version, exact verifier IDs, structured recovery, streams, exits, and deliberate exclusions
- [YouTube](./youtube.md) covers URL planning, diagnostics, and the real transcription plus summary flow
- [Zoom](./zoom.md) covers local meeting selection, diagnostics, and isolated dry runs
- [Summaries](./summaries.md) covers profile and prompt discovery, summary configuration, and real summary output
- [Configuration](./configuration.md) covers profiles, low-level targets, prompts, sources, timeouts, and output resolution
- [Diagnostics](./diagnostics.md) covers structured readiness reports and exit consistency
- [Dry runs](./dry-runs.md) covers source validation, zero side effects, and output isolation
