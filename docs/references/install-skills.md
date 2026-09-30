---
name: Install skills
description: Profiles, the private clone, ownership, fleet sync from any machine, hooks, and cutover for just install-skills
tags:
  - area/ea
  - kind/doc
  - topic/playbook
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-30
---

`just install-skills` installs current local `authoring/`, every package in the private tree, and `authoring/commands/*.md` for explicit local testing. It still flattens into the authoring checkout's `skills/`. `just sync` and `just sync-fleet` instead install committed `skills/` and commands from GitHub's published `main`. Their previews and applies use the same published source. Run `just install-skills --help` for profiles, targets, and flags

## Run it

- The profile follows the OS: `mac` on macOS, `om1` elsewhere. Pass `--profile` to override
- Every package under `_skills_private/` installs; `--private-root PATH` points to another private tree
- A name that is both public and private stops the run; delete the stale copy it names
- A run prints one line per change, such as `add\t~/.claude/skills/concise`, and nothing when every target is current. `--dry-run` prints the same lines without writing; `--check` exits 1 and lists them on stderr when a selected target needs work. `--json` prints the per-target report instead
- Applies from one repository, its worktrees included, take turns through a lock in its git common directory. Published deployments also lock the tool-owned detached checkout under that directory. An older deployment cannot replace a newer published revision. An apply waits up to `--timeout` for another, then exits 75; previews and checks of installed copies do not wait

## Commands

- Claude Code, Pi, and OpenCode read each command as a file. Codex dropped custom prompts, so each command also installs as a skill in `~/.codex/skills`, called as `$name`, with the command's description. Pi and OpenCode do not read that folder, so no agent sees a command twice
- A command that shares a skill's name stops the run: Claude Code would hide the command, and Codex would need one folder for both. `scripts/tests/test_commands.py` catches a clash with a public skill in CI
- Pi and OpenCode read `$1`, `$2`, … as arguments even inside a word, so `$2nd-pass` reaches the agent as `nd-pass`. The same test rejects a digit placeholder followed by a letter
- Each run removes the commands earlier versions put in `~/.codex/prompts` and `~/.config/agents/commands`, which Codex and Amp no longer read

## Private skills

Private skills live in the private repository `pascalandy/skills-private`, cloned inside this checkout at `_skills_private/`. Its URL is this checkout's `origin` with `skills` renamed to `skills-private`, so each machine reaches GitHub the way its public checkout does

- Git uses the nearest `.git` above the current directory. Inside `_skills_private/`, git commands act on the private repository; anywhere else, on the public one
- This repository's `.gitignore` line `/_skills_private/` keeps the clone and its `.git` out of the public repository; it is not a submodule. Keep that line, and never `git add -f` the folder
- `scripts/sync_private.py` manages the original checkout's clone; `just sync` and `just sync-fleet` pass that checkout explicitly. It clones a missing folder, commits uncommitted edits as `🧰 skill: private: save edits from <machine>`, pulls with rebase, and pushes. A folder that is not a clone, or a clone off `main`, stops it untouched. Edits that conflict with GitHub stay committed on that machine and stop it; resolve them with `git pull --rebase` in `_skills_private/`
- Commits need an author email GitHub accepts for pushes, such as `pascalandy@users.noreply.github.com`; set it in the clone with `git -C _skills_private config user.email` when the global one is private
- Worktrees do not get `_skills_private/`, since git does not copy ignored folders; edit private skills in the main checkout

## Sync machines

GitHub's `main` is the public source. Every machine keeps its authoring checkout and existing private clone. A separate detached `published-deployment` worktree under the Git common directory holds the published revision and the code that deploys it. The authoring checkout supplies Git objects and never switches branch, moves HEAD, rewrites its index, or installs its working tree during sync

- `just sync` fetches public `main`, saves and pulls the existing private clone, and installs the published snapshot on this machine. It also works on a dirty, non-main, detached, or locally ahead authoring checkout. With `--dry-run` or `--check`, it does not save private edits or write installs; it can refresh the tool-owned published checkout
- `just sync-fleet` deploys to every registry machine, including the initiating machine, or to named machines such as `just sync-fleet mbp`. It fetches GitHub's `main`, or uses the latest known published revision when the network is temporarily unavailable. It saves and pulls the initiating machine's private clone before sending the public commit over SSH. Each reached machine updates only its detached published worktree, saves and pulls its own existing private clone, and installs the committed snapshot. A fetched commit that predates a machine's installed published revision cannot roll it back
- A commit GitHub lacks reaches no other machine, so push it first. Public authoring branches and edits do not block deployment. A machine whose `_skills_private` is not a clone reports `needs-you` and stays untouched; other machines continue. A private conflict stays committed in that existing clone for manual resolution
- An `offline` or `failed` machine waits for the next sync. It needs no queue: any later sync, from any machine, or its own `just sync`, catches it up. A run whose only failures are temporary, such as offline machines, exits 75 instead of 1
- A run prints `synced<TAB>NAME<TAB>SHA` for each machine it changed, and nothing when none needed a change; `--dry-run` runs every check without changing anything and prints `ready<TAB>NAME<TAB>SHA` for each machine a sync would change: one behind GitHub, or one whose private clone or installed skills would change. A failure lists every machine's status on stderr. `--verbose` adds GitHub's commit, its public skill count, and each machine's outcome and changes; `--debug` adds the remote output
- `just sync-fleet --check` compares each machine's published checkout and private clone with GitHub's `main` of each repository, and its installed skills per harness with the published snapshot, then exits 1 naming each difference on stderr. It compares names and contents, so skills other tools installed do not count
- Editing a private skill fires no hook, so run `just sync` or `just sync-fleet` afterwards; each sync also saves the private edits of the machines it reaches
- The registry is `fleet.toml`, tracked in the private repository, so every machine has it and hosts and accounts stay out of this public one. The private `private-network` skill ships it in `references/`, so agents read it too; the sync uses the only `fleet.toml` in the clone, wherever that skill lives. It reads `ssh` and `path`, relative to that machine's home; other keys are notes for agents:

