# ontology-map Schema

Canonical contract shared by Create, Update, and Check. All sub-skills must honor this schema.

---

## The Fixed 5-File Output

Every successful run writes exactly these files to `<out>/`. None are optional. If a file has no content to report, it must still be written with an explicit empty-state note.

```text
<out>/
├── INDEX.md           # routes + run metadata
├── concepts.md        # core ideas, 1-line definitions, relative-path sources
├── systems.md         # named clusters of files that form a system
├── questions.md       # gaps the corpus implies but does not answer
└── connections.md     # typed relations between files (empty-state allowed)
```

Plus an internal cache (not counted in the "5 files"):

```text
<out>/.cache/mine.json    # per-file extraction cache; safe to delete
```

---

## INDEX.md

Structure:

```markdown
---
kind: ontology-index
corpus: <corpus name or leaf directory, e.g. "great-books">
input: <absolute or relative path to corpus root>
out: <absolute or relative path to this dir>
corpus_metrics:
  files: 72
  words: 61400
last_refresh: 2026-04-19T13:45:22Z
cache:
  path: .cache/mine.json
  entries: 72
  hits_this_run: 66
  misses_this_run: 6
source_signals:
  wikilinks_detected: true
  frontmatter_detected: true
  extensions_scanned: [".md", ".txt"]
---

# Ontology Index

- [Concepts](concepts.md) -- 48 entries
- [Systems](systems.md) -- 7 clusters
- [Questions](questions.md) -- 11 implied-missing gaps
- [Connections](connections.md) -- empty-state / typed relations

## Run Summary

<one-paragraph summary: action taken, counts, anything notable>
```

Hard rules for INDEX.md:

- `kind: ontology-index` is the discriminator that identifies our output on re-entry. Update refuses to overwrite any `INDEX.md` without it.
- `last_refresh` is UTC ISO-8601.
- `source_signals` records what was detected, not assumed.
- No wiki-specific fields (`tags`, `topic/*`, `INDEX` backlinks) unless the host post-processes them in.

---

## concepts.md

Markdown table, one row per concept:

```markdown
# Concepts

| Concept | Definition | Sources |
|---------|------------|---------|
| Gerontocracy | Rule by the old; named contrast to meritocracy. | [lecture-03.md](../lecture-03.md), [lecture-17.md](../lecture-17.md) |
| ... | ... | ... |
```

- **Concept**: noun phrase, deduped across files.
- **Definition**: one line, distilled from the corpus, not invented.
- **Sources**: relative paths from `<out>/` to the source files. Use `[[wikilink]]` instead of relative path **only if** `source_signals.wikilinks_detected` is true.

Empty state:

```markdown
# Concepts

_No recurring concepts detected above the noise floor._
```

---

## systems.md

```markdown
# Systems

## <system name>

<one-paragraph description of the cluster and the thesis that ties the files together>

**Members:**
- [file-a.md](../file-a.md)
- [file-b.md](../file-b.md)
- ...

---
```

- A "system" is a set of files that together describe a coherent mechanism, argument, or domain.
- Minimum 2 members.
- Maximum suggestion: aim for 3-12 systems; more than 20 implies the mining prompt is too loose.

Empty state:

```markdown
# Systems

_No multi-file systems detected. The corpus reads as independent entries._
```

---

## questions.md

```markdown
# Questions

Gaps the corpus implies but does not answer. These are extraction outputs, not author opinion.

- **<question>** -- implied by [file-a.md](../file-a.md), [file-c.md](../file-c.md).
- **<question>** -- implied by ...
```

- A "question" is a claim or topic referenced in multiple files but never defined or resolved.
- One line per question; do not attempt to answer.

Empty state:

```markdown
# Questions

_No implied-missing gaps detected._
```

---

## connections.md

Only populate if the mining phase captured **relation type**, not just co-occurrence. Co-occurrence is already visible via concept sources.

