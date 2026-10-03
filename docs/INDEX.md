---
name: Docs
description: Script conventions, checks, installs, releases, the remote skill lists, and the skill count, read on demand from AGENTS.md
schema_version: 3
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: 2026-09-26
date_updated: 2026-10-03
---

# Docs

> Content catalog. Read this first to find relevant pages
> **Total pages:** 8 | **Last updated:** 2026-10-02

`AGENTS.md` holds what every session needs. These pages hold procedures that only some tasks need

## Wiki Map

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
