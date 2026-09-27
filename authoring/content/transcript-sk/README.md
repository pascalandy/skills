# Transcript CLI

`scripts/transcript.py` is the executable boundary for `transcript-sk`. It transcribes YouTube videos or Zoom recordings with Deepgram and can create a Markdown summary through a named inference profile and an ephemeral, tool-free Pi process.

The v3 CLI uses subcommands, validates source input before execution, returns structured output, and has a read-only `doctor` command. It never prompts for input.

## Runtime requirements

- Python 3.12+ and `uv`
- `ffmpeg` and `ffprobe` on `PATH` for YouTube
- Zoom recordings under `~/Documents/Zoom` for Zoom mode
- `pi` on `PATH` when summary generation is enabled
- `glow` for optional Markdown preview; Rich is the fallback renderer
- Deepgram API key in the macOS keyring

Set the Deepgram key with:

```bash
chezmoi secret keyring set --service=deepgram --user=api_key
```

The runtime falls back to `DEEPGRAM_API_KEY` when the keyring is unavailable. It never prints the key.

The scripts pin `yt-dlp` to `2026.7.4`, the version covered by the Arc adapter and transport check.

## Command tree

```text
transcript
├── run
│   ├── youtube --url URL
│   └── zoom (--latest | --path PATH)
├── list
│   ├── profiles
│   ├── prompts
│   └── models --provider PROVIDER
└── doctor
```

Every command and nested command supports `-h` and `--help`. Top-level help lists only commands. Leaf help owns flags, defaults, and examples.

Use the script through `uv`:

```bash
uv run <skill_dir>/scripts/transcript.py --help
uv run <skill_dir>/scripts/transcript.py run youtube --help
uv run <skill_dir>/scripts/transcript.py run zoom --help
```

`--version` prints `transcript 3.1.0` to `stdout`.

## Manage inference profiles

Use profiles for every normal model choice. A profile binds the provider, model, and reasoning effort into one named configuration.

```bash
uv run <skill_dir>/scripts/transcript.py list profiles
uv run <skill_dir>/scripts/transcript.py list profiles --json
```

The registry defines these profiles in preference order:

| Profile | Provider | Model | Effort | Use |
|---|---|---|---|---|
| `astra` | `codex` | `gpt-6-astra` | `low` | Default |
| `sol` | `codex` | `gpt-5.6-sol` | `medium` | Second choice |
| `glm` | `openrouter` | `z-ai/glm-5.3-flash` | `medium` | Third choice |

The order does not define a fallback chain. One run selects one profile. If that inference fails, the run fails.

When a user asks to use or change a model, show `list profiles` first. Reframe the choice as selecting an existing profile, updating one, or creating one. Add or change profiles in the `INFERENCE_PROFILES` registry in `scripts/transcript.py`. Keep this table and `SKILL.md` synchronized with the registry.

Use the low-level `--provider`, `--model`, and `--effort` flags only to diagnose or test a custom target. Supply all three flags together. Do not combine them with `--profile`.

## Run commands

### YouTube

```bash
uv run <skill_dir>/scripts/transcript.py run youtube \
  --url "https://youtu.be/dQw4w9WgXcQ"
```

Defaults:

- prompt `follow_along_note`
- profile `astra`
- provider `codex`
- model `gpt-6-astra`
- effort `low`
- output parent `~/Documents/_my_docs/61_transcription_exports_yt`

The CLI rejects an invalid URL before reading credentials, starting network work, or creating an output directory.

### Zoom

Use the latest meeting folder containing an `.m4a` file:

```bash
uv run <skill_dir>/scripts/transcript.py run zoom --latest
```

Use a specific meeting folder:

```bash
uv run <skill_dir>/scripts/transcript.py run zoom \
  --path "2026-05-03 14.46.55 Réunion Zoom de Camille Exemple"
```

`--path` accepts a folder name under `~/Documents/Zoom` or a full folder path. It rejects an audio-file path. The CLI resolves the folder and verifies that it contains an `.m4a` file before reading credentials or creating output.

