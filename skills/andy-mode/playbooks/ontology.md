# Ontology Map

> Corpus-agnostic ontology generator. Given a directory, produces a fixed 5-file ontology: `INDEX.md`, `concepts.md`, `systems.md`, `questions.md`, `connections.md`. Works on wikis, docs trees, lecture notes, book chapters, or any folder of text. The skill owns output end-to-end; users do not hand-edit these files.

---

## Routing

Load `references/ontology/ROUTER.md` to determine which sub-skill handles this request.

For the output contract, cache format, signal detection, and hard rules, read `references/ontology/SCHEMA.md`.

> **Reading principle:** Agents should read progressively -- only load sub-skill `MetaSkill.md` files when the routing decision lands there. Do not preload all workflows.

---

## The Problem

When a caller asks for an ontology, plain folder listing is not enough. The next agent cannot tell which files define core concepts, which cluster into systems, or what the corpus is implicitly *missing*. An ontology layer solves that -- but ontology layers that live inside a wiki tool leak wiki conventions into every non-wiki caller.

The `ontology` route pulls the ontology layer into its own route. It reads any directory, detects signals when they exist (frontmatter, wikilinks), and always produces the same 5-file output so the next caller -- human or AI, wiki host or bare folder -- can orient fast.

---

## The Solution

Point the `ontology` route at a directory. It:

1. Walks the input recursively (markdown/text files only).
2. Mines every file once, caching results by `mtime + size` so refreshes only re-mine what changed.
3. Writes exactly five files to the output directory:
   - `INDEX.md` -- routes to the other four, records input, corpus metrics, last refresh, cache status.
   - `concepts.md` -- core ideas + one-line definitions + relative-path sources.
   - `systems.md` -- named clusters of files forming a system.
   - `questions.md` -- gaps the corpus implies but does not answer.
   - `connections.md` -- typed relations between files (empty-state note if none typed).

Three operations cover every scenario:

1. **Create** -- no ontology exists in the output dir. Runs the full pipeline.
2. **Update** -- an `INDEX.md` already exists in the output dir. Cache-aware refresh; `--force` ignores cache and regenerates everything.
3. **Check** -- inspect corpus metrics, cache state, and last refresh without writing.

The skill writes only; drift detection, linting, and post-processing belong to the host (e.g. `wiki-map` flags hand-edits after the `ontology` route returns).

---

## What's Included

| Component | Path | Purpose |
|-----------|------|---------|
| Router | `references/ontology/ROUTER.md` | Create / Update / Check dispatch |
| Schema | `references/ontology/SCHEMA.md` | 5-file output contract, cache, signals, hard rules |
| Create | `references/ontology/Create/MetaSkill.md` | First-time generation workflow |
| Update | `references/ontology/Update/MetaSkill.md` | Cache-aware refresh workflow |
| Check | `references/ontology/Check/MetaSkill.md` | Status inspection (no writes) |
| Mine | `references/ontology/Mine/MetaSkill.md` | Internal per-file extraction, shared by Create and Update |

**Summary:**
- **Sub-skills:** 3 user-facing (Create, Update, Check) + 1 internal (Mine)
- **Output:** fixed 5-file set, always
- **Dependencies:** None. For parallel mining, use (and reload) `$pi-subagents` when sub-agents are supported; otherwise mine sequentially without loss of behavior.

---

## Invocation Scenarios

The skill is invoked via natural prompt. Flag-style shorthands (`--out`, `--force`, `--check`) are accepted as prompt arguments; there is no separate CLI.

| Trigger | What Happens |
|---------|--------------|
| "build an ontology for `<dir>`" / "andy-mode ; ontology `<dir>`" | Router inspects output dir -> Create or Update. Default output: `<dir>/_ontology/`. |
| Same with explicit output: `--out <out>` or "output to `<out>`" | Router honors the caller's output path. |
| "refresh the ontology" / "regenerate ontology" | Routes to Update (incremental). |
| "rebuild from scratch" / `--force` | Routes to Update; cache is discarded. |
| "check ontology status" / "is the ontology stale?" / `--check` | Routes to Check (no writes). |
| Host call from `wiki-map` Compile / FullSweep --deep | Host passes `input=references/`, `out=references/_meta/ontology/`; Router picks Create or Update. |
| Direct call from another skill (great-books, secret-history, etc.) | Same routing; output path is caller-chosen. |
| User points at a skill directory (contains `SKILL.md` + `references/`) | Router preflight redirects: corpus = `references/`, output = `references/_ontology/`. Asks once before proceeding. |

---

## Example Usage

### First-time generation

```text
User: build an ontology for my lecture-notes folder

AI responds:
Running Create in ontology...

Input:  lecture-notes/                         (72 files, 61,400 words)
Output: lecture-notes/_ontology/
Mining: 72 files via 6 parallel workers...
Cache:  lecture-notes/_ontology/.cache/mine.json (72 entries)

Written:
- lecture-notes/_ontology/INDEX.md
- lecture-notes/_ontology/concepts.md       (48 concepts)
- lecture-notes/_ontology/systems.md        (7 systems)
- lecture-notes/_ontology/questions.md      (11 implied-missing)
- lecture-notes/_ontology/connections.md    (empty-state: no typed relations detected)
```

### Refresh existing ontology

```text
User: refresh the ontology in docs/

AI responds:
Running Update in ontology...

Input:  docs/                                  (84 files, 70,200 words)
Output: docs/_ontology/                        (INDEX.md found)
Cache:  docs/_ontology/.cache/mine.json        (81 entries)

Changed since last run: 6 files (3 new, 3 mtime-bumped).
Re-mining 6 files, reusing 78 cached entries.

Regenerated:
- INDEX.md                    (last_refresh updated)
- concepts.md                 (+2 concepts, 1 removed)
- systems.md                  (unchanged)
- questions.md                (+1 gap)
- connections.md              (empty-state: unchanged)
```

### Status check

```text
User: check ontology status for this folder

AI responds:
Running Check in ontology...

Input:  scratch-notes/                         (18 files, 9,200 words)
Existing ontology: none
Cache: none

Recommendation: run Create if you want the 5-file ontology for this corpus.
```

---

## Configuration

No runtime configuration is required. Defaults:

| Default | Value | Override |
|---------|-------|----------|
| Output dir | `<input>/_ontology/` | `--out <path>` or prompt arg |
| Force full re-mine | off (cache honored) | `--force` |
| Extensions mined | `.md`, `.txt`, `.org` | `--ext "md,txt,..."` |

## Customization

| Customization | Where | Impact |
|---------------|-------|--------|
| Output dir convention | Caller / host | Hosts pick their own path (e.g. `_meta/ontology/`) |
| Mining prompts | `references/ontology/Mine/MetaSkill.md` | Tune per-file extraction behavior |
| Cache location | `references/ontology/SCHEMA.md` | Default is `<out>/.cache/mine.json` |

---

## Hard Rules

1. **Never hand-edit output.** The `ontology` route owns the 5 output files end-to-end. Hosts that want to annotate do so in sibling files, not inside the output.
2. **Never assume corpus conventions.** Wikilinks, frontmatter, and any input-side `INDEX.md` are optional signals -- detected, never required.
3. **Always produce the fixed 5 files.** Empty-state notes are required when a file has nothing to report. Never skip files.
4. **Drift detection is the host's job.** This skill writes; the host lints.
5. **Never mine a skill root.** When `SKILL.md` is present at `input`, the router preflight redirects to its `references/` subdir (or the caller must override). The skill root itself is never the corpus.
