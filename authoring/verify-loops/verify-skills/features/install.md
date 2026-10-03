# Install

`just install-skills` copies every public skill, every private skill, and each `commands/*.md` into the agent folders of one machine profile. It removes names the repository once published and no longer provides. Here it writes into the run's test home, with an empty private folder.

## Sub-features

- `install-apply`: each skill lands in every skill folder of the profile, identical to `skills/<name>/`
- `install-commands`: each command lands as a file for Claude Code, Pi, and OpenCode, and as a skill in Codex's skill folder
- `install-current`: after an install, `--check` finds nothing left to change

## How to get to it (user POV)

- `just install-skills`, directly or through `just sync`, `just sync-fleet`, or the lefthook hooks on `main`
- `just install-skills --dry-run` or `--check` to preview

## Driving it with just

Preconditions:

- Compile passed in this run

- **Install and check.** Run the block. It prints `install: exit 0` and `install-check: exit 0`. `install.out` holds one `add` line per entry, and `install-check.out` is empty.
- **Compare with the checkout.** The same block prints `install-diff: exit 0`, and `install-diff.out` is empty: the installed Claude Code skills and commands match `skills/` and `commands/` file for file.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  record install just install-skills --private-root "$RUN/private" &&
  record install-check just install-skills --check --private-root "$RUN/private" &&
  record install-diff sh -c 'diff -r -x __pycache__ -x ".*_cache" -x node_modules -x .DS_Store skills "$HOME/.claude/skills" &&
    diff -r commands "$HOME/.claude/commands"' )
```

## Gotchas

- Without the run env, `just install-skills` writes into the live agent folders. Every block loads it first
- The empty `$RUN/private` keeps the private clone out of the run. Without `--private-root`, a worktree also installs the main checkout's `_skills_private/`
- An install also recompiles the checkout's `skills/` and deletes cache-only leftover folders in `authoring/` and `skills/`. Those are its only writes outside the run folder
- Installs from one repository, worktrees included, take turns through a lock in its git folder. An install waits for a concurrent one and exits 75 after `--timeout`; rerun it
- On om1, the profile skips `apple-mail`. A public `apple-mail` would show in `install-diff.out` as an expected difference
