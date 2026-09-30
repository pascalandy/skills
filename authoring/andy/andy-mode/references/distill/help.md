# distill

Distill a local text file through a named prompt using Claude, Codex, or OpenCode.

## Synopsis

```text
distill.py <input> [options]
distill.py --list-prompts
distill.py --list-models [--provider PROVIDER]
distill.py --help
distill.py --version
```

## Description

`distill` reads a local text file, resolves a prompt name from the `distill-prompt` route, runs it against your chosen LLM provider, and writes the result to a timestamped output folder.

This v1 scope is file-only. `distill` remains a meta-skill so URL and media flows can be added later without changing its name.

## Positional arguments

**`input`**
Local file path. Required unless using `--list-prompts`, `--list-models`, `--help`, or `--version`.

## Options

### Prompt selection

**`--prompt STEM`** - default: `follow_along_note`
Distill prompt to apply. STEM matches a folder in andy-mode's `references/distill-prompt/` directory. Underscores and hyphens both accepted. Use `--list-prompts` to see all available prompts.

### Provider & model

**`--provider {claude,codex,opencode}`** - default: `claude`
LLM backend to use.

**`--model MODEL`**
Specific model name. Defaults depend on provider:
- claude -> `claude-opus-4-6`
- codex -> `gpt-5.4`
- opencode -> `1-glm`

Available Claude models: `claude-opus-4-6`, `claude-sonnet-4-6`

Available OpenCode agents: `1-glm`, `2-luna`, `3-sol`, `4-astra`, `5-qwen`

Use `--list-models` to see all supported values.

**`--effort {low,medium,high,max}`** - default: `high` (or `low` for Sonnet models)
Reasoning effort. Canonical vocabulary; the script translates per provider:

| Canonical | Claude | Codex |
|---|---|---|
| `low` | `low` | `low` |
| `medium` | `medium` | `medium` |
| `high` | `high` | `high` |
| `max` | `max` | `xhigh` |

**Note:** `claude-sonnet-4-6` defaults to `low` effort for faster, more economical results. Opus defaults to `high`.

**OpenCode note:** `--effort` is not supported with `--provider opencode`. OpenCode reasoning behavior is defined by the selected curated agent.

### Output

**`--output-dir DIR`**
Parent folder for the timestamped run folder. Default: parent directory of the input file.

**`--no-open`**
Do not open the output folder in Finder when done (macOS only).

### Discovery

**`--list-prompts`**
List every prompt available in the distill-prompt library and exit.

**`--list-models`**
List supported models and exit. Combine with `--provider` to filter.

### Behavior

**`--dry-run`**
Resolve all inputs, check dependencies, and print the plan without calling the LLM or writing files.

**`-q, --quiet`**
Suppress progress output. Only errors and the final output path are printed.

**`-h, --help`**
Show this help message and exit.

**`--version`**
Show program version and exit.

## Defaults

| Setting | Default value |
|---|---|
| Prompt | `follow_along_note` |
| Provider | `claude` |
| Model (claude) | `claude-opus-4-6` |
| Model (codex) | `gpt-5.4` |
| Model (opencode) | `1-glm` |
| Effort | `high` (or `low` for Sonnet models) |
| Output dir | parent directory of the input file |
| Run folder name | `{slug}_{timestamp}_{prompt}/` |
| Timestamp format | `YYYY-MM-DD_HH-MM-SS` |
| Open in Finder when done | yes (macOS only) |

## Output

Each run creates a timestamped folder named:

```text
{slug}_{timestamp}_{prompt}/
```

The folder contains:

- **`{slug}_{prompt}.md`** - the distilled output
- **`{slug}_raw.{ext}`** - a copy of the original input file (same extension as input)
- **`{slug}_meta.yml`** - run metadata in YAML format (timestamp, provider, model, effort, duration)

### Default output location

The output folder is created alongside the input file:

```text
~/Documents/article.md
~/Documents/article_2026-04-06_14-32-08_follow_along_note/
```

Override with `--output-dir`.

## Examples

**Local file, default prompt:**
```bash
distill ~/Documents/article.md
```

**Local file with specific prompt:**
```bash
distill --prompt short_summary ~/notes.txt
```

**Use codex with specific model and effort:**
```bash
distill --provider codex --model gpt-5.4 --effort max ./meeting.md
```

**Use OpenCode with the default curated agent:**
```bash
distill --provider opencode ~/Documents/article.md
```

**See what prompts exist:**
```bash
distill --list-prompts
```

**See claude models only:**
```bash
distill --list-models --provider claude
```

**Verify flags without running:**
```bash
distill --dry-run --prompt summary_with_quotes ~/Documents/article.md
```

## E2E tests

**opencode**
```bash
uv run <skill_dir>/scripts/distill.py --provider opencode --prompt short_summary ~/Documents/_my_docs/62_distill_exports/raw_transcript.txt
```

**claude**
```bash
uv run <skill_dir>/scripts/distill.py --provider claude --prompt short_summary ~/Documents/_my_docs/62_distill_exports/raw_transcript.txt
```

## See also

- `distill-prompt` - the prompt library route
- `transcript` - separate YouTube and Zoom workflow. YouTube uses bundled prompts; Zoom summaries use `synthese-rencontre` from `distill-prompt`
