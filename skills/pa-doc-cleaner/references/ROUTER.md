---
name: pa-doc-cleaner
description: Universal documentation-maintenance meta-skill for keeping documentation systems accurate, compact, coherent, and navigable across repositories, websites, content systems, project-management workspaces, knowledge bases, or personal workflows. USE WHEN refresh stale docs, outdated docs, audit docs against reality, review docs for drift, deduplicate docs, consolidate docs, prune dead docs, condense overlapping docs, clean up repeated notes, fix frontmatter, regenerate indexes, repair routing tables, normalize taxonomy, repair cross-references, improve documentation navigation.
---

# Doc Cleaner

## Routing

| Request Pattern | Route To |
|---|---|
| update docs for this change, capture what changed, write an ADR, document this module, write current-state docs for this artifact | out of scope -> hand off to `pa-doc-update`; if unavailable, state that the request is outside `pa-doc-cleaner` |
| explore this project, figure out what needs to change, define the feature, write the implementation plan, implement the change | out of scope -> hand off to `pa-scope`, `architect`, `figure-it-out`, or a separate `poteto-mode` delivery session as appropriate; if unavailable, state that the request is outside `pa-doc-cleaner` |
| fix frontmatter, repair indexes, rebuild routing tables, repair cross-references, normalize taxonomy, fix documentation navigation, restore documentation structure, repair metadata | `StructureGovernance/MetaSkill.md` |
| deduplicate docs, consolidate overlapping docs, prune docs, condense repeated sections, remove dead knowledge, clean up redundant notes, simplify this duplicated doc area | `ConsolidationPass/MetaSkill.md` |
| refresh stale docs, outdated docs, audit docs against reality, review docs for drift, see what should be kept or updated, stale documentation sweep, maintenance audit | `DriftRefresh/MetaSkill.md` |
