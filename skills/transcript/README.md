# Transcript CLI

`scripts/transcript.py` is the executable boundary for `transcript`. It transcribes YouTube videos or Zoom recordings with Deepgram and can create a Markdown summary through a named inference profile and an ephemeral, tool-free `claude` or `pi` process.

The CLI uses subcommands, validates source input before execution, answers each command in one JSON line, and has a read-only `doctor` command. It never prompts for input. It follows the CLI contract in `docs/references/script-conventions.md` of the `pascalandy/skills` repository.

## Runtime requirements

- Python 3.12+ and `uv`
- `ffmpeg` and `ffprobe` on `PATH` for YouTube
- Zoom recordings under `~/Documents/Zoom` for Zoom mode
- When summary generation is enabled, `claude` (Claude Code) on `PATH` and signed in for the default `opus` profile and the `sonnet` test profile, or `pi` for the `astra`, `sol`, and `glm` profiles
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
uv run <skill_dir>/scripts/transcript.py list profiles
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

`--url` takes several YouTube URLs, so one terminal shows every video's status. `just ttr` passes every URL it receives:

```bash
just ttr "https://www.youtube.com/watch?v=VIDEO_A" "https://www.youtube.com/watch?v=VIDEO_B"
```

The recipe puts its own `--url` first. A `--url` with no value adds no URL, so `just ttr --url URL_A --url URL_B` and `just ttr --profile sonnet --url URL_A` work too.

The queue runs one URL at a time, so uploads never share bandwidth.

- Before any work, it checks every URL, and one invalid URL exits `2` with nothing run. It checks the summary CLI and reads the Deepgram key once, and each URL gets its own `--timeout` budget and result folder
- A repeated video runs once, which `-v` reports. The queue compares video IDs, so `youtu.be/ID` and `watch?v=ID&t=30` never bill the same audio twice
- On a terminal, the spinner names the URL's place, as in `[2/4] Deepgram transcription...`, and so do the `-v` and `--debug` lines
- Each result folder prints on `stderr` as soon as it appears, before Deepgram starts
- A failed URL prints `[2/4] error:` on `stderr`, with its own fix, and the queue moves on. A result that cannot be saved, such as on a full disk, stops the queue instead, because every later URL would fail to save the same way
- After the last URL, the answer's `errors` name each failed URL with its fix, then `1 of 4 URLs failed; 3 saved a transcript` and a command that reruns only the failed or unrun URLs. That command keeps a repair they share, such as a longer `--timeout`
- The run exits `75` only when no URL saved a transcript and every failure came before any paid request, so rerunning the same command is safe. Any other failure exits `1`
- An interrupt stops the queue once the current URL is cleaned up. Its answer lists the files of the finished URLs and a command that reruns the URLs that did not finish

