# Transcript CLI

`scripts/transcript.py` is the executable boundary for `transcript`. It transcribes YouTube videos or Zoom recordings with Deepgram and can create a Markdown summary through a named inference profile and an ephemeral, tool-free `claude` or `pi` process.

The CLI uses subcommands, validates source input before execution, returns structured output, and has a read-only `doctor` command. It never prompts for input. It follows the CLI contract in `docs/maintainer/references/script-conventions.md` of the `pascalandy/skills` repository.

## Runtime requirements

- Python 3.12+ and `uv`
- `ffmpeg` and `ffprobe` on `PATH` for YouTube
- Zoom recordings under `~/Documents/Zoom` for Zoom mode
- When summary generation is enabled, `claude` (Claude Code) on `PATH` and signed in for the default `opus` profile, or `pi` for the `astra`, `sol`, and `glm` profiles
- `glow` for optional Markdown preview; Rich is the fallback renderer
- Deepgram API key in the macOS keyring
- The `distill-prompt` skill installed beside this one for Zoom summaries, which use its `synthese-rencontre` prompt

Set the Deepgram key with:

```bash
chezmoi secret keyring set --service=deepgram --user=api_key
```

The runtime falls back to `DEEPGRAM_API_KEY` when the keyring is unavailable. It never prints the key.

The scripts pin `yt-dlp` to `2026.7.4`, the version covered by the Arc adapter and transport check.

## Commands and options

The argument parser is the only list of commands, options, defaults, and exit codes. Read it through help:

```bash
uv run <skill_dir>/scripts/transcript.py --help
uv run <skill_dir>/scripts/transcript.py help run youtube
uv run <skill_dir>/scripts/transcript.py run zoom --help
```

## Manage inference profiles

Use profiles for every normal model choice. A profile binds the provider, model, and reasoning effort into one named configuration.

```bash
uv run <skill_dir>/scripts/transcript.py list profiles --json
```

The registry lists profiles in preference order. The order does not define a fallback chain. One run selects one profile. If that inference fails, the run fails.

When a user asks to use or change a model, show `list profiles` first. Reframe the choice as selecting an existing profile, updating one, or creating one. Add or change profiles in the `INFERENCE_PROFILES` registry in `scripts/transcript.py`; no other file lists them.

Use the low-level `--provider`, `--model`, and `--effort` flags only to diagnose or test a custom target.

The `claude` provider runs `claude --print` with no tools, MCP servers, hooks, slash commands, saved session, settings files, or `CLAUDE.md`. Hooks from an administrator's managed settings still run, because no command-line option disables them. The transcript's `@` characters reach Claude as the JSON escape `\u0040`, so an `@path` in a transcript cannot attach a local file. The profile's effort overrides any `CLAUDE_CODE_EFFORT_LEVEL`. Claude accepts only the efforts `low`, `medium`, `high`, `xhigh`, and `max`; the CLI rejects any other level, which Claude Code would silently replace with its default. The `codex` and `openrouter` providers run through `pi`.

## Run commands

A YouTube run rejects an invalid URL before reading credentials, starting network work, or creating an output directory.

For Zoom, `--path` accepts a folder name under `~/Documents/Zoom` or a full folder path. It rejects an audio-file path. The CLI resolves the folder and verifies that it contains an `.m4a` file before reading credentials or creating output.

Finder and preview are opt-in. A normal run has no GUI side effect and does not render the generated Markdown.

## Discovery and diagnostics

