---
name: docs
description: Universal documentation meta-skill for creating or updating documentation tied to a concrete change, lightweight decision rationale, or concrete artifact across repositories, websites, content systems, project-management workspaces, knowledge bases, or personal workflows. USE WHEN update docs for this change, capture what changed, release notes, changelog, sync shipped changes, ADR, decision record, why did we choose this, document this module, document this workflow as it works today, update this reference doc to match current state, document this page or board.
---

# Doc

## Shared Evidence Rule

Before drafting any in-scope documentation update, build an evidence baseline:

1. Inspect the target artifact and existing documentation.
2. In a git workspace, run `git status --short`, `git diff --stat`, and the relevant `git diff` for changed paths; include staged diff when staged changes matter. If there is no diff or the workspace is not git-backed, state that explicitly.
3. Check for an existing relevant `postmortem-*.md` artifact, especially under the resolved `sdlc-pa` export root beside related lifecycle artifacts. If it exists, use it as context for lessons, risks, rationale, follow-ups, and cross-references.
4. If the documentation target, affected surface, blast radius, validation surface, or artifact relevance is unclear, use (and reload) `$blast-radius` first and feed its scope judgment back into this doc update.

Do not create or rewrite postmortems here.

## Routing

| Request Pattern | Route To |
|---|---|
| postmortem, lessons learned, incident review, retrospective, session review, durable feedback capture, what happened, what did this reveal, what should we remember or change next time | out of scope -> state that the request is outside the `docs` route |
| clean up docs, deduplicate docs, refresh stale docs across the repo, audit documentation, reorganize docs, fix frontmatter, repair routing tables, documentation governance | out of scope -> hand off to the `docs-cleaner` route; if unavailable, state that the request is outside the `docs` route |
| explore this project, figure out what needs to change, define the feature, write the implementation plan, implement the change | out of scope -> hand off to `architect`, `figure-it-out`, or a separate `poteto-mode` delivery session as appropriate; if unavailable, state that the request is outside the `docs` route |
| update the docs for this change, capture what changed, document this fix, release notes, changelog, sync docs after shipping, post-ship docs, capture the shipped changes, document what we just changed | `ChangeCapture/MetaSkill.md` |
| adr this, record this decision, why did we choose this, capture the rationale, record chosen/rejected alternatives, tradeoffs and consequences | `RationaleCapture/MetaSkill.md` |
| document this module as it works today, document this component as it exists now, document this workflow as it works today, document this page, explain this artifact in documentation form, write current-state reference docs for this thing, update this reference doc to match current state | `ArtifactDocumenter/MetaSkill.md` |
