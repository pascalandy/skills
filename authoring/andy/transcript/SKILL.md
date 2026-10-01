---
name: "transcript"
description: "Use when the user invokes `transcript` or asks to transcribe a YouTube video or Zoom recording."
kind: "general"
---

# Transcript

Transcribe YouTube or Zoom audio with Deepgram, then optionally create a Markdown summary through a named inference profile, run by a tool-free, session-free `claude` or `pi` process.

Resolve `scripts/transcript.py` relative to this skill directory and run that absolute path with `uv run`. Give a real run a 600-second process timeout. The CLI enforces its own 570-second workflow deadline by default.

## Choose the command

```bash
# YouTube
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url>" --json

# Latest Zoom meeting
uv run <skill_dir>/scripts/transcript.py run zoom --latest --json

# Specific Zoom meeting folder
uv run <skill_dir>/scripts/transcript.py run zoom --path "<folder-name-or-full-path>" --json
```

Pass `--profile` only when the user selects a profile; `list profiles --json` marks the default.

## Manage inference through profiles

Treat every request to use, change, or add a model as a profile-management request. Do not translate the request directly into `--provider`, `--model`, or `--effort`.

First run:

```bash
uv run <skill_dir>/scripts/transcript.py list profiles --json
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

Use `--json` for discovery, dry runs, and real runs unless the user asks for a terminal preview. JSON success is one object on `stdout` and leaves `stderr` empty; warnings join it as a `warnings` list. A failure leaves `stdout` empty and writes one JSON object on `stderr`.

For an unfamiliar machine or after a preflight failure, run:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
uv run <skill_dir>/scripts/transcript.py doctor --source zoom --json
```

`doctor` checks local dependencies and credentials without calling Deepgram, a summary model, or another paid API.

Before a run with a non-default profile, prompt, output, or source setting, resolve the plan without secrets, network calls, or writes:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url>" --prompt short_summary --dry-run --json
```

Discover valid values through the command tree:

```bash
uv run <skill_dir>/scripts/transcript.py list prompts --json
uv run <skill_dir>/scripts/transcript.py list profiles --json
uv run <skill_dir>/scripts/transcript.py list models --provider claude --json
uv run <skill_dir>/scripts/transcript.py list models --provider codex --json
uv run <skill_dir>/scripts/transcript.py list models --provider openrouter --json
uv run <skill_dir>/scripts/transcript.py --help
```

Exit `2` means the invocation or source is invalid. Exit `1` means runtime work failed. Exit `75` means a temporary failure before any paid request; rerunning the same command is safe. Exits `130` and `143` mean the run was interrupted. Read the error `code`, `message`, and `hint`; the hint is the command that fixes it. Never rerun an exit `1` run automatically, because Deepgram may already have billed the audio.

Report the result folder and summary status. After a summary failure, the transcript is still published: read `output_dir` from the `stderr` JSON. Do not paste the generated summary into chat unless the user asks.

## YouTube transport check

The canonical transport fixture is:

```text
https://www.youtube.com/watch?v=EIEc43CxIvY
```

Run `uv run <skill_dir>/scripts/youtube_smoke.py` for the free transport check. The transport check requires Arc and pinned `yt-dlp` `2026.7.4`; it skips anonymous access, validates temporary audio with `ffprobe`, and never calls Deepgram or a summary model.

Arc's `Default` profile must have a valid YouTube session. If it expires, sign in again. Arc can remain open. YouTube Premium does not replace browser authentication. The normal run tries Arc, or Chrome when Arc is absent. If browser authentication fails, it retries anonymously.

## Changing this skill

Read `README.md` in this skill directory before changing code, tests, prompts, or documentation. It owns the CLI contract, runtime requirements, output formats, and validation procedure.

Always finish every `transcript` change with the README's E2E closeout. Keep Checks, Automated tests, CI, Agent QA, and E2E separate. E2E is the last gate and passes only when the relevant coded validation and Agent QA pass.
