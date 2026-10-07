---
name: distill-from-file
description: Distill a local text file by running distill.py with a chosen prompt stem. USE WHEN the input is a file path on disk (article, transcript, markdown, plain text) and the user wants to apply a named distill prompt to it.
---

# distill from-file

> Apply a distill prompt to a local text file. Output lands in a timestamped folder beside the input.

## When to Use

- The user has a local file (`.md`, `.txt`, or any plain-text document) and wants it distilled
- A prompt from the `distill-prompt` route has already been chosen (or the agent picks one)
- The user has `claude` or `codex` CLI installed

Do **not** use this for YouTube URLs -- use `$transcript` instead. URL and media inputs are deferred to future sub-skills.

## Prerequisites

- `uv` (Python runtime/package manager)
- `claude` or `codex` CLI in `$PATH`
- A prompt choice from `distill-prompt`
- Optional: `glow` for rich `--help` rendering

## Basic Invocation

Resolve `../../../scripts/distill/distill.py` relative to this sub-skill directory (`dirname MetaSkill.md`) and run that absolute path.

```bash
uv run <sub_skill_dir>/../../../scripts/distill/distill.py \
    <input-file> \
    --prompt <prompt-stem>
```

Everything else defaults sensibly (claude provider, opus model, medium effort, output beside input, open Finder on macOS).

## Reading the Full CLI Reference

Instead of duplicating flag documentation here, run:

```bash
uv run <sub_skill_dir>/../../../scripts/distill/distill.py --help
```

This renders `references/distill/help.md` via `glow` (or plain markdown fallback) and covers:

- All flags and defaults
- Effort ETL (canonical → vendor values)
- Context size limits per provider
- Exit codes
- Dry-run behavior
- `--list-models` output format

## Common Variations

| Intent | Command |
|---|---|
| Default (claude + follow-along-note style) | `distill.py file.md --prompt follow_along_note` |
| Short summary with codex | `distill.py file.md --prompt short_summary --provider codex` |
| Maximum reasoning effort | `distill.py file.md --prompt follow_along_note --effort max` |
| Custom output directory | `distill.py file.md --prompt follow_along_note --output-dir ~/Desktop/runs` |
| Check flags without running | `distill.py file.md --prompt short_summary --dry-run` |

Available prompt stems come from `distill-prompt`. Common values are:
`follow_along_note`, `short_summary`, and `summary_with_quotes`.

## Output Shape

```
<input-parent>/{slug}_{YYYY-MM-DD_HH-MM-SS}_{prompt}/
├── {slug}_{prompt}.md  # distilled result
├── {slug}_raw.{ext}    # copy of the original input file (same extension as input)
└── {slug}_meta.yml     # YAML run metadata (provider, model, effort, duration, tokens, original file path)
```

The slug is the input filename stem. The prompt name is the normalized prompt stem.

The command answers `{"ok":true,"file":"<path>"}` with the path of `{slug}_{prompt}.md`; read the distilled result from there.

## Error Paths

A failure leaves stdout empty and ends stderr with `{"ok":false,"errors":[…]}`, whose message names the problem. Run `--help` for the full exit-code map. Common failures:

- **Exit 3** -- input file missing or unreadable. Check the path.
- **Exit 4** -- unknown prompt stem. Run `--list-prompts` and choose one of the available values.
- **Exit 5** -- `claude` or `codex` CLI not in `$PATH`. Install the provider CLI.
- **Exit 6** -- LLM call failed or context size exceeded. Check file length; the limit is 600k tokens for Claude and 450k for Codex.
- **Exit 7** -- output parent directory not writable. Use `--output-dir` to pick a writable location.
