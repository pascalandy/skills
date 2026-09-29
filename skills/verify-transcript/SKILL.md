---
name: "verify-transcript"
description: "Use when validating transcript CLI behavior or locating its verification features. Use for paid YouTube end-to-end checks only when explicitly authorized."
---

# Verify transcript

Drive `transcript` only through `scripts/transcript.py`. The verifier finds that public CLI in either the categorized `authoring/` source layout or the flat applied skill layout.

## Launch

This is a short-lived CLI. It does not start a server or retain a process.

```bash
VERIFY_DIR="<verify-transcript-skill-dir>"
uv run "$VERIFY_DIR/scripts/verify_transcript.py" --help
```

Resolve `VERIFY_DIR` from this skill's directory. Do not depend on the caller's working directory.

## Doctor

Check the verifier before a run when the layout or local tools look wrong.

```bash
uv run "$VERIFY_DIR/scripts/verify_transcript.py" doctor --json
```

`doctor` checks `uv`, all seven Feature Map pages, and the adjacent `transcript` public script. It does not call Deepgram, a summary model, YouTube, or Zoom.

## Drive

Run all free checks with one command.

```bash
uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --json
```

The default run covers help and version output, structured recovery, transcript-only planning, discovery, configuration, diagnostics, YouTube dry-run planning, and Zoom source and summary planning. A valid diagnostic response can pass even when the machine is not ready. Read each diagnostic feature's `readiness_ok` observation.

Search the Feature Map before a focused check. Copy exact selectable values from `features[].id`. Matching Markdown pages are in `documents[]`.

```bash
uv run "$VERIFY_DIR/scripts/verify_transcript.py" features zoom --json
uv run "$VERIFY_DIR/scripts/verify_transcript.py" features --json
```

Read [features/README.md](features/README.md) for the index. Each feature page names its public command, expected state, and proof.

Run a paid end-to-end check only when the user has explicitly authorized paid transcription and summary calls.

```bash
uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify \
  --feature youtube.real-summary \
  --allow-paid \
  --json
```

Paid work requires both the paid feature ID and `--allow-paid`. The flag alone does not select paid work. `--all` also selects the paid feature and therefore requires `--allow-paid`.

## Evidence

Every verification returns a `verdict` and `evidence_dir`. The default evidence root remains `${XDG_STATE_HOME:-~/.local/state}/eval-transcript/runs`. Runs retained before the skill rename stay in the same history.

Each case retains:

- The exact public command with no secret values
- Captured `stdout`, `stderr`, exit code, duration, and normalized parsed output
- The feature verdict and observations
- An artifact manifest with names, sizes, and SHA-256 hashes for the paid flow

The final `result.json` records the selected layout, aggregate counts, paid authorization, and cleanup result. A successful paid check records the artifact manifest before cleanup. A failed paid check retains its command and process evidence, then cleanup removes any scratch output.

## Cleanup

The verifier creates one marked directory under the system temporary directory. A `finally` block removes that directory after success, failure, timeout, or interruption.

Cleanup refuses a path outside the system temporary directory, a name without the current run ID, or a directory without the current marker. Cleanup never receives the evidence path. Retained evidence survives every normal teardown.

Do not delete evidence as part of verification. If the user asks to remove old evidence, inspect the exact run directories first and use a recoverable deletion method.

## Helpers

After changing Deepgram uploads, run this bounded verification loop:

1. Run the verifier doctor above and set `TRANSCRIPT_DIR` to the skill directory reported by its `transcript_skill` check, whether source or applied
2. Run the upload contract tests below, then the verifier helper tests
3. Run the default free verification and inspect its verdict and evidence
4. If the user explicitly authorized paid calls, run the existing `youtube.real-summary` feature above and require its `audio_upload` evidence

```bash
uv run --with pytest --with httpx --with rich pytest \
  "$TRANSCRIPT_DIR/scripts/tests/test_transcript.py" -k TestDeepgramContract -q
```

These deterministic tests check bounded upload chunks, intact audio, rejection of success before the full payload is sent, timeout byte reporting, and the workflow deadline. A successful real run alone does not prove behavior on a slow or interrupted connection.

Run the focused helper tests after changing this verifier.

```bash
uv run --with pytest pytest "$VERIFY_DIR/scripts/tests" -q
```

The tests cover layout discovery, exact feature discovery, public-surface ownership, output streams, paid selection, command confinement, process capture, cleanup, Feature Map coverage, and artifact validation. They stub external paid boundaries. The paid command above is the real end-to-end proof.