Several URLs always run as a queue, even when they name one video. Its answer lists the files of every URL, in URL order; see [Output](#output). A dry run lists the queue as `source.urls`.

## Discovery and diagnostics

Discovery never reads credentials or starts network work. `doctor` checks local requirements without paid API calls:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube
```

Each check has a `pass`, `warn`, or `fail` status, which `-v` lists. Each failed check is one error with its fix, and exits `1`. A `warn` check, such as a missing `pi`, needs nothing for the default profile, so it never fails `doctor`. No output contains the Deepgram credential.

For a run with changed source or summary settings, inspect the plan first with `--dry-run`. Dry-run source validation is real and read-only. It checks a YouTube URL or resolves Zoom media, but it does not read secrets, call an API, or create files.

## Output

Every command answers in one JSON line, as `docs/references/script-output.md` of the `pascalandy/skills` repository describes. Success is `{"ok":true,…}` on `stdout` with exit `0`. A failure leaves `stdout` empty, ends `stderr` with `{"ok":false,"errors":[…]}`, and exits non-zero. Each error says what failed, then the command that fixes it after `fix:`, `retry:`, or `rerun:`; a usage error without one adds `help`, the help command of the command it came from. `--help` and `--version` stay text.

- A run answers the `files` it saved, in the order they appeared; the folder holding them is the result folder
- `list` answers its values, such as `profiles` and their `default`
- A dry run answers its plan: `source`, `summary`, `output_dir`, and `timeout_seconds`
- `doctor` answers `{"ok":true}`, or one error per failed check

While a run works, `stderr` shows each result folder as soon as it appears, before Deepgram starts, so the path is usable at once. Nothing else reaches `stderr` by default. `-v` adds the run plan, one line per step, and what needs no action, such as browser access falling back to anonymous; `--debug` adds child commands, timings, and tracebacks. On a terminal, each step shows a spinner that leaves nothing behind; `--no-progress`, `--no-color`, `NO_COLOR`, or `TERM=dumb` turn it off. `--preview` renders the summary on `stderr` too.

A successful run answers:

```json
{"ok":true,"files":["/absolute/result/path/meta.txt","/absolute/result/path/raw_transcript.txt","/absolute/result/path/raw_sentences.txt","/absolute/result/path/raw_transcript.json","/absolute/result/path/follow_along_note.md"]}
```

A failure after the result folder appears keeps the folder, and its metadata records the failed stage and the reason. The answer still lists the `files` saved, so the folder stays findable. A summary failure exits `1` and lists the raw transcript files, because they are saved.

Exit `75` means a temporary failure before any paid request, such as a network error reaching YouTube or Deepgram refusing the audio; rerunning the same command is safe. A failure after the Deepgram upload started exits `1`, because Deepgram may have transcribed, and billed, the audio.

## Safety and reruns

Input and configuration validation run before credentials, paid APIs, or output writes. The result folder appears once the audio is ready, before Deepgram starts. Each file in it is written through a hidden temporary file and one rename, so a reader never sees a partial file. YouTube temporary audio is always removed.

Deepgram upload failures are not replayed automatically because the service may have accepted the request before the client timed out. Follow the command its error names instead of blindly retrying.

Audio uploads use 64 KiB blocks and declare the full file size with `Content-Length`. The CLI checks the sent byte count before accepting a successful response. With `-v`, human output reports `Audio upload complete` before waiting for the transcription response. This confirms that the client sent every block; saving the transcript still requires a valid Deepgram transcription. The metadata of a saved transcript records `Audio upload: complete (N bytes)`, which `verify-transcript` checks and retains in its evidence.

The 300-second write timeout applies to each block, so a slow upload can take more than 300 seconds while making progress. The workflow budget is checked between blocks. A stalled upload reports a lower bound on the bytes sent because its last block may have been partially transmitted. A timeout after the upload started fails with an error whose fix reruns the command with twice the `--timeout`.

For a slow connection or a long recording, allow more than the default workflow deadline for downloading, uploading, transcription, and summarization:

```bash
just ttr "https://www.youtube.com/watch?v=VIDEO_ID" --timeout 20m
```

For several videos, use [Queue several videos](#queue-several-videos).

Each run creates a new result folder, and a failed run keeps its own, so a rerun never touches an earlier result. A full run is intentionally not idempotent. Use `--dry-run` for plan verification and do not replay a timed-out run until its metadata shows how far it got.

## Output files

Each YouTube run creates a timestamped folder. Its files appear in this order:

- `meta.txt`, with the folder
- `raw_transcript.txt`, `raw_sentences.txt`, and `raw_transcript.json`, once Deepgram answers
- `{prompt}.md`, when summary generation succeeds

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

Zoom files appear in the same order. Name collisions receive `-2`, `-3`, and later suffixes.

The metadata holds the title, date, and source from the moment the folder appears. Each stage rewrites it, so it always shows how far the run got:

- `Transcript status`: `in progress`, `complete`, `failed`, or `interrupted`
- `Summary status`: `pending`, `running`, `succeeded`, `failed`, `skipped`, `not started`, or `interrupted`

YouTube metadata also records the audio method that worked: `anonymous`, `arc`, or `chrome`.

## YouTube transport

Normal YouTube runs try browser authentication first. When Arc's `~/Library/Application Support/Arc/User Data/Default` profile exists, a bounded adapter changes only yt-dlp's in-memory keyring name to `Arc`. Otherwise the CLI uses Chrome's Default profile. If browser authentication fails, it retries anonymously, which `-v` reports and the metadata records.

One yt-dlp call reads the video's title and ID and downloads its best native audio stream at 64 kbps or less, or its best audio when none is that small. Deepgram receives that file as is, with no transcode.

Arc's `Default` profile must have a valid YouTube session. If the session expires, sign in again to YouTube in Arc. Arc can remain open. YouTube Premium does not replace browser authentication. The script does not export cookies or modify Arc, Chrome, or Keychain.

Run the free transport check on the canonical video from [Test videos](#test-videos):

```bash
uv run <skill_dir>/scripts/youtube_smoke.py
```

The transport check requires Arc. It skips anonymous access, downloads temporary audio, validates the stream with `ffprobe`, and removes the download. A pass answers `{"ok":true}`; `-v` reports each step, and a network failure exits `75`. It never calls Deepgram or a summary model. A pass proves the Arc adapter ran. It does not prove the full user flow.

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

Every real test run passes `--profile sonnet`: Claude Sonnet 5.5 at `medium` effort. A test only needs a summary to come back, so the default `opus` profile adds cost and nothing else.

Pascal pre-authorizes every paid test run that follows this rule: a video from this table and `--profile sonnet`. The rule covers the E2E closeout and the `youtube.real-summary` feature of `verify-transcript`, so run them without asking. A new row needs his go-ahead before it counts, and so does any other paid run: a URL outside the table, such as a `--youtube-url` override, another profile, or a hint that switches the profile after a failed summary.

Run a paid test from a local session on a Mac whose Arc is signed in to YouTube, such as mbp. Over SSH, the macOS Keychain keeps Arc's cookies out of reach and yt-dlp reports `find-generic-password failed`, and Linux has no Arc profile. Both fall back to anonymous access, which YouTube usually refuses. From SSH or Linux, hand the closeout commands to a local Mac session.

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
uv run <skill_dir>/scripts/transcript.py list prompts
uv run <skill_dir>/scripts/transcript.py list profiles
uv run <skill_dir>/scripts/transcript.py list models --provider claude
uv run <skill_dir>/scripts/transcript.py list models --provider codex
uv run <skill_dir>/scripts/transcript.py doctor --source youtube
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
  --profile sonnet \
  --prompt short_summary \
  --output-dir <temporary-dir>
```

When a change touches the queue, also run both [test videos](#test-videos) as one queue in a pseudo-terminal, so the spinner shows:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube \
  --url "https://www.youtube.com/watch?v=EIEc43CxIvY" "https://www.youtube.com/watch?v=QwpTAk_IiyU" \
  --profile sonnet \
  --prompt short_summary \
  --output-dir <temporary-dir>
```

A real Zoom run is not part of the closeout for now, even when a change affects Zoom: Pascal does not use Zoom. Zoom mode stays supported, and its coverage is the automated tests plus the free `zoom.dry-run` and `diagnostics.zoom` features of `verify-transcript`. Report Zoom E2E as `NOT RUN`. To exercise Zoom anyway, run:

```bash
uv run <skill_dir>/scripts/transcript.py run zoom --latest --profile sonnet
uv run <skill_dir>/scripts/transcript.py run zoom \
  --path "2026-05-03 14.46.55 Réunion Zoom de Camille Exemple" \
  --profile sonnet
```

Before deciding E2E:

- confirm each pseudo-terminal log is complete and not truncated
- read every log from start to finish
- classify every `failed`, `error`, `warning`, `skipped`, `timeout`, `unavailable`, and `traceback` line
- verify the exit code and the answer agree with `meta.txt` and every listed file
- confirm a success left only the result folder on `stderr`
- confirm default success has no summary preview and does not open Finder
- confirm YouTube creates one folder per URL under the chosen output parent
- for a queue, confirm `stderr` showed the folders, and the answer lists their files, in URL order, and the spinner named `[1/2]` and `[2/2]` and left nothing behind
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