Discovery never reads credentials or starts network work. `doctor` checks local requirements without paid API calls:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
```

Checks have `pass`, `warn`, or `fail` status. A healthy report goes to `stdout`; a report with a failed check goes to `stderr` and exits `1`. It never contains the Deepgram credential.

For a run with changed source or summary settings, inspect the plan first with `--dry-run --json`. Dry-run source validation is real and read-only. It checks a YouTube URL or resolves Zoom media, but it does not read secrets, call an API, or create files.

## Output and JSON

`stdout` holds the result only: the published folder path, discovery values, or the dry run's output parent. A failure leaves `stdout` empty.

`stderr` stays empty on success unless a warning needs action, such as browser access falling back to anonymous. `-v` adds the run plan and one line per step; `--debug` adds child commands, timings, and tracebacks. On a terminal, each step shows a spinner that leaves nothing behind; `--no-progress`, `--no-color`, `NO_COLOR`, or `TERM=dumb` turn it off.

With `--json`, success is one JSON object on `stdout`, and warnings join it as a `warnings` list. A failure is one JSON object on `stderr` with `ok: false` and an `error` object holding `code`, `message`, and `hint`. The hint is the command that fixes the error. With `-v` or `--debug`, their lines come first, and the JSON object still ends `stderr`.

A successful run payload includes:

```json
{
  "ok": true,
  "command": "run",
  "source": "youtube",
  "output_dir": "/absolute/result/path",
  "summary": {
    "status": "succeeded",
    "profile": "opus",
    "provider": "claude",
    "model": "claude-opus-5-5",
    "effort": "high",
    "error": null
  },
  "artifacts": {
    "transcript": "/absolute/result/path/raw_transcript.txt",
    "sentences": "/absolute/result/path/raw_sentences.txt",
    "json": "/absolute/result/path/raw_transcript.json",
    "metadata": "/absolute/result/path/meta.txt",
    "summary": "/absolute/result/path/follow_along_note.md"
  }
}
```

A summary failure still publishes the raw artifacts and records the reason in metadata. The run exits `1` with the same payload, plus its `error`, on `stderr`, so the published folder stays findable.

Exit `75` means a temporary failure before any paid request, such as a network error reaching YouTube or Deepgram refusing the audio; rerunning the same command is safe. A failure after the Deepgram upload started exits `1`, because Deepgram may have transcribed, and billed, the audio.

## Safety and reruns

Input and configuration validation run before credentials, paid APIs, or output writes. Publication uses a hidden adjacent staging directory and one final rename. A publication failure removes staging. YouTube temporary audio is always removed.

Deepgram upload failures are not replayed automatically because the service may have accepted the request before the client timed out. Follow the returned hint instead of blindly retrying.

Audio uploads use 64 KiB blocks and declare the full file size with `Content-Length`. The CLI checks the sent byte count before accepting a successful response. With `-v`, human output reports `Audio upload complete` before waiting for the transcription response. This confirms that the client sent every block; publication still requires a valid Deepgram transcription. Published metadata records `Audio upload: complete (N bytes)`, which `verify-transcript` checks and retains in its evidence.

The 300-second write timeout applies to each block, so a slow upload can take more than 300 seconds while making progress. The workflow budget is checked between blocks. A stalled upload reports a lower bound on the bytes sent because its last block may have been partially transmitted. A timeout after the upload started returns `transcription_timeout`; its hint reruns the command with twice the `--timeout`.

For a slow connection or a long recording, allow more than the default workflow deadline for downloading, uploading, transcription, and summarization:

```bash
just ttr "https://www.youtube.com/watch?v=VIDEO_ID" --timeout 20m
```

Concurrent uploads share the available bandwidth. Run them sequentially when the connection is slow.

A successful repeated command creates a new result folder. This preserves prior artifacts but means a full run is intentionally not idempotent. Use `--dry-run` for plan verification and do not replay a timed-out run until its output location has been checked.

## Output files

Each YouTube run creates a timestamped folder containing:

- `{prompt}.md` when summary generation succeeds
- `raw_transcript.txt`
- `raw_sentences.txt`
- `raw_transcript.json`
- `meta.txt`

Each Zoom run creates one meeting folder under the output parent. The name removes `Réunion Zoom de`:

```text
2026-05-03 14.46.55 Réunion Zoom de Camille Exemple
becomes
2026-05-03 14.46.55 Camille Exemple
```

The Zoom files use the folder name as their base:

```text
{base}/
├── {base}.md
├── {base}.raw_transcript.txt
├── {base}.raw_sentences.txt
├── {base}.raw_transcript.json
└── {base}.meta.txt
```

The Markdown file exists only after successful summary generation. Name collisions receive `-2`, `-3`, and later suffixes. Metadata records summary status. YouTube metadata also records the successful audio method as `anonymous`, `arc`, or `chrome`.

## YouTube transport

Normal YouTube runs try browser authentication first. When Arc's `~/Library/Application Support/Arc/User Data/Default` profile exists, a bounded adapter changes only yt-dlp's in-memory keyring name to `Arc`. Otherwise the CLI uses Chrome's Default profile. If browser authentication fails, it retries anonymously and warns on `stderr`, or in the `warnings` list under `--json`.

Arc's `Default` profile must have a valid YouTube session. If the session expires, sign in again to YouTube in Arc. Arc can remain open. YouTube Premium does not replace browser authentication. The script does not export cookies or modify Arc, Chrome, or Keychain.

The canonical transport check fixture is:

```text
https://www.youtube.com/watch?v=EIEc43CxIvY
```

Run the free transport check:

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

The transport check requires Arc. It skips anonymous access, downloads temporary audio, validates the stream with `ffprobe`, and removes the download. A pass prints nothing and exits `0`; `-v` reports each step, and a network failure exits `75`. It never calls Deepgram or a summary model. A pass proves the Arc adapter ran. It does not prove the full user flow.

## Validation model

Use these evidence names consistently:

- **Checks** verify a narrow coded contract such as syntax, discovery output, or authenticated media transport
- **Automated tests** exercise Python behavior through pytest, usually with external boundaries mocked
- **CI** runs its configured checks and automated tests; it performs no Agent QA
- **Agent QA** exercises the real terminal command and inspects its visible output and saved artifacts
- **E2E** combines the relevant coded validation with Agent QA across the real pipeline

Passing Checks, Automated tests, or CI alone never proves E2E. Always finish every `transcript` change, including documentation and test changes, with the E2E closeout below.

## Checks

Run syntax and discovery checks:

```bash
uv run python -m py_compile <skill_dir>/scripts/transcript.py
uv run <skill_dir>/scripts/transcript.py --help
uv run <skill_dir>/scripts/transcript.py run youtube --help
uv run <skill_dir>/scripts/transcript.py run zoom --help
uv run <skill_dir>/scripts/transcript.py list prompts --json
uv run <skill_dir>/scripts/transcript.py list profiles --json
uv run <skill_dir>/scripts/transcript.py list models --provider claude --json
uv run <skill_dir>/scripts/transcript.py list models --provider codex --json
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
```

Run the free authenticated transport check:

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

## Automated tests

```bash
just check --only transcript
```

The suite mocks external boundaries. It proves the coded CLI and pipeline contracts, not Agent QA or E2E.

## CI

`just check` runs the same repository checks and automated tests as GitHub Actions. Report CI as `NOT RUN` unless the relevant CI workflow itself ran.

## Mandatory E2E closeout

Always perform this section last after any change to `transcript`. Save complete pseudo-terminal logs outside the export folders.

Run the canonical YouTube Agent QA path:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube \
  --url "https://www.youtube.com/watch?v=EIEc43CxIvY" \
  --prompt short_summary \
  --output-dir <temporary-dir> \
  --json
```