Defaults:

- prompt `distill-prompt/references/synthese-rencontre/prompt.md`
- profile `astra`
- provider `codex`
- model `gpt-6-astra`
- effort `low`
- output parent `~/Desktop/Travail/Mandats`

### Shared run flags

| Flag | Contract |
|---|---|
| `--no-summary` | Save the transcript artifacts and skip Pi |
| `--profile {astra,sol,glm}` | Select a complete inference profile |
| `--prompt NAME` | Select a bundled prompt name |
| `--provider {codex,openrouter}` | Set an advanced custom target with `--model` and `--effort` |
| `--model MODEL` | Set an advanced custom target with `--provider` and `--effort` |
| `--effort LEVEL` | Set an advanced custom target with `--provider` and `--model` |
| `--output-dir DIR` | Change the parent directory for the result folder |
| `--preview` | Render the saved summary after publication |
| `--open` | Open the published result folder in Finder |
| `--dry-run` | Resolve the plan without secrets, network calls, or writes |
| `--json` | Return one JSON document on `stdout` |
| `--timeout SECONDS` | Override the 570-second workflow deadline |
| `--debug` | Show a traceback for an unexpected internal error |

`--no-summary` cannot be combined with summary flags or `--preview`. `--profile` cannot be combined with a custom target. `--json` cannot be combined with `--preview` because both own `stdout`.

Finder and preview are opt-in. A normal run has no GUI side effect and does not render the generated Markdown.

## Discovery and diagnostics

Discovery never reads credentials or starts network work:

```bash
uv run <skill_dir>/scripts/transcript.py list prompts
uv run <skill_dir>/scripts/transcript.py list prompts --json
uv run <skill_dir>/scripts/transcript.py list profiles --json
uv run <skill_dir>/scripts/transcript.py list models --provider codex --json
uv run <skill_dir>/scripts/transcript.py list models --provider openrouter --json
```

`doctor` checks local requirements without paid API calls:

```bash
uv run <skill_dir>/scripts/transcript.py doctor
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
uv run <skill_dir>/scripts/transcript.py doctor --source zoom --no-summary --json
```

Checks have `pass`, `warn`, or `fail` status. `doctor` exits `1` when any required check fails. Its report never contains the Deepgram credential.

For a run with changed source or summary settings, inspect the plan first:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube \
  --url "https://youtu.be/dQw4w9WgXcQ" \
  --profile glm \
  --prompt short_summary \
  --dry-run \
  --json