```markdown
# Connections

Typed relations between files.

| From | Relation | To |
|------|----------|----|
| [lecture-03.md](../lecture-03.md) | supersedes | [lecture-01.md](../lecture-01.md) |
| [lecture-17.md](../lecture-17.md) | contradicts | [lecture-09.md](../lecture-09.md) |
```

Common relation types: `supersedes`, `contradicts`, `extends`, `sources`, `refutes`, `applies`. The mining phase is responsible for typing; do not infer post-hoc.

Empty state:

```markdown
# Connections

_No typed relations detected. Relations are surfaced in `concepts.md` via shared sources._
```

---

## Corpus Metrics

Every run records corpus size for operator context, but corpus size is **not** a gate. If the user invokes `ontology-map`, Create and Update proceed for any non-empty directory that has mineable files.

| Metric | Notes |
|--------|-------|
| File count | `.md` + `.txt` + `.org` by default |
| Word count | Whole corpus, tokenized on whitespace |

If no mineable files are found, stop with a clear message and do not write partial ontology files.

---

## Cache

`<out>/.cache/mine.json` -- single JSON file. Schema:

```json
{
  "version": 1,
  "corpus_root": "<path relative to the ontology output dir, e.g. \"../lessons\">",
  "generated_at": "2026-04-19T13:45:22Z",
  "entries": {
    "<relative-path-from-corpus-root>": {
      "mtime": 1713528000,
      "size": 4821,
      "concepts": [{"name": "...", "definition": "..."}],
      "systems": [{"name": "...", "role": "member" }],
      "questions": ["..."],
      "connections": [{"to": "<rel-path>", "type": "supersedes"}]
    }
  }
}
```

> **Portability rule.** `corpus_root` is stored relative to `<out>/` (the ontology output dir), not absolute. Readers resolve it against `<out>/` at load time. This lets the cache survive corpus renames and repository relocations as long as the relative layout is preserved. If resolution fails, the cache is treated as invalid for that run (see invalidation list below).

Cache-key rule: `mtime + size`. Not `date_updated:` frontmatter (not every corpus has it).

Cache invalidation:

- `--force` -> delete file, re-mine everything.
- File missing from corpus -> remove entry.
- Entry stale (mtime or size changed) -> re-mine that file.
- Schema `version` mismatch -> delete file, re-mine everything.
- Stored `corpus_root` cannot be resolved against `<out>/` -> warn, treat cache as invalid for this run, full regen.

---

## Signal Detection (never assume)

Before mining, probe the corpus to set `source_signals`:

| Signal | How to detect | Effect |
|--------|---------------|--------|
| Wikilinks | grep for `\[\[[^\]]+\]\]` in ≥10% of files | Use `[[wikilink]]` in sources columns |
| Frontmatter | grep for leading `---\n` YAML in ≥10% of files | Read `sources:`, `tags:`, `date_updated:` as hints |
| Extensions | first pass file list | Record actually-mined extensions |
| Skill context | `SKILL.md` + `references/` present at input root | Redirect input to `references/`; default out to `references/_ontology/` (router preflight handles this) |

Record all three in INDEX.md `source_signals`.

---

## What NOT To Include

- No `kind/*` / `topic/*` / `status/*` tags. Those are wiki-map conventions.
- No `LOG.md` entries. Hosts handle logging.
- No `INDEX.md` backlinks into the corpus. `ontology-map`'s INDEX is self-contained.
- No per-file frontmatter templates for concepts/systems/questions. One file each, markdown.

---

## Hard Rules (shared by all sub-skills)

1. Always write all 5 files; use empty-state notes when content is absent.
2. Relative paths only in outputs, unless wikilinks are detected.
3. Cache keys are `mtime + size`, never frontmatter dates.
4. Corpus size is informational only; do not block Create or Update based on file or word count.
5. The skill owns output files end-to-end. Hand-edits are overwritten on the next run.
6. Drift detection is the host's job; this skill does not lint.
7. On any schema-version mismatch, regenerate rather than patch.
