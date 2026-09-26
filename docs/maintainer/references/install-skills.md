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

Move one machine at a time from the old dotfiles skill engine to this installer, and only with Pascal's authorization for that machine. Never let both engines write the same targets

| Machine | Profile |
|---|---|
| `mbp16` | `mac` |
| Mac mini | `mac` |
| `om1` | `om1` |

1. **Stop the old writers.** The old engine has no timer; it runs only when one of these is called. Confirm that nothing calls them during the cutover, including `fleet-sync-skills` from another machine, and list which exist:
   - `~/.local/bin/`: `dotfiles-release`, `dotfiles-skills`, `sync-skills`, `mbp-sync-skills`, `fleet-sync-skills`
   - `~/justfile` recipes `skills-update`, `sync-skills`, `pull-dotfiles`, and `om1`
   - The release clone in `~/.local/share/dotfiles-release/`
2. **Preserve old state.** Copy `~/.local/state/dotfiles-skills/` and any existing `~/.local/state/install-skills/manifest.json` outside every target. If `~/.local/state/dotfiles-skills/pending.json` exists, stop: the old engine has an unfinished recovery
3. **Select the source.** Use a skills checkout at a reviewed `main` revision. Record the machine, `git rev-parse HEAD`, the profile, and the private packages already installed there. Pass each one with `--private NAME`, plus `--private-root PATH` when the private tree is not `_skills_private/`
4. **Preview.** Run `just install-skills --profile PROFILE --dry-run --json` with those `--private` flags, then the same with `--check --json`. For each conflict, compare the installed copy with its source, and move an edit worth keeping into `authoring/` or the private tree first. Do not use `--force` to skip this review
5. **Apply after approval.** Show Pascal the preview. After approval, run `just install-skills --profile PROFILE` with the same flags. The follow-up `--check --json` must exit 0
6. **Verify discovery.** Run `just skills-discover --profile PROFILE`. An unavailable native adapter remains unverified, so start a new session in that agent and confirm the expected skills appear
7. **Retire the old engine.** Only after step 6 passes, move the step 1 writers, the release clone, and `~/.local/state/dotfiles-skills/` to the trash. Keep the step 2 copy until Pascal discards it. Switch the machine's chezmoi source to dotfiles `main`, which no longer ships the old writers. chezmoi does not delete files removed from its source, so the trash step is still needed

Keep `~/.local/share/dotfiles/machine-identity.sh`, `~/.local/share/dotfiles/command-context.sh`, and `chezmoi-apply-mbp`. The old bootstrap installed them too, but they are not skill writers

## Related

- [[script-conventions]]
- [[release]]
