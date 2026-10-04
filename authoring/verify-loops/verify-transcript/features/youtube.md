# YouTube

YouTube mode validates a public video URL, resolves a summary plan, attempts a browser-authenticated download before an anonymous fallback, transcribes audio with Deepgram, and can summarize it through `claude` or `pi`.

## Sub-features

- `diagnostics.youtube` checks YouTube prerequisites without paid calls
- `interface.structured-recovery` checks invalid YouTube sources and configuration without paid calls
- `dry-runs.transcript-only` resolves a YouTube plan with summary generation disabled
- `youtube.dry-run-summary` resolves the canonical URL and summary configuration without network calls or writes
- `youtube.real-summary` transcribes and summarizes the canonical public fixture through the public CLI and verifies completed audio upload metadata

## How to get to it (user POV)

- Run `transcript run youtube --url <URL> --json`
- Add `--dry-run` to inspect the plan without downloading or transcribing
- Add `--profile` or `--prompt` to change summary settings

## Driving it with verify-transcript

Preconditions:

- `verify-transcript doctor --json` locates `transcript` and `uv`
- A real run has a valid Deepgram credential, pinned yt-dlp, `ffmpeg`, `ffprobe`, and a signed-in `claude` for the default summary profile
- A local session on a Mac whose Arc is signed in to YouTube, as the transcript README's `Test videos` rule requires

- **Free plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.dry-run-summary --json`. Require exit `0`, `side_effects: []`, the canonical URL, the configured summary plan, and a planned output path that remains absent
- **Transcript-only plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature dry-runs.transcript-only --json`. Require the canonical URL, disabled summary fields, a timeout override, and no output creation
- **Recovery.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature interface.structured-recovery --json`. Require invalid source and configuration errors on `stderr`
- **Diagnostics.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature diagnostics.youtube --json`. Require a consistent JSON report and inspect `readiness_ok`
- **Real flow.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.real-summary --allow-paid --json`. Require a `PASS` verdict, five non-empty artifacts, a successful summary, consistent metadata, and retained hashes. Require `Audio upload: complete (N bytes)` in `meta.txt` with positive `N` and matching `audio_upload` evidence containing `status: complete` and `bytes: N` in the artifact manifest and observations

## Gotchas

- A YouTube dry run validates URL shape, not video availability
- `--no-summary` still calls paid Deepgram transcription
- `--allow-paid` alone selects no paid feature
- An expired browser session falls back to anonymous access. The run fails if both download methods fail or YouTube removes the video
- Full transcript and summary content is removed with scratch after its hashes and sizes are recorded
- Upload completion means the client sent the full payload; publication also requires a valid Deepgram response
- A real success does not exercise slow or interrupted uploads. Run the deterministic upload verification loop in [SKILL.md](../SKILL.md) for those cases
