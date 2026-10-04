---
name: Docs
description: The public guide, plus script conventions, checks, installs, releases, the remote skill lists, and the skill count, read on demand from AGENTS.md
schema_version: 3
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: 2026-09-26
date_updated: 2026-10-04
---

# Docs

> Content catalog. Read this first to find relevant pages
> **Total pages:** 24 | **Last updated:** 2026-10-04

`AGENTS.md` holds what every session needs. These pages hold procedures that only some tasks need, and the guide teaches readers who never open a terminal

## Wiki Map

### kind/guide

| File | Description |
|------|-------------|
| `guide/README.md` | Public tutorial in seven pages for readers who use a chat app such as ChatGPT or Claude: paste one sentence, then use the modes and skills |
| `guide-fr-ca/README.md` | The same tutorial in Canadian French, page for page under the same file names |

### kind/doc

| File | Description |
|------|-------------|
| `references/checks.md` | How `just check`, signoff, merge, commit hooks, and the manual CI workflow fit together, and how to change them |
| `references/install-skills.md` | Profiles, the private clone, ownership, fleet sync from any machine, hooks, and cutover for `just install-skills` |
| `references/release.md` | Steps to publish a tagged release |
| `references/remote-skills-dev.md` | Generated list of the `dev` skills only |
| `references/remote-skills-general.md` | Generated list of the `general` skills only, for someone who never writes code |
| `references/remote-skills.md` | Generated name and description of every skill in `skills/`, grouped by kind with modes first, each with its routes and their descriptions, for agents that cannot load these skills |
| `references/script-conventions.md` | The CLI contract for scripts/ and skill-local scripts, and the shared code and tests that enforce it |
| `references/skill-count.md` | Generated count of skills per `authoring/` category and kind, to spot skills that appeared or vanished |
