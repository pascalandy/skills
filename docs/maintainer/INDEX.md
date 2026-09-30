---
name: Maintainer
description: Script conventions, checks, installs, releases, and the remote skill table for maintaining this repository
schema_version: 3
tags:
  - area/ea
  - kind/wiki
  - status/open
date_created: 2026-09-26
date_updated: 2026-09-30
---

# Maintainer

> Content catalog. Read this first to find relevant pages
> **Total pages:** 5 | **Last updated:** 2026-09-30

## Wiki Map

### kind/doc

| File | Description |
|------|-------------|
| `references/checks.md` | How `just check`, signoff, commit hooks, and the manual CI workflow fit together, and how to change them |
| `references/install-skills.md` | Profiles, private packages, ownership, and cutover for `just install-skills` |
| `references/release.md` | Steps to publish a tagged release |
| `references/remote-skills.md` | Generated name and description of every skill in `skills/`, for agents that cannot load these skills |
| `references/script-conventions.md` | The CLI contract for scripts/ and skill-local scripts, and the shared code and tests that enforce it |
