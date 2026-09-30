# Create -- First-time ontology generation

Run this when no `INDEX.md` exists at `<out>/`, or when the user explicitly asks to wipe and regenerate.

Follows the schema in `../SCHEMA.md`. Load that file before starting if not already loaded.

---

## When Create runs

- `<out>/` does not exist, OR
- `<out>/` exists but has no `INDEX.md`, OR
- User explicitly said "from scratch" / "wipe and regenerate" **and** approved replacing an existing ontology.

If a prior INDEX exists and the user did not approve replacement, re-route to Update.

---

## Workflow

### Phase 1 -- Orient

1. Restate inputs:
   ```text
   Create | input=<path> | out=<path>
   ```
2. Verify `input` exists and is a directory. If not, stop and report.
3. Ensure `<out>/` exists (create it) and that it is empty of ontology files. If it contains unrelated files, list them and ask before proceeding.

### Phase 2 -- Signal Detection

Walk `input` recursively, filter to configured extensions (default `.md`, `.txt`, `.org`). For the resulting file list:

1. Count files and total words (whitespace-tokenized).
2. Grep the full file list for `\[\[[^\]]+\]\]` wikilinks. Set `wikilinks_detected = true` when >= 10% of files match.
3. Grep the full file list for a leading `---\n` YAML block. Set `frontmatter_detected = true` when >= 10% of files match.

Record all three signals; they feed `source_signals` in `INDEX.md`.

### Phase 3 -- Corpus Metrics

Record file count, word count, and extensions scanned. These metrics are informational only; do not block ontology generation based on corpus size.

If no mineable files are found, stop with a clear message and do not write partial ontology files.

### Phase 4 -- Mine

Delegate to the Mine phase (`../Mine/MetaSkill.md`). Pass the file list, extension filter, `source_signals`, and an empty cache. Mine produces per-file extractions and writes `<out>/.cache/mine.json` atomically. Parallelization policy lives in Mine -- do not reimplement here.

### Phase 5 -- Synthesize

From the cached per-file extractions, build the 4 content files per `../SCHEMA.md`:

1. **concepts.md** -- merge per-file concept lists, dedupe by normalized name (lowercase, stripped punctuation), keep the clearest one-line definition, aggregate sources.
2. **systems.md** -- cluster files by shared concept overlap and explicit per-file `systems` hints from mining. One cluster per coherent thesis; minimum 2 members.
3. **questions.md** -- surface topics mentioned in >= 2 files but never defined.
4. **connections.md** -- include only relations that carry a relation *type* from mining. Otherwise emit the empty-state note.

### Phase 6 -- Write INDEX.md

Fill INDEX per schema: input, out, corpus metrics, `last_refresh` = now (UTC ISO-8601), cache counts, signal detection, and a one-paragraph run summary.

### Phase 7 -- Report

Return a run summary to the caller:

```text
Create complete | files_mined=<n> (cache misses=<n>, hits=0) | concepts=<n> systems=<n> questions=<n> connections=<n|empty>
Output: <out>/
```

---

## Gotchas

- If `<out>/` was non-empty with stray files, stop and ask. Don't silently overwrite non-ontology content.
- If mining returns zero concepts for a large corpus, the mining prompt is probably wrong -- report and ask before continuing.
- If wikilinks are present in the corpus but the mining phase produced only relative paths, trust `source_signals` and convert during synthesis -- do not ignore the detected signal.
- The cache directory (`.cache/`) counts as an ontology file for cleanliness checks; do not complain about it on a subsequent Update.
