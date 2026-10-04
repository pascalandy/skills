# Transcript CLI

`scripts/transcript.py` is the executable boundary for `transcript`. It transcribes YouTube videos or Zoom recordings with Deepgram and can create a Markdown summary through a named inference profile and an ephemeral, tool-free `claude` or `pi` process.

The CLI uses subcommands, validates source input before execution, returns structured output, and has a read-only `doctor` command. It never prompts for input. It follows the CLI contract in `docs/references/script-conventions.md` of the `pascalandy/skills` repository.

## Runtime requirements

- Python 3.12+ and `uv`
- `ffmpeg` and `ffprobe` on `PATH` for YouTube
- Zoom recordings under `~/Documents/Zoom` for Zoom mode
- When summary generation is enabled, `claude` (Claude Code) on `PATH` and signed in for the default `opus` profile, or `pi` for the `astra`, `sol`, and `glm` profiles
- `glow` for optional Markdown preview; Rich is the fallback renderer
- Deepgram API key in the macOS keyring
- The `andy-mode` skill installed beside this one for Zoom summaries, which use the `synthese-rencontre` prompt of its `distill-prompt` route

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

## Queue several videos

`--url` takes several YouTube URLs, and it can repeat. `just ttr` passes every URL it receives:

```bash
just ttr "https://www.youtube.com/watch?v=VIDEO_A" "https://www.youtube.com/watch?v=VIDEO_B"
```

A queue runs one URL at a time, so uploads never share bandwidth.

- Before any work, the queue checks every URL. One invalid URL exits `2`, and nothing runs
- It checks the summary CLI and reads the Deepgram key once, then gives each URL its own `--timeout` budget and its own result folder
- A repeated video runs once, with a warning, so Deepgram never bills the same audio twice. The queue compares video IDs, so `youtu.be/ID` and `watch?v=ID&t=30` count as one video
- On a terminal, the spinner names the URL's place, as in `[2/4] Deepgram transcription...`. Lines from `-v` and `--debug` carry the same prefix
- Each result folder prints on `stdout` as soon as it is published, even when a later URL fails. A URL whose summary failed still prints its transcript folder, so paid results are never hidden
- A failed URL prints `[2/4] error:` and its own fix on `stderr`, and the queue moves on. After the last URL, `error: 1 of 4 URLs failed; 3 published a result folder` ends `stderr`, followed by a command that reruns only the failed URLs. That command keeps a repair they share, such as a longer `--timeout`
- A failed publication, such as a full disk or an unwritable `--output-dir`, stops the queue. Every later URL would bill Deepgram, then fail the same way
- The run exits `75` only when every URL failed before any paid request, so rerunning the same command is safe. Any other failure exits `1`
- An interrupt stops the queue once the current URL is cleaned up. Under `--json`, its error object lists the finished URLs, and its hint reruns the URLs that did not finish
- `--preview` takes one URL, because each summary would print between the result paths

Several URLs always give the queue output, even when they name one video. With `--json`, the queue prints one object after the last URL: `ok`, `command`, `source`, and `results`. Each entry of `results` is the single-run payload from [Output and JSON](#output-and-json), or its failure object, plus the entry's `url`.

When a URL fails, the object goes to `stderr` with `ok: false` and the error code `queue_failed`. A dry run lists the queue as `source.urls`.

## Discovery and diagnostics

Discovery never reads credentials or starts network work. `doctor` checks local requirements without paid API calls:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
```

Checks have `pass`, `warn`, or `fail` status. A healthy report goes to `stdout`; a report with a failed check goes to `stderr` and exits `1`. It never contains the Deepgram credential.

For a run with changed source or summary settings, inspect the plan first with `--dry-run --json`. Dry-run source validation is real and read-only. It checks a YouTube URL or resolves Zoom media, but it does not read secrets, call an API, or create files.

## Output and JSON

`stdout` holds the result only: the published folder path, discovery values, or the dry run's output parent. A failure leaves `stdout` empty, except that a queue keeps the folders it published before the failure.

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

Concurrent runs share the available bandwidth. Queue the URLs in one run instead, as in [Queue several videos](#queue-several-videos), which uploads one at a time.

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

Run the free transport check on the canonical video from [Test videos](#test-videos):

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

The transport check requires Arc. It skips anonymous access, downloads temporary audio, validates the stream with `ffprobe`, and removes the download. A pass prints nothing and exits `0`; `-v` reports each step, and a network failure exits `75`. It never calls Deepgram or a summary model. A pass proves the Arc adapter ran. It does not prove the full user flow.

## Test videos

Real test runs use these short, public videos from Framework's official channel to limit Deepgram cost and summary wait time:

| Video | Length | Use |
|---|---|---|
| `https://www.youtube.com/watch?v=EIEc43CxIvY` | 4 min 57 s | Canonical video: the transport check, `verify-transcript`, and the E2E closeout |
| `https://www.youtube.com/watch?v=QwpTAk_IiyU` | 2 min 36 s | Second video, for a test that needs two different videos |

To test with another video, pick a public one under 5 minutes, read its length without downloading it, then add its row here:

```bash
uvx yt-dlp@2026.7.4 --skip-download --print duration "<youtube-url>"
```

The length prints in seconds.

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

When a change touches the queue, also run both [test videos](#test-videos) as one queue in a pseudo-terminal, without `--json`, so the spinner shows:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube \
  --url "https://www.youtube.com/watch?v=EIEc43CxIvY" "https://www.youtube.com/watch?v=QwpTAk_IiyU" \
  --prompt short_summary \
  --output-dir <temporary-dir>
```

A real Zoom run is not part of the closeout for now, even when a change affects Zoom: Pascal does not use Zoom. Zoom mode stays supported, and its coverage is the automated tests plus the free `zoom.dry-run` and `diagnostics.zoom` features of `verify-transcript`. Report Zoom E2E as `NOT RUN`. To exercise Zoom anyway, run:

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
- confirm YouTube creates one folder per URL under the chosen output parent
- for a queue, confirm `stdout` lists the folders in URL order and the spinner named `[1/2]` and `[2/2]` and left nothing behind
- confirm Zoom creates one meeting folder under the chosen output parent when a real Zoom run was made
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
