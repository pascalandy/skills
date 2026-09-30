---
name: Docs
description: Script conventions, checks, installs, releases, and the remote skill tables, read on demand from AGENTS.md
schema_version: 3
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: 2026-09-26
date_updated: 2026-09-30
---

# Docs

> Content catalog. Read this first to find relevant pages
> **Total pages:** 7 | **Last updated:** 2026-09-30

`AGENTS.md` holds what every session needs. These pages hold procedures that only some tasks need

## Wiki Map

### kind/doc

| File | Description |
|------|-------------|
| `references/checks.md` | How `just check`, signoff, merge, commit hooks, and the manual CI workflow fit together, and how to change them |
| `references/install-skills.md` | Profiles, the private clone, ownership, fleet sync from any machine, hooks, and cutover for `just install-skills` |
| `references/release.md` | Steps to publish a tagged release |
| `references/remote-skills-dev.md` | Generated table of the `dev` skills only |
| `references/remote-skills-general.md` | Generated table of the `general` skills only, for someone who never writes code |
| `references/remote-skills.md` | Generated name and description of every skill in `skills/`, grouped by kind, for agents that cannot load these skills |
| `references/script-conventions.md` | The CLI contract for scripts/ and skill-local scripts, and the shared code and tests that enforce it |
