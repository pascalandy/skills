# Update -- Refresh an existing ontology

Run this when `<out>/INDEX.md` already exists. Cache-aware by default; `--force` regenerates everything.

Follows the schema in `../SCHEMA.md`. Load that file before starting if not already loaded.

---

## When Update runs

- `<out>/INDEX.md` is present, AND
- The user asked to refresh / regenerate, OR the router defaulted here because output already exists.

Two modes inside Update:

| Mode | Trigger | Behavior |
|------|---------|----------|
| Incremental | default | Reuse cache; re-mine only changed files |
| Full regen | `--force`, or any of the 4 content files is missing (repair), or cache schema-version mismatch | Delete cache, re-mine everything |

---

## Workflow

### Phase 1 -- Orient

1. Restate inputs:
   ```text
   Update | mode=<incremental|full-regen> | input=<path> | out=<path> | force=<bool>
   ```
2. Verify `input` exists. Verify `<out>/INDEX.md` exists. Read its frontmatter to confirm `kind: ontology-index` and pull `last_refresh`.
3. Check for repair conditions:
   - Any of `concepts.md` / `systems.md` / `questions.md` / `connections.md` missing -> switch to full regen, note "repair" in run summary.
   - Cache JSON missing or `version` mismatch -> switch to full regen.
   - Cache's stored `corpus_root` cannot be resolved against `<out>/` -> warn, switch to full regen.

### Phase 2 -- Signal Detection

Same as Create Phase 2. Compare against the previously-recorded `source_signals` in INDEX. If they changed (e.g., wikilinks newly detected), treat as a signal shift -- incremental is still fine; record the change in the run summary.

### Phase 3 -- Corpus Metrics

Recompute file count, word count, and extensions scanned. These metrics are informational only; do not block ontology refresh based on corpus size.

If no mineable files are found, stop with a clear warning and keep the existing ontology untouched.

### Phase 4 -- Cache Diff

Load `<out>/.cache/mine.json`. Build the current file list from the walk.

Compute three sets:

- **New**: file in walk, not in cache.
- **Changed**: file in both, `mtime` or `size` differs.
- **Removed**: file in cache, not in walk.

In **full regen** mode, treat every file as "changed" and discard the cache file contents (keep the file, overwrite atomically).

### Phase 5 -- Mine (incremental)

Delegate to `../Mine/MetaSkill.md` with:

- Files to (re-)mine: New + Changed
- Files to skip: unchanged cached entries (reused as-is)
- Entries to drop: Removed

Update the cache JSON atomically (write to `.cache/mine.json.tmp`, fsync, rename).

### Phase 6 -- Synthesize

Identical to Create Phase 5. Rebuild all 4 content files from the full cache (not just the delta). Ontology outputs are always re-derived from the merged cache so stale entries cannot leak through.

### Phase 7 -- Write INDEX.md

Overwrite `INDEX.md`. Update:

- `last_refresh` = now (UTC ISO-8601)
- `cache.entries` = total entries in cache
- `cache.hits_this_run` = reused entries
- `cache.misses_this_run` = new + changed
- `source_signals` = freshly-detected values
- Run summary paragraph: what changed (deltas in concept / system / question counts vs previous INDEX if recorded).

### Phase 8 -- Report

```text
Update complete | mode=<incremental|full-regen> | changed_files=<n> (new=<n>, modified=<n>, removed=<n>) | cache_hits=<n> misses=<n>
Deltas: concepts <+n/-n>, systems <+n/-n>, questions <+n/-n>, connections <+n/-n|empty>
Output: <out>/
```

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| `<out>/INDEX.md` malformed or not ours | Refuse to overwrite. Ask the user: replace it (full regen) or abort. |
| Cache file exists but JSON invalid | Treat as cache-missing, full regen. |
| Corpus signal profile changed (e.g. wikilinks newly detected) | Log the shift, continue incremental mine. |
| All files unchanged (cache hits for every file) | Still re-synthesize and rewrite INDEX.md with bumped `last_refresh`. Report zero deltas. |
| User asked to "refresh" but no INDEX at `<out>` | Router will have picked Create instead; reassert that in the run summary. |
| Output dir contains hand-edits (diff against cache-reconstructed expected content) | Overwrite anyway. Note in the run summary: "Hand-edits detected in <files> and overwritten." Hosts lint this. |

---

## Gotchas

- Always re-derive outputs from the **whole** cache after the delta merge. Never patch individual lines into existing output files.
- Atomic write the cache (`.tmp` + rename). A crashed Update that partially wrote the cache would poison the next incremental run.
- Cache key is `mtime + size`. A file rewritten with identical content but updated mtime is treated as changed -- this is correct; the mining pass is cheap relative to being wrong.
- `last_refresh` is UTC. Do not localize.
- `--force` wipes the cache; the user gets no incremental benefit. Use it only when schema changes or mining prompt changes.
