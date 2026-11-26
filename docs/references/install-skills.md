---
name: Install skills
description: Profiles, the private clone, ownership, syncing this machine, and cutover for just install-skills
tags:
  - area/ea
  - kind/doc
  - topic/playbook
  - status/stable
date_created: 2026-09-26
date_updated: 2026-11-26
---

`just install-skills` installs public skills, every package in the private clone's `authoring/`, and `commands/*.md` into one machine profile's agent directories. `just install-skills --help` lists profiles, targets, and flags. The prospective public source is the same in preview and apply

## Run it

- The profile follows the OS: `mac` on macOS, `linux` elsewhere. Pass `--profile` to override
- Every package under `skills-private/authoring/` installs; packages elsewhere in the clone, such as `skill_archived/`, never do. `--private-root PATH` names another private repository root
- A name that is both public and private stops the install, a dry run included, and the error names both paths: remove the public package to keep the skill private, or delete the private copy to publish it
- A run answers `{"ok":true,"changes":[...]}`, one change per entry, such as `["add","~/.claude/skills/concise"]`, and `{"ok":true}` when every target is current. `--dry-run` answers the same without writing; `--check` fails when a selected target needs work, with the changes beside the error. `-v` logs how many entries each target holds current
- Applies from one repository, its worktrees included, take turns through a lock in its git directory, so overlapping runs, such as two worktrees installing at once, leave the newest working tree installed. An apply waits up to `--timeout` for another, then exits 75; previews and checks do not wait
- Git keeps a directory that still holds ignored files, so moving or renaming a skill can leave its old folder in `authoring/` or `skills/` behind. An apply deletes each such category, package, or skill folder when it holds only caches: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, `node_modules/`, or `.DS_Store`. A leftover holding any other ignored file stays, and the apply fails once the install is done, naming the file. A file saved outside those caches during cleanup survives. If cleanup cannot scan or delete a leftover, the apply also fails once the install is done

## Agent instructions

When the private root exists, `just install-skills` also reads two masters under its `authoring/integrations/fleet/references/`:

| Source | Destination |
|---|---|
| `AGENTS-HARNAIS.md` | `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.pi/agent/AGENTS.md`, `~/.config/opencode/AGENTS.md`, `~/.gemini/GEMINI.md` |
| `AGENTS-PROJECTS.md` | `<projects>/AGENTS.md` |
| `@AGENTS.md` followed by a newline | `<projects>/CLAUDE.md` |

`<projects>` is the parent of the resolved private root, including an override. Both profiles install all seven files and create missing parent directories, even for an absent harness. Grok reads Claude's file, so the installer creates no `~/.grok/AGENTS.md`

Without a private root, the public install leaves instruction files alone. With a private root, either missing master fails the run before any installation. A standalone install uses the local clone without network access. `just sync` updates the private clone before installation

The seven files share the skills' plan and JSON report. An unchanged file produces no change. Preview and check compare their bytes too, so `--check` sees missing or different instructions. Reports contain paths and actions, never file contents

A destination symlink becomes a regular file, even when dangling. A directory or another non-file destination is a conflict that blocks the whole install. When contents differ, the old bytes go into a unique backup under `~/.cache/agents-instructions/`. A link without file contents is backed up as a link. An identical symlink target needs no content backup. Each destination keeps its five newest backups, separately from files with the same name elsewhere

A failed backup cancels that destination's replacement. Each file is replaced through a temporary file and rename. If a later write fails, the failure report lists the destinations already changed; rerunning installs what remains

Instruction files are installed copies. Their masters change through a skills-private worktree and PR

## Commands

- Claude Code, Pi, and OpenCode read each command as a file. Codex dropped custom prompts and Antigravity has none, so each command also installs as a skill in `~/.codex/skills` and `~/.gemini/config/skills`, called as `$name` in Codex and `/name` in Antigravity, with the command's description. Pi and OpenCode read neither folder, so no agent sees a command twice
- T3 runs Antigravity with its own config folder, whose `skills` links to `~/.gemini/config/skills`, so only that folder reaches it. `~/.gemini/skills` and `~/.agents/skills` serve the standalone CLI only
- A command that shares a skill's name stops the run: Claude Code would hide the command, and Codex and Antigravity would need one folder for both. `scripts/tests/test_commands.py` catches a clash with a public skill in CI
- Pi and OpenCode read `$1`, `$2`, … as arguments even inside a word, so `$2nd-pass` reaches the agent as `nd-pass`. The same test rejects a digit placeholder followed by a letter
- Each run removes the commands earlier versions put in `~/.codex/prompts` and `~/.config/agents/commands`, which Codex and Amp no longer read

## Private skills

Private skills live in the private repository `pascalandy/skills-private`, cloned once per machine at `skills-private/`, beside the main checkout in the same projects folder. Its URL is this checkout's `origin` with `skills` renamed to `skills-private`, so each machine reaches GitHub the way its public checkout does