```toml
[machines.om1]
ssh = "pascal@om1.example.ts.net"
path = "projects/skills"

[machines.mbp]
ssh = "andy16@mbp16.example.ts.net"
path = "Documents/github_local/skills"
```

### Hooks

Run `lefthook install` once in each machine's main checkout. On `main` in a checkout that has the private clone:

- A local commit installs nothing. Pushing `main` starts a background job that waits for the push to reach GitHub, then deploys every registry machine, including the initiating machine
- A pull that brings commits starts the same background deployment of published `main`. A pull with nothing new fires no hook
- Worktrees, other branches, and checkouts without the private clone skip all of it. A clone without the registry warns and skips it too, without blocking git. Fleet sync moves only detached worktrees and never triggers authoring hooks

Background runs never make git wait on a sleeping laptop. They log to `~/.local/state/skills-sync/fleet.log` and send a desktop notification, `notify-send` on Linux or Notification Center on macOS, only when a machine needs you or fails; an offline machine waits for the next sync

## Ownership

- The installer keeps no ownership database. The local authoring mode owns names git history ever added under `skills/` or `authoring/commands/`, plus uncommitted skills flattened in `skills/`. Published mode reads ownership history and content from the detached revision only; it rejects a dirty or attached published source. A shallow clone is refused because its history is incomplete
- It removes an owned name once no source provides it and never touches entries it did not publish, such as `~/.claude/skills/synced/`
- It also owns every package name the private clone's history ever added, so deleting a private skill and letting `just sync` commit the deletion removes its installed copies on every machine the deletion reaches. A private skill never committed is not owned; after deleting it, trash its installed copies yourself
- Installed copies are execution copies. Apply overwrites an in-place edit, so make edits in `authoring/` or the private clone
- To promote a private skill, move it into `authoring/`, delete the private copy, and rerun

## First deployment of the new launcher

The old `just sync`, `just sync-fleet`, and hooks cannot run code that was not present when their authoring checkout was created. Before the first live deployment, get approval for each machine. Upgrade its authoring checkout to the launcher version with an ordinary no-clobber Git fast-forward, only when Git can do so without overwriting local work. On `main`, the no-clobber upgrade is `git -C "$root" fetch origin main` followed by `git -C "$root" merge --ff-only origin/main`, with `root` set to the original checkout path. A dirty checkout that blocks that upgrade is a migration blocker; do not reset, stash, or overwrite it. Once the launcher version is present, later syncs leave the authoring HEAD, branch, index, and files unchanged even if that checkout falls behind or becomes dirty

If the old dirty-gated sync cannot perform the first deployment, bootstrap directly from the repository's published detached worktree. Set `root` to the original checkout's absolute path and `registry` to the actual `fleet.toml` under its existing `_skills_private/`. This does not use the old sync or write the authoring checkout. Run these commands only after the old writers are stopped and live deployment is approved:

```sh
root="$HOME/Documents/github_local/skills"
registry="$root/_skills_private/integrations/private-network/references/fleet.toml"
git -C "$root" fetch origin main
common=$(git -C "$root" rev-parse --path-format=absolute --git-common-dir)
git -C "$root" -c core.hooksPath=/dev/null worktree add --detach "$common/published-deployment" origin/main
uv run "$common/published-deployment/scripts/sync.py" --worker --author-root "$root"
uv run "$common/published-deployment/scripts/sync_fleet.py" --worker --author-root "$root" --fleet "$registry" --dry-run
```

The worktree-add command is for a missing deployment worktree only. If one exists, do not overwrite it: run the new launcher, which checks ownership and reconciles a missing registered tool worktree. Inspect the dry run before applying `just sync-fleet`. On a machine without a private clone, the local `sync.py` bootstrap creates the single original `_skills_private/` first. The `registry` path varies by machine; locate the one file in that clone before setting it

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
3. **Select the source.** Use a reviewed GitHub `main` revision in the detached published checkout. Record the machine, published revision, profile, and private packages already installed there. Make the original private tree hold exactly the packages that remain private
4. **Preview.** From the clean detached published checkout, run `just install-skills --snapshot --private-root PATH --profile PROFILE --dry-run --json`, then the same with `--check --json`. Set PATH to the original checkout's private clone. An in-place edit shows as `update`; move one worth keeping into `authoring/` or the private tree first. Resolve each conflict, a symlink or wrong type at a target path, by hand
5. **Apply after approval.** Show Pascal the preview. After approval, run `just install-skills --snapshot --private-root PATH --profile PROFILE` from the same published checkout. A follow-up `--snapshot --private-root PATH --check --json` from that checkout must exit 0
6. **Verify discovery.** Run `just skills-discover --profile PROFILE` with the same `--private-root`. An unavailable native adapter remains unverified, so start a new session in that agent and confirm the expected skills appear
7. **Retire the old engine.** Only after step 6 passes, move the step 1 writers, the release clone, `~/.local/state/dotfiles-skills/`, and any `~/.local/state/install-skills/` left by an earlier installer version to the trash. Keep the step 2 copy until Pascal discards it. Switch the machine's chezmoi source to dotfiles `main`, which no longer ships the old writers. chezmoi does not delete files removed from its source, so the trash step is still needed

Keep `~/.local/share/dotfiles/machine-identity.sh`, `~/.local/share/dotfiles/command-context.sh`, and `chezmoi-apply-mbp`. The old bootstrap installed them too, but they are not skill writers

## Related

- [[script-conventions]]
- [[release]]