```

Dry-run source validation is real and read-only. It checks a YouTube URL or resolves Zoom media, but it does not read secrets, call an API, or create files.

## I/O and JSON contract

Human mode writes the published result path or discovery values to `stdout`. Configuration, progress, warnings, retries, and errors go to `stderr`.

Interactive `stderr` uses a live spinner. Redirected `stderr` emits deterministic `Starting ...` and `Completed ... in 0.0s` lines without terminal control sequences. Summary generation adds a whole-second counter only in an interactive terminal.

With `--json`, successful discovery, doctor, dry-run, and run output is one JSON document on `stdout`. Routine progress is suppressed. A fatal failure writes one JSON error document to `stderr`, so neither stream requires stripping human progress lines.

A successful run payload includes:

```json
{
  "ok": true,
  "command": "run",
  "source": "youtube",
  "output_dir": "/absolute/result/path",
  "summary": {
    "status": "succeeded",
    "profile": "astra",
    "provider": "codex",
    "model": "gpt-6-astra",
    "effort": "low",
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

Usage and runtime errors under `--json` contain `ok: false` and an `error` object with `code`, `message`, and `hint`. A summary failure publishes the valid raw artifacts, returns a run payload with `ok: false`, records the reason in metadata, and exits `1`.

Exit codes:

| Code | Meaning |
|---|---|
| `0` | Success, help, version, discovery, doctor with no failures, or dry-run |
| `1` | Runtime, summary, publication, or doctor failure |
| `2` | Invalid command, flag, configuration, URL, or Zoom source |
| `130` | User interruption |

Expected failures do not print tracebacks. Use `--debug` or `DEBUG=1` only when diagnosing an unexpected internal error.

## Safety and reruns

Input and configuration validation run before credentials, paid APIs, or output writes. Publication uses a hidden adjacent staging directory and one final rename. A publication failure removes staging. YouTube temporary audio is always removed.

Deepgram upload failures are not replayed automatically because the service may have accepted the request before the client timed out. Follow the returned hint instead of blindly retrying.

Audio uploads use 64 KiB blocks and declare the full file size with `Content-Length`. The CLI checks the sent byte count before accepting a successful response. Human output reports `Audio upload complete` before waiting for the transcription response. This confirms that the client sent every block; publication still requires a valid Deepgram transcription. Published metadata records `Audio upload: complete (N bytes)`, which `verify-transcript-sk` checks and retains in its evidence.

The 300-second write timeout applies to each block, so a slow upload can take more than 300 seconds while making progress. The workflow budget is checked between blocks. A stalled upload reports a lower bound on the bytes sent because its last block may have been partially transmitted. Upload and workflow timeouts return `transcription_timeout` with a network-specific hint.

For a slow connection or a long recording, allow more than the default 570 seconds for downloading, uploading, transcription, and summarization:

```bash
just ttr "https://www.youtube.com/watch?v=VIDEO_ID" --timeout 1200
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

Normal YouTube runs try browser authentication first. When Arc's `~/Library/Application Support/Arc/User Data/Default` profile exists, a bounded adapter changes only yt-dlp's in-memory keyring name to `Arc`. Otherwise the CLI uses Chrome's Default profile. If browser authentication fails, it retries anonymously and reports the fallback on `stderr`.

Arc's `Default` profile must have a valid YouTube session. If the session expires, sign in again to YouTube in Arc. Arc can remain open. YouTube Premium does not replace browser authentication. The script does not export cookies or modify Arc, Chrome, or Keychain.

The canonical transport check fixture is:

```text
https://www.youtube.com/watch?v=EIEc43CxIvY
```

Run the free transport check:

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

The transport check requires Arc. It skips anonymous access, downloads temporary audio, validates the stream with `ffprobe`, and removes the download. It never calls Deepgram, Pi, Codex, or OpenRouter. A pass proves the Arc adapter ran. It does not prove the full user flow.

## Validation model

Use these evidence names consistently:

- **Checks** verify a narrow coded contract such as syntax, discovery output, or authenticated media transport
- **Automated tests** exercise Python behavior through pytest, usually with external boundaries mocked
- **CI** runs its configured checks and automated tests; it performs no Agent QA
- **Agent QA** exercises the real terminal command and inspects its visible output and saved artifacts
- **E2E** combines the relevant coded validation with Agent QA across the real pipeline

Passing Checks, Automated tests, or CI alone never proves E2E. Always finish every `transcript-sk` change, including documentation and test changes, with the E2E closeout below.

## Checks

Run syntax and discovery checks:

```bash
uv run python -m py_compile <skill_dir>/scripts/transcript.py
uv run <skill_dir>/scripts/transcript.py --help
uv run <skill_dir>/scripts/transcript.py run youtube --help
uv run <skill_dir>/scripts/transcript.py run zoom --help
uv run <skill_dir>/scripts/transcript.py list prompts --json
uv run <skill_dir>/scripts/transcript.py list profiles --json
uv run <skill_dir>/scripts/transcript.py list models --provider codex --json
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
```

Run the free authenticated transport check:

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

## Automated tests

```bash
just check --only transcript-sk
```

The suite mocks external boundaries. It proves the coded CLI and pipeline contracts, not Agent QA or E2E.

## CI

`just check` runs the same repository checks and automated tests as GitHub Actions. Report CI as `NOT RUN` unless the relevant CI workflow itself ran.

## Mandatory E2E closeout

Always perform this section last after any change to `transcript-sk`. Save complete pseudo-terminal logs outside the export folders.

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
