---
description: "Apply a named distill prompt to a local text file and save the result in a timestamped folder beside it."
---

# distill

> Apply named distill prompt to local text file. Output lands in timestamped folder beside input

---

## Routing

Load `references/distill/ROUTER.md` to determine which sub-skill handles this req.

---

## The Problem

There is good prompt library (`distill-prompt`) and two capable LLM CLIs (`claude`, `codex`), but no thin tool tying them to local files. Users now either:

- Go through YouTube transcription skill first (wrong tool for local file)
- Hand-craft shell pipeline with cat, right effort flag, and right model
- Copy-paste prompt text into LLM chat

None is repeatable, versioned, or friction-free.

- **Prompts are reusable, workflows are not** -- same prompt goes through 3 ad-hoc pipelines
- **Vendor flag differences** -- `claude` and `codex` agree on `low`/`medium`/`high` but diverge at top (`max` vs `xhigh`); users should not track that
- **No canonical output location** -- results scatter across Downloads, Desktop, clipboard

Fundamental issue: applying distill prompt to local file should be one cmd, not workflow.

---

## The Solution

`distill` is a thin CLI (`distill.py`) that takes a local text file and prompt stem, resolves that prompt from the `distill-prompt` route, runs the chosen LLM, and writes output to a timestamped folder beside the source. It's file-only in v1 -- URL and media inputs are out of scope. The `references/distill/from-file/` directory keeps room for future `from-url` and `from-media` sub-skills without renaming `distill`.

**Core capabilities:**

1. **Thin wrapper** -- reads input file, resolves prompt stem, calls LLM, writes output
2. **Canonical effort vocabulary** -- users type `low|medium|high|max`; script translates to per-vendor values internally
3. **Provider-agnostic** -- `--provider claude` or `--provider codex`, same interface
4. **Context-size pre-flight** -- fails fast with clear error if input exceeds safe limit (600k tokens for Claude, 450k for Codex)
5. **Glow-rendered help** -- `--help` reads `references/distill/help.md` so rich markdown help is version-controlled
6. **Output lives next to source** -- timestamped folder `{slug}_{timestamp}_{prompt}/` beside input file

---

## Workflow

1. **Pick prompt.** Read the `distill-prompt` playbook to choose the prompt that fits the user's need. Use that prompt's stem with `--prompt`
2. **Read CLI help.** Resolve `scripts/distill/distill.py` from the andy-mode directory and run `--help` to see flags, defaults, and exit codes:
   ```
   uv run <skill_dir>/scripts/distill/distill.py --help
   ```
3. **Invoke with chosen prompt:**
    ```
    uv run <skill_dir>/scripts/distill/distill.py \
        ~/Documents/article.md \
        --prompt follow_along_note
    ```
4. **Output lands beside input:**
    ```
    ~/Documents/article_2026-04-06_14-32-08_follow_along_note/
    ├── article_follow_along_note.md  # the distilled result
    ├── article_raw.md                # a copy of the original input file
    └── article_meta.yml              # YAML run metadata (provider, model, effort, duration, tokens)
    ```
    The command answers `{"ok":true,"file":"<path>"}`; read the distilled result from that path. A failure leaves stdout empty and ends stderr with `{"ok":false,"errors":[…]}`

For dry-run, alternate providers, or custom output locations, read `references/distill/help.md` via `--help`.

---

## What's Included

| Component | Path | Purpose |
|-----------|------|---------|
| Router | `references/distill/ROUTER.md` | Routes req patterns to right input sub-skill |
| from-file sub-skill | `references/distill/from-file/MetaSkill.md` | Docs for local-file input path (v1 default) |
| CLI help | `references/distill/help.md` | Full user-facing CLI help, rendered by `--help` via glow |
| Script | `scripts/distill/distill.py` | PEP 723 single-file Python script |

**Summary:**
- **Input sub-skills:** 1 (from-file)
- **Scripts:** 1 (distill.py)
- **Dependencies:** `distill-prompt` (prompt library), `claude` or `codex` CLI, `uv` runtime, `tiktoken` (auto-installed by uv), optional `glow` for rich help rendering

---

## Invocation Scenarios

| Trigger | What Happens |
|---------|--------------|
| "distill my article.md" | Routes to from-file -- runs distill.py on file with default prompt (`follow_along_note`) |
| "summarize this file with short-summary" | Routes to from-file -- uses the `distill-prompt` route to choose `short_summary`, then passes it via `--prompt` |
| "distill with codex max effort" | Routes to from-file -- same flow with `--provider codex --effort max` |
| "what distill options exist" | Run `distill.py --help` to see full flag reference |
| URL or YouTube link | Out of scope in v1. Use `$transcript` for YouTube. |

---

## Configuration

No config required. Defaults cover common case:

- Provider: `claude`
- Model: `claude-opus-4-6`
- Effort: `medium`
- Output: beside input file
- Open in Finder when done (macOS)

All defaults are overridable via flags. See `references/distill/help.md` via `--help`.

---

## Related Work

- **`distill-prompt`** -- the prompt library route `distill` reads from
- **`transcript`** -- separate YouTube and Zoom transcription workflow. YouTube uses bundled prompts; Zoom summaries use `synthese-rencontre` from `distill-prompt`

---

## What This Skill Does NOT Do

| Out of Scope | Why |
|---|---|
| URL input | Deferred. `distill` remains a meta-skill so `from-url` can be added later without renaming. |
| Media input (audio/video) | Deferred. `from-media` is future sub-skill. |
| Stdin / piped input | v1 accepts file paths only. |
| Batch input (`distill *.md`) | Single input per invocation. Use shell loops for batching. |
| Inline prompt text flag | Use prompt library. Add folder in `distill-prompt` for new prompts. |
| Prompt chaining | Run `distill` twice with intermediate files. |