- The clone mirrors this repository: packages that install live in `authoring/<category>/<skill>/`, and `skill_archived/` holds packages that never install, such as the skills `jsm` installs. Move a package into `authoring/` to install it, and back to `skill_archived/` to retire it
- The repository is the source of truth. Change a private skill in a worktree of `skills-private` and open a PR there, never in the clone. After the merge, `just sync` pulls and installs it
- `scripts/sync_private.py` manages the clone; `just sync` runs it. It clones a missing folder, then fast-forwards `main` to GitHub's. A folder that is not a clone, a clone off `main`, one with uncommitted edits, or one with commits GitHub lacks stops it with exit 1, untouched: it never commits or pushes
- Worktrees of this repository share the main checkout's clone, since it sits beside the main checkout
- The private sync names a refused SSH key and asks you to unlock the SSH agent or load the key. It names an HTTPS login that no git credential helper answered, and the git config key to check. It treats network failures as temporary. Every clone or fetch failure includes a command to inspect it locally, without copying Git's output into the report

## Sync this machine

- `just sync` pulls `main` and the private clone, and installs on the machine it runs on. It refuses a checkout off `main`. With `--dry-run` or `--check` it skips the pulls and previews the current checkout
- Keep the main checkout on `main`, without edits, and do branch work in a worktree, so a pull or an install never meets your work
- The justfile imports `~/.config/skills/local.just` when it exists. A machine keeps its own recipes there, outside git, such as one that merges a PR and deploys it

## Ownership

- The installer keeps no state. It owns every name git history ever added under `skills/`, `commands/`, or the former `authoring/commands/`, plus uncommitted skills still compiled in `skills/`. A shallow clone is refused because its history is incomplete
- It removes an owned name once no source provides it and never touches entries it did not publish, such as `~/.claude/skills/synced/`
- It also owns every package name the private clone's history ever added under `authoring/`, so deleting a private skill, or moving it to `skill_archived/`, in a merged PR of `skills-private` removes its installed copies at each machine's next install. A name only ever added elsewhere, such as an archived skill `jsm` installed, stays untouched, unless this repository's history owns it too, as it owns `cass`. A private skill never committed is not owned; after deleting it, trash its installed copies yourself
- Installed copies are execution copies. Apply overwrites an in-place edit, so make edits in `authoring/`, `commands/`, or a worktree of `skills-private`
- To make a public skill private, remove it from `authoring/` in a PR, then add its package to `authoring/` of `skills-private` in a PR there once the first lands. An install while both copies exist stops and names them
- To promote a private skill, add it to `authoring/` in a PR, and remove the private copy in a `skills-private` PR merged right before it. An install while both copies exist stops and names them

## Cutover

Get the machine owner's approval before starting the cutover. Move one machine at a time from the old dotfiles skill engine and stop its writers before this installer applies any changes.

| Example machine | OS | Profile |
|---|---|---|
| `laptop.example` | macOS | `mac` |
| `workstation.example` | Linux | OS default |

The commands below use the OS default. Carry any `--profile` or `--private-root` override through steps 4 to 6.

1. **Stop the old writers.** The old engine has no timer; it runs only when one of these is called. Confirm that nothing calls them during the cutover, including `fleet-sync-skills` from another machine, and list which exist:
   - `~/.local/bin/`: `dotfiles-release`, `dotfiles-skills`, `sync-skills`, `fleet-sync-skills`, and any machine-specific `*-sync-skills` wrapper
   - `~/justfile` recipes `skills-update`, `sync-skills`, `pull-dotfiles`, and any machine-specific recipe that calls the old engine
   - The release clone in `~/.local/share/dotfiles-release/`
2. **Preserve old state.** Copy `~/.local/state/dotfiles-skills/` outside every target. If `~/.local/state/dotfiles-skills/pending.json` exists, stop: the old engine has an unfinished recovery
3. **Select the source.** Use a skills checkout at a reviewed `main` revision. Record the machine, `git rev-parse HEAD`, the profile, and the private packages already installed there. Check that the merged private `main` holds in `authoring/` exactly the packages that remain private, and fix any gap through a worktree of `skills-private` and a PR. If the private clone is elsewhere, pass its path, for example `--private-root "$HOME/projects/team-skills"`
4. **Preview.** Run `just install-skills --dry-run` with that source, then `just install-skills --check`. An in-place edit shows as `update`; move one worth keeping into `authoring/`, or into `authoring/` of `skills-private` through a PR, first. Resolve each skill or command conflict, a symlink or wrong type at a target path, by hand. Instruction symlinks follow the [agent instructions](#agent-instructions) rules
5. **Apply after approval.** Show the machine owner the preview. Once they approve it, run `just install-skills` with the same overrides. Run `just install-skills --check` with those overrides and confirm it exits 0
6. **Verify discovery.** Run `just skills-discover` with the same overrides. Claude Code has no command that lists its skills, so the check leaves it out: start a new Claude Code session and confirm the expected skills appear
7. **Retire the old engine.** Only after step 6 passes, move the step 1 writers, the release clone, `~/.local/state/dotfiles-skills/`, and any `~/.local/state/install-skills/` left by an earlier installer version to the trash. Keep the step 2 copy until the machine owner discards it. Switch the machine's chezmoi source to dotfiles `main`, which no longer ships the old writers. chezmoi does not delete files removed from its source, so the trash step is still needed

Keep `~/.local/share/dotfiles/machine-identity.sh`, `~/.local/share/dotfiles/command-context.sh`, and `chezmoi-apply-*` wrappers. The old bootstrap installed them too, but they are not skill writers

## Related

- [[script-conventions]]
- [[release]]
