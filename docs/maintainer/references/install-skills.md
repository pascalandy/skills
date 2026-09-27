---
name: Install skills
description: Profiles, private packages, ownership, fleet sync from om1, hooks, and cutover for just install-skills
tags:
  - area/ea
  - kind/doc
  - topic/playbook
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-27
---

`just install-skills` installs public skills, every package in the private tree, and `authoring/commands/*.md` into one machine profile's agent directories. `just install-skills --help` lists profiles, targets, and flags. The prospective public source is the same in preview and apply

## Run it

- The profile follows the OS: `mac` on macOS, `om1` elsewhere. Pass `--profile` to override
- Every package under `_skills_private/` installs; `--private-root PATH` points to another private tree
- A name that is both public and private stops the run; delete the stale copy it names
- Preview via `just install-skills --dry-run --json`; use `--check` to exit nonzero when selected targets need work

## Sync machines

om1 is the hub. Every sync runs there and sends om1's skills to the other machines, which only receive

- `just sync` pulls `main` and installs on the machine it runs on. It refuses a checkout off `main`. With `--dry-run` or `--check` it skips the pull and previews the current checkout
- `just sync-fleet` syncs every machine in `_skills_private/fleet.toml`; name machines to limit it, such as `just sync-fleet mbp`, by registry name or host. The hub installs its own working tree. Every other machine receives the hub's `main` commit over SSH, without GitHub, fast-forwards its checkout to it, receives an exact mirror of the hub's `_skills_private/` without `fleet.toml` or runtime files, which the mirror also deletes there, then runs `just install-skills`
- A machine whose checkout is off `main`, has uncommitted changes under `authoring/`, `skills/`, `scripts/`, or `justfile`, or has commits the hub lacks reports `needs-you` and stays untouched. Other edits, such as editor settings, do not block it. An `offline` or `failed` machine gets one retry, then catches up at the next sync
- Success prints nothing. `--verbose` prints each machine's outcome, and `--dry-run` runs every check without changing anything
- `just sync-fleet --check` compares each machine's checkout, private tree, and installed skills per harness with the hub, then exits 1 naming each difference. It compares names and contents, so skills other tools installed do not count
- Private skills live only in the hub's `_skills_private/`; a copy edited on another machine is overwritten at the next sync. Editing a private skill fires no hook, so run `just sync-fleet` afterwards
- The registry stays in the private tree so hosts and accounts stay out of this public repository. Each `path` is relative to that machine's home:

```toml
[machines.om1]
ssh = "pascal@om1.example.ts.net"
path = "projects/skills"

[machines.mbp]
ssh = "andy16@mbp16.example.ts.net"
path = "Documents/github_local/skills"
```

### Hooks

`lefthook install` in the hub's checkout wires `lefthook.yml`. On `main` in that checkout, a commit or a pull that brings commits installs the hub at once, then syncs the other machines in the background, so git never waits on a sleeping laptop. A pull with nothing new fires no hook. Worktrees, other branches, and checkouts without `fleet.toml` skip the sync

The background run logs to `~/.local/state/skills-sync/fleet.log`. It sends a desktop notification only when a machine needs you or fails; an offline machine waits for the next sync

## Ownership

- The installer keeps no state. It owns every name git history ever added under `skills/` or `authoring/commands/`, plus uncommitted skills still flattened in `skills/`. A shallow clone is refused because its history is incomplete
- It removes an owned name once no source provides it and never touches entries it did not publish, such as `~/.claude/skills/synced/`
- A private skill that was never published is not owned. After deleting it from the private tree, trash its installed copies yourself
- Installed copies are execution copies. Apply overwrites an in-place edit, so make edits in `authoring/` or the private tree
- To promote a private skill, move it into `authoring/`, delete the private copy, and rerun

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
2. **Preserve old state.** Copy `~/.local/state/dotfiles-skills/` outside every target. If `~/.local/state/dotfiles-skills/pending.json` exists, stop: the old engine has an unfinished recovery
3. **Select the source.** Use a skills checkout at a reviewed `main` revision. Record the machine, `git rev-parse HEAD`, the profile, and the private packages already installed there. Make the private tree hold exactly the packages that remain private, and pass `--private-root PATH` when it is not `_skills_private/`
4. **Preview.** Run `just install-skills --profile PROFILE --dry-run --json` with that source, then the same with `--check --json`. An in-place edit shows as `update`; move one worth keeping into `authoring/` or the private tree first. Resolve each conflict, a symlink or wrong type at a target path, by hand
5. **Apply after approval.** Show Pascal the preview. After approval, run `just install-skills --profile PROFILE` with the same flags. The follow-up `--check --json` must exit 0
6. **Verify discovery.** Run `just skills-discover --profile PROFILE` with the same `--private-root`. An unavailable native adapter remains unverified, so start a new session in that agent and confirm the expected skills appear
7. **Retire the old engine.** Only after step 6 passes, move the step 1 writers, the release clone, `~/.local/state/dotfiles-skills/`, and any `~/.local/state/install-skills/` left by an earlier installer version to the trash. Keep the step 2 copy until Pascal discards it. Switch the machine's chezmoi source to dotfiles `main`, which no longer ships the old writers. chezmoi does not delete files removed from its source, so the trash step is still needed

Keep `~/.local/share/dotfiles/machine-identity.sh`, `~/.local/share/dotfiles/command-context.sh`, and `chezmoi-apply-mbp`. The old bootstrap installed them too, but they are not skill writers

## Related

- [[script-conventions]]
- [[release]]
