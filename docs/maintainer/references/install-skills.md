---
name: Install skills
description: Profiles, private packages, ownership, and cutover for just install-skills
tags:
  - area/ea
  - kind/doc
  - topic/playbook
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-26
---

`just install-skills` installs public skills, explicitly selected private packages, and `authoring/commands/*.md` into one machine profile's agent directories. `just install-skills --help` lists profiles, targets, and flags. The prospective public source is the same in preview and apply

## Run it

- `--profile mac` is the default; use `--profile om1` on om1
- `--private NAME` explicitly includes an ignored package from `_skills_private/`
- Preview via `just install-skills --dry-run --json`; use `--check` to exit nonzero when selected targets need work

## Ownership

- A source-aware manifest in `~/.local/state/install-skills/` records installed skills and migrates the public-only v1 format. Public-only runs retain omitted private ownership and inactive profile targets. Retire a private skill only with `--retire-private NAME:DIGEST` from its manifest record
- If a copy was edited in place, move the edit to `authoring/`, then rerun with `--force`

## Cutover

For a later authorized cutover, stop old installed skill writers first, preserve old manifests and snapshots, record each machine's selected revision/profile/private sources and preview decisions, then verify the post-install report and `just skills-discover --profile PROFILE`. An unavailable native adapter remains unverified

## Related

- [[script-conventions]]
- [[release]]