When the change affects Zoom, also run the relevant real Zoom path:

```bash
uv run <skill_dir>/scripts/transcript.py run zoom --latest --json
uv run <skill_dir>/scripts/transcript.py run zoom \
  --path "2026-05-03 14.46.55 Réunion Zoom de Camille Exemple" \
  --json
```

Before deciding E2E:

- confirm each pseudo-terminal log is complete and not truncated
- read every log from start to finish
- classify every `failed`, `error`, `warning`, `skipped`, `timeout`, `unavailable`, and `traceback` line
- verify the exit code and JSON document agree with `meta.txt` and every listed artifact
- confirm a `--json` success left `stderr` empty
- confirm default success has no summary preview and does not open Finder
- confirm YouTube creates one folder under the chosen output parent
- confirm Zoom creates one meeting folder under the chosen output parent when Zoom changed
- confirm the relevant Checks and Automated tests passed

Report the categories separately:

```text
Checks: PASS | FAIL | NOT RUN
Automated tests: PASS | FAIL | NOT RUN
CI: PASS | FAIL | NOT RUN
Agent QA: PASS | FAIL | NOT RUN
E2E: PASS | FAIL | NOT RUN
```

E2E passes only when the relevant coded validation and Agent QA pass. If a prerequisite cannot run, report E2E as `NOT RUN` or `FAIL` and do not report the change complete.
