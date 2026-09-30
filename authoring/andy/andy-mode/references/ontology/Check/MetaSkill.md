# Check -- Status inspection

Run this when the user wants ontology status, whether an existing ontology is stale, or what the cache looks like. **Never writes.**

Follows the schema in `../SCHEMA.md`.

---

## When Check runs

Any of:

- User asks "ontology status", "is the ontology stale", "what is the cache state", or similar status questions.
- `--check` flag is set.
- Host wants a dry-run before deciding to call Create or Update.

---

## Workflow

### Phase 1 -- Orient

Restate inputs:

```text
Check | input=<path> | out=<path>
```

Verify `input` exists and is a directory. `<out>/` may or may not exist.

### Phase 2 -- Walk

Walk `input` recursively, filter to configured extensions. Compute:

- File count.
- Total word count (whitespace-tokenized).
- Wikilink density (files with `[[...]]` / total files).
- Frontmatter density (files with leading YAML / total files).

### Phase 3 -- Inspect Output

If `<out>/` exists:

- List which of the 5 files are present.
- If `INDEX.md` present and parseable, read frontmatter: `last_refresh`, `cache.entries`, `source_signals`.
- If `.cache/mine.json` present, read and report entry count.

### Phase 4 -- Diff Cache vs Corpus (if cache exists)

Without re-mining, compute:

- Files in walk not in cache (would be New on next Update).
- Files in cache with stale `mtime`/`size` (would be Changed).
- Files in cache not in walk (would be Removed).

This is a dry run -- read-only.

### Phase 5 -- Report

Print a structured report. No files are written.

```text
Check report for <input>

Corpus:
  files: 72
  words: 61,400
  extensions scanned: .md .txt
  wikilink density: 23% of files
  frontmatter density: 89% of files

Existing ontology at <out>:
  INDEX.md:       present (last_refresh: 2026-04-12T09:30:00Z, 7 days ago)
  concepts.md:    present
  systems.md:     present
  questions.md:   present
  connections.md: present (empty-state)
  cache:          present (65 entries)

Drift since last run (dry):
  new files:     7
  changed files: 3
  removed files: 0
  -> Update recommended

Recommendation: run `andy-mode ; ontology <input>` to Update (incremental).
```

### Phase 6 -- No Writes

Do not touch `<out>/`. Do not create directories. Do not modify the cache.

---

## Output Contract

The report is free-form markdown but must include these sections in order:

1. Corpus metrics
2. Existing ontology state (or "none")
3. Cache drift (or "no cache")
4. One-line recommendation: `Create` or `Update`.

Hosts can parse the last line for automation.

---

## Gotchas

- Never regenerate, mine, or write. Even if the ontology looks obviously wrong, Check only reports.
- If `INDEX.md` is malformed (not ours), say so and recommend the user investigate -- don't propose action.
- Timestamps in the report are relative ("7 days ago") plus absolute, for human readability.
