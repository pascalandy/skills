---
name: Install skills
description: Profiles, the private clone, ownership, fleet sync from any machine, hooks, and cutover for just install-skills
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
- Applies from one repository, its worktrees included, take turns through a lock in its git directory, so overlapping runs, such as a commit hook during `just sync-fleet`, leave the newest working tree installed. Previews and checks do not wait

## Private skills

Private skills live in the private repository `pascalandy/skills-private`, cloned inside this checkout at `_skills_private/`. Its URL is this checkout's `origin` with `skills` renamed to `skills-private`, so each machine reaches GitHub the way its public checkout does

- Git uses the nearest `.git` above the current directory. Inside `_skills_private/`, git commands act on the private repository; anywhere else, on the public one
- This repository's `.gitignore` line `/_skills_private/` keeps the clone and its `.git` out of the public repository; it is not a submodule. Keep that line, and never `git add -f` the folder
- `scripts/sync_private.py` manages the clone; `just sync` and `just sync-fleet` run it. It clones a missing folder, commits uncommitted edits as `🧰 skill: private: save edits from <machine>`, pulls with rebase, and pushes. A folder that is not a clone, or a clone off `main`, stops it untouched. Edits that conflict with GitHub stay committed on that machine and stop it; resolve them with `git pull --rebase` in `_skills_private/`
- Commits need an author email GitHub accepts for pushes, such as `pascalandy@users.noreply.github.com`; set it in the clone with `git -C _skills_private config user.email` when the global one is private
- Worktrees do not get `_skills_private/`, since git does not copy ignored folders; edit private skills in the main checkout

## Sync machines

GitHub's `main` is the source. Every machine in the fleet runs the same commands and hooks, and any of them can start a sync

- `just sync` pulls `main`, saves and pulls the private clone, and installs on the machine it runs on, without touching the others. It refuses a checkout off `main`. With `--dry-run` or `--check` it skips the pulls and previews the current checkout
- `just sync-fleet` brings every machine in `_skills_private/fleet.toml` to GitHub's `main`, the machine it runs on included; name machines to limit it, such as `just sync-fleet mbp`, by registry name or host. It fetches GitHub's `main`, or uses the last one fetched when GitHub is unreachable, and saves and pulls its own private clone first. Each machine then receives that commit over SSH, fast-forwards its checkout to it, saves and pulls its own private clone from GitHub, and runs `just install-skills`. The machine running it takes the same steps in a local shell
- A commit GitHub lacks reaches no other machine, so push it first. A machine whose checkout is off `main`, has uncommitted changes under `authoring/`, `skills/`, `scripts/`, or `justfile`, has commits GitHub lacks, or whose `_skills_private` is not a clone reports `needs-you` and stays untouched. Other edits, such as editor settings, do not block it
- An `offline` or `failed` machine gets one retry. It needs no queue: any later sync, from any machine, or its own `just sync`, catches it up
- Success prints nothing. `--verbose` prints GitHub's commit, its public skill count, and each machine's outcome and per-harness counts; `--dry-run` runs every check without changing anything
- `just sync-fleet --check` compares each machine's checkout and private clone with GitHub's `main` of each repository, and its installed skills per harness with its sources, then exits 1 naming each difference. It compares names and contents, so skills other tools installed do not count
- Editing a private skill fires no hook, so run `just sync` or `just sync-fleet` afterwards; each sync also saves the private edits of the machines it reaches
- The registry is tracked in the private repository, so every machine has it and hosts and accounts stay out of this public one. Each `path` is relative to that machine's home:

```toml
[machines.om1]
ssh = "pascal@om1.example.ts.net"
path = "projects/skills"

[machines.mbp]
ssh = "andy16@mbp16.example.ts.net"
path = "Documents/github_local/skills"
```

### Hooks

Run `lefthook install` once in each machine's main checkout. On `main` in a checkout that has the registry:

- A commit installs this machine at once. The other machines wait for GitHub: pushing `main` starts a background job that waits for the push to land, then syncs them
- A pull that brings commits installs this machine, then syncs the other machines in the background. A pull with nothing new fires no hook
- Worktrees, other branches, and checkouts without the registry skip all of it. A machine a sync reaches runs its merge with hooks off, so it never starts another sync

Background runs never make git wait on a sleeping laptop. They log to `~/.local/state/skills-sync/fleet.log` and send a desktop notification, `notify-send` on Linux or Notification Center on macOS, only when a machine needs you or fails; an offline machine waits for the next sync

## Ownership

- The installer keeps no state. It owns every name git history ever added under `skills/` or `authoring/commands/`, plus uncommitted skills still flattened in `skills/`. A shallow clone is refused because its history is incomplete
- It removes an owned name once no source provides it and never touches entries it did not publish, such as `~/.claude/skills/synced/`
- It also owns every package name the private clone's history ever added, so deleting a private skill and letting `just sync` commit the deletion removes its installed copies on every machine the deletion reaches. A private skill never committed is not owned; after deleting it, trash its installed copies yourself
- Installed copies are execution copies. Apply overwrites an in-place edit, so make edits in `authoring/` or the private clone
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
