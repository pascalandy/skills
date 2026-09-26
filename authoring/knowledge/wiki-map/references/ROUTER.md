---
name: "wiki-map"
description: "Route wiki-map requests to ingest, query, lint, or compile workflows."
---

# Wiki Map

> **Note:** This router dispatches to sub-skills. Read only the sub-skill
> referenced by the matched pattern. Do not read all sub-skills preemptively.

## Routing

| Request Pattern | Route To |
|---|---|
| `pa-doc-update` postflight, post-write documentation conformance | Caller-owned `WikiMapPostflight.md` -> read `SCHEMA.md`; keep the caller's scope and do not load an operational sub-skill or workflow |
| create wiki map, create wiki, bootstrap, init wiki, new wiki, organize files | `Ingest/MetaSkill.md` -> `workflows/CreateWikiMap.md` |
| ingest, process source, add source, add to wiki, webclip, process article | `Ingest/MetaSkill.md` -> `workflows/IngestSingle.md` |
| batch ingest, process sources, ingest all, bulk import | `Ingest/MetaSkill.md` -> `workflows/IngestBatch.md` |
| delete page, remove page, get rid of page, delete webclip | `Ingest/MetaSkill.md` -> `workflows/Delete.md` |
| upgrade then normalize, migrate to v3 and convert to collection, upgrade and remove inception | `Ingest/MetaSkill.md` -> load `workflows/UpgradeSchema.md` and `workflows/NormalizeWikiMap.md`; plan them separately, obtain approval naming both, execute and verify UpgradeSchema first, revalidate normalization preconditions, then execute NormalizeWikiMap |
| upgrade wiki, upgrade schema, migrate wiki, migrate to v3, clean legacy wiki logs | `Ingest/MetaSkill.md` -> `workflows/UpgradeSchema.md` |
| normalize wiki, convert to collection, wiki collection, remove inception, flatten wiki wrapper | `Ingest/MetaSkill.md` -> `workflows/NormalizeWikiMap.md` |
| add DDD glossary, create DDD glossary, build DDD glossary, update DDD glossary, create ubiquitous language, build ubiquitous language, create domain glossary, update domain glossary | `Query/MetaSkill.md` -> `workflows/AddDDDGlossary.md` |
| query, search wiki, ask wiki, what does the wiki say, find in wiki, domain model terms | `Query/MetaSkill.md` -> `workflows/Search.md` or `workflows/DeepQuery.md` |
| synthesize, deep query, compare, timeline, current understanding | `Query/MetaSkill.md` -> `workflows/DeepQuery.md` |
| file answer, save answer, save as wiki page, compound answer | `Query/MetaSkill.md` -> `workflows/FileAnswer.md` |
| recursive wiki update, refresh wiki tree, update nested wiki, rebuild index routes | `Lint/MetaSkill.md` -> `workflows/RecursiveUpdate.md` |
| maintain wiki, wiki maintenance, maintenance pass, maintenance cycle, triage fixes, safe-fix plan, living wiki maintenance | `Lint/MetaSkill.md` -> `workflows/MaintenanceCycle.md` |
| lint, health check, full sweep | `Lint/MetaSkill.md` -> `workflows/FullSweep.md` |
| find orphans, contradictions, provenance, sources, stale pages, outdated information, freshness check, topic tags, tag order, big pages, index size, legacy logs, partial write, recovery, root documentation, `AGENTS.md`, `README.md`, DRY across root files | `Lint/MetaSkill.md` -> `workflows/QuickCheck.md` |
| compile wiki, fill wiki gaps, promote missing entities, is the wiki complete, concept mining | `Compile/MetaSkill.md` -> `workflows/CompileWiki.md` |
| wiki-map update (bare phrase, ambiguous) | Orient read-only, report any schema upgrade or collection-normalization opportunity, then ask whether the user wants **upgrade**, **normalize**, **lint**, **maintain**, **refresh**, **compile**, or **query glossary**. Never treat the phrase as migration approval. |
