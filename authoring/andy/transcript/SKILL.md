---
name: "transcript"
description: "Use when the user invokes `transcript` or asks to transcribe a YouTube video or Zoom recording."
kind: "general"
configuration-is-needed: true
api-key: "deepgram"
---

# Transcript

Transcribe YouTube or Zoom audio with Deepgram, then optionally create a Markdown summary through a named inference profile, run by a tool-free, session-free `claude` or `pi` process.

Resolve `scripts/transcript.py` relative to this skill directory and run that absolute path with `uv run`. Allow a 600-second process timeout for a real run, multiplied by the input URL count for a queue.

## Choose the command

```bash
# YouTube
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url>"

# YouTube queue
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url-a>" "<youtube-url-b>"

# Latest Zoom meeting
uv run <skill_dir>/scripts/transcript.py run zoom --latest

# Specific Zoom meeting folder
uv run <skill_dir>/scripts/transcript.py run zoom --path "<folder-name-or-full-path>"
```

Pass `--profile` only when the user selects a profile; `list profiles` marks the default.

## Manage inference through profiles

Treat every request to use, change, or add a model as a profile-management request. Do not translate the request directly into `--provider`, `--model`, or `--effort`.

First run:

```bash
uv run <skill_dir>/scripts/transcript.py list profiles
```

Show the current profile names, providers, models, and efforts. Then ask whether the user wants to select an existing profile, update one, or create one. If the user already named a profile, show its configuration and use `--profile <name>`.

The list order records preference only. The CLI runs one profile and never falls back to another profile.

To update or create a profile, edit the `INFERENCE_PROFILES` registry in `scripts/transcript.py`, the only list of profiles, then run the validation procedure in `README.md`.

For Zoom, `--path` names the meeting folder, not its `audio*.m4a` file. A plain folder name resolves under `~/Documents/Zoom`.

`help run youtube` and `help run zoom` list every run option and its default. Add an option only when the request calls for it. `--provider`, `--model`, and `--effort` form an advanced custom target for diagnostics only. `--open` and `--preview` are opt-in, so a normal run has no GUI side effect.

## Change a prompt

Each YouTube prompt is a Markdown file in `references/prompts/`, and its file name without `.md` is the `--prompt` value. Edit a file there to change a prompt, or add a `.md` file to create one; `list prompts` shows it. In a managed installation, edit the source package, because the next install overwrites installed copies.

Only `summary_with_quotes` receives the timestamped transcript; every other prompt receives plain text. Zoom summaries use the `synthese-rencontre` prompt from andy-mode's `distill-prompt` route.

## Agent operation

Every command answers in one JSON line. Success is `{"ok":true,…}` on `stdout`: a run lists the `files` it saved, `list` its values, and a dry run its plan. A failure leaves `stdout` empty and ends `stderr` with `{"ok":false,"errors":[…]}`. While a run works, `stderr` shows each result folder as soon as it appears.

For an unfamiliar machine or after a preflight failure, run:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube
uv run <skill_dir>/scripts/transcript.py doctor --source zoom
```

`doctor` checks local dependencies and credentials without calling Deepgram, a summary model, or another paid API.

Before a run with a non-default profile, prompt, output, or source setting, resolve the plan without secrets, network calls, or writes:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url>" --prompt short_summary --dry-run
```

Discover valid values through the command tree:

```bash
uv run <skill_dir>/scripts/transcript.py list prompts
uv run <skill_dir>/scripts/transcript.py list profiles
uv run <skill_dir>/scripts/transcript.py list models --provider claude
uv run <skill_dir>/scripts/transcript.py list models --provider codex
uv run <skill_dir>/scripts/transcript.py list models --provider openrouter
uv run <skill_dir>/scripts/transcript.py --help
```

Exit `2` means the invocation or source is invalid. Exit `1` means runtime work failed. Exit `75` means a temporary failure before any paid request; rerunning the same command is safe. Exits `130` and `143` mean the run was interrupted. Each error ends with the command that fixes it, after `fix:`, `retry:`, or `rerun:`; a usage error without one adds a `help` command instead. Never rerun an exit `1` run automatically, because Deepgram may already have billed the audio.

Report the result folder, the one holding the `files`, and whether a summary `.md` is among them. A failure after the folder appears keeps it, and its answer still lists the `files` saved, including the metadata that names the failed stage. A run with several URLs lists the files of each URL, and its `errors` name each failed URL before a command that reruns only those. Do not paste the generated summary into chat unless the user asks.

## YouTube transport check

Run `uv run <skill_dir>/scripts/youtube_smoke.py` for the free transport check on `https://www.youtube.com/watch?v=EIEc43CxIvY` from the README's `Test videos` table. The transport check requires Arc and pinned `yt-dlp` `2026.7.4`. It validates temporary audio with `ffprobe` and never calls Deepgram or a summary model.

Arc's `Default` profile must have a valid YouTube session. If it expires, sign in again. Arc can remain open. YouTube Premium does not replace browser authentication. The normal run tries Arc, or Chrome when Arc is absent. If browser authentication fails, it retries anonymously.

## Changing this skill

Read `README.md` in this skill directory before changing code, tests, prompts, or documentation. It owns the CLI contract, runtime requirements, output formats, and validation procedure.

Always finish every `transcript` change with the README's E2E closeout. Its `Test videos` rule pre-authorizes the paid runs with `--profile sonnet`, so run the closeout without asking. Keep Checks, Automated tests, CI, Agent QA, and E2E separate. E2E is the last gate and passes only when the relevant coded validation and Agent QA pass.
