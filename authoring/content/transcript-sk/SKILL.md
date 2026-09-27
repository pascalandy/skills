---
name: "transcript-sk"
description: "Use when the user mentions `transcript-sk` or asks to transcribe a YouTube video or Zoom recording."
---

# Transcript

Transcribe YouTube or Zoom audio with Deepgram, then optionally create a Markdown summary through a named inference profile and Pi's tool-free, session-free mode.

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

The default profile is `astra`. Use `--profile sol` or `--profile glm` only when the user selects that profile.

## Manage inference through profiles

Treat every request to use, change, or add a model as a profile-management request. Do not translate the request directly into `--provider`, `--model`, or `--effort`.

First run:

```bash
uv run <skill_dir>/scripts/transcript.py list profiles --json
```

Show the current profile names, providers, models, and efforts. Then ask whether the user wants to select an existing profile, update one, or create one. If the user already named a profile, show its configuration and use `--profile <name>`.

The built-in profiles are:

| Profile | Provider | Model | Effort |
|---|---|---|---|
| `astra` | `codex` | `gpt-6-astra` | `low` |
| `sol` | `codex` | `gpt-5.6-sol` | `medium` |
| `glm` | `openrouter` | `z-ai/glm-5.3-flash` | `medium` |

The order records preference only. The CLI runs one profile and never falls back to another profile.

To update or create a profile, edit the `INFERENCE_PROFILES` registry in `scripts/transcript.py`, update this table and `README.md`, then run the validation procedure in `README.md`.

For Zoom, `--path` names the meeting folder, not its `audio*.m4a` file. A plain folder name resolves under `~/Documents/Zoom`.

Use these options only when the request calls for them:

- `--no-summary` saves transcript artifacts without an AI summary
- `--profile NAME` selects a complete inference configuration
- `--provider`, `--model`, and `--effort` form an advanced custom target and must be supplied together; use them only for diagnostics
- `--prompt` overrides the summary prompt
- `--output-dir DIR` changes the parent directory for the result folder
- `--preview` renders the saved summary and cannot be combined with `--json`
- `--open` opens Finder after publication; the default has no GUI side effect
- `--timeout SECONDS` changes the workflow deadline

YouTube defaults to `follow_along_note` and the `astra` profile. Zoom uses `distill-prompt/references/synthese-rencontre/prompt.md` and the same profile.

## Agent operation

Use `--json` for discovery, dry runs, and real runs unless the user asks for a terminal preview. JSON success output is one document on `stdout`; progress stays on `stderr`.

For an unfamiliar machine or after a preflight failure, run:

```bash
uv run <skill_dir>/scripts/transcript.py doctor --source youtube --json
uv run <skill_dir>/scripts/transcript.py doctor --source zoom --json
```

`doctor` checks local dependencies and credentials without calling Deepgram, Pi, or another paid API.

Before a run with a non-default profile, prompt, output, or source setting, resolve the plan without secrets, network calls, or writes:

```bash
uv run <skill_dir>/scripts/transcript.py run youtube --url "<youtube-url>" --prompt short_summary --dry-run --json
```

Discover valid values through the command tree:

```bash
uv run <skill_dir>/scripts/transcript.py list prompts --json
uv run <skill_dir>/scripts/transcript.py list profiles --json
uv run <skill_dir>/scripts/transcript.py list models --provider codex --json
uv run <skill_dir>/scripts/transcript.py list models --provider openrouter --json
uv run <skill_dir>/scripts/transcript.py --help
```

Exit `2` means the invocation or source is invalid. Exit `1` means runtime work failed. Read the error `code`, `message`, and `hint`; use `doctor` when the hint names it. Exit `130` means the user interrupted the run.

Report the result folder and summary status. Do not paste the generated summary into chat unless the user asks.

## YouTube transport check

The canonical transport fixture is:

```text
https://www.youtube.com/watch?v=EIEc43CxIvY
```

Run `uv run <skill_dir>/scripts/youtube_smoke.py` for the free transport check. The transport check requires Arc and pinned `yt-dlp` `2026.7.4`; it skips anonymous access, validates temporary audio with `ffprobe`, and never calls Deepgram or Pi.

Arc's `Default` profile must have a valid YouTube session. If it expires, sign in again. Arc can remain open. YouTube Premium does not replace browser authentication. The normal run tries Arc, or Chrome when Arc is absent. If browser authentication fails, it retries anonymously.

## Changing this skill

Read `README.md` in this skill directory before changing code, tests, prompts, or documentation. It owns the CLI contract, runtime requirements, output formats, and validation procedure.

Always finish every `transcript-sk` change with the README's E2E closeout. Keep Checks, Automated tests, CI, Agent QA, and E2E separate. E2E is the last gate and passes only when the relevant coded validation and Agent QA pass.
