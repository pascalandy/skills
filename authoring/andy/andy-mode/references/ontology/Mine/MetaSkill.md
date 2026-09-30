# Mine -- Per-file extraction (internal)

Shared phase used by Create and Update. Not user-facing. Produces the cache entries that Synthesize later merges into the 4 content files.

---

## Contract

**Input:**

- `corpus_root`: absolute path to the corpus root (runtime input). Note: the value written into `.cache/mine.json` is stored *relative* to `<out>/` per the "Cache writes" section below; these are distinct concerns.
- `files_to_mine`: list of file paths (relative to `corpus_root`).
- `cache`: existing `.cache/mine.json` contents (may be empty).
- `source_signals`: `{wikilinks_detected, frontmatter_detected}` from the detection phase.

**Output:**

- Updated cache object: one entry per file mined. Cache entries for files not in `files_to_mine` are preserved verbatim.

**Side effects:**

- Atomic write to `<out>/.cache/mine.json` via `.tmp` + rename.

---

## Per-file extraction

For each file, produce this structure:

```json
{
  "mtime": <unix ts>,
  "size": <bytes>,
  "concepts": [
    {"name": "Gerontocracy", "definition": "Rule by the old; contrast to meritocracy."}
  ],
  "systems": [
    {"name": "Law of Asymmetry", "role": "member"}
  ],
  "questions": [
    "Why does the gerontocracy-meritocracy cycle not stabilize?"
  ],
  "connections": [
    {"to": "lecture-01.md", "type": "supersedes"}
  ]
}
```

Extraction rules:

- **Concepts**: named nouns / noun phrases the file defines or centrally discusses. Definition is one line, distilled from the file, **never invented**. If the file references a concept without defining it, either emit it with a best-effort one-line definition or drop it -- do NOT fall it through to `questions` (see Questions rule below).
- **Systems**: named clusters or frameworks the file names explicitly (e.g. "the EOC triad", "the capital arc"). `role` is `member` if the file is one of several; `definition` if the file is the canonical source.
- **Questions**: genuine unresolved interrogatives the file poses without answering. **Every emitted entry must either end with a literal `?` or begin with a known interrogative lead (`Why`, `How`, `What`, `Where`, `When`, `Does`, `Do`, `Did`, `Can`, `Could`, `Will`, `Would`, `Should`, `Is`, `Are`, `If ...`).** Topics referenced without a definition but without a question-shape go to `concepts` with a best-effort one-line definition, or are dropped entirely -- they do NOT fall through into `questions`. Surviving questions become `questions.md` entries if they appear across >=2 files.
- **Connections**: only emit if the file explicitly names a typed relation. Acceptable types: `supersedes`, `contradicts`, `extends`, `sources`, `refutes`, `applies`. If the relation is unclear, omit -- do not infer.

If `frontmatter_detected`, read YAML frontmatter and treat these fields as hints:

- `sources:` -> candidate connections of type `sources`.
- `supersedes:` -> connections of type `supersedes`.
- `tags:` -> concept candidates (filter aggressively; tags are often noise).

If `wikilinks_detected`, parse `[[target]]` occurrences as co-occurrence signals; only count them as typed connections when the surrounding text names the relation (e.g. "this supersedes [[earlier-lecture]]").

---

## Parallelization

Default: use (and reload) `$pi-subagents` to dispatch parallel workers.

1. Batch `files_to_mine` into groups of ~10 files.
2. Dispatch one sub-agent per batch with the same extraction contract.
3. Collect results; merge into the cache object.

Fallback (harness does not support sub-agents, or `files_to_mine` < 10):

1. Mine sequentially, file by file.
2. Flush the cache to `.cache/mine.json.tmp` every 10 files so a crashed run does not lose work. Final rename on completion.

---

## Cache writes

When writing `<out>/.cache/mine.json`, compute `corpus_root` as the relative path **from `<out>/` to the input corpus root**, not as an absolute path. Use forward slashes. Example: if out is `foo/references/_ontology/` and input is `foo/references/lessons/`, store `"corpus_root": "../lessons"`.

On read, callers must resolve `corpus_root` against `<out>/` before using it. If resolution fails (the relative path no longer points at a directory), warn the caller and treat the cache as invalid for this run -- do **not** silently treat every file as new.

---

## Cache Key

The key into `cache.entries` is the path **relative to `corpus_root`**, using forward slashes. Example: `topic/sub/file.md`.

This means renaming a file invalidates its entry (by design). Renames are rare; re-mining a renamed file is cheap.

---

## Output

Return (to Create / Update):

- The full merged cache object.
- Counts: mined, cache-hits, cache-misses, dropped (removed files).
- A flat list of all extracted concepts / systems / questions / connections, deduped, ready for Synthesize to format.

---

## Gotchas

- Do not invent definitions. If the file uses a concept without defining it, leave the concept out of `concepts`. Drop the phrase into `questions` **only if it is interrogative-shaped** per the Questions rule above; otherwise omit it.
- A concept that appears exactly once in the corpus is usually noise. Let Synthesize decide; Mine's job is to extract faithfully.
- Relation typing is strict. "This lecture talks about X" is not `sources`; an explicit citation is.
- Keep definitions to one line. Multi-line definitions blow up `concepts.md`.
- The mining prompt is tuned per corpus only via `extensions` and `source_signals`. Do not add corpus-specific heuristics (wiki-specific kind tags, lecture numbering schemes) here -- those belong to the host.
