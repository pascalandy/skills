---
name: "git-local"
description: "Use instead of `git clone` when a request gives a GitHub URL or `owner/repo`, or when a task needs the code of an external GitHub repository."
kind: "dev"
---

This skill replaces `git clone`. It puts a GitHub repository in the `opensrc` cache and reports its path. Use `gh` for issues, pull requests, and repository metadata that need no copy of the code.

Keep every copy in the cache, never in `/tmp`, the current folder, or the default path of `gh repo clone` or `git clone`. Make a separate checkout only when the user asks for one, or for git history, as [Branches, Tags, and Git History](#branches-tags-and-git-history) says.

## Prerequisites

Confirm each tool before the first step. If one is missing, stop and give the user its install command; do not install it yourself.

| Tool | Where | Linux | macOS | Confirm |
|---|---|---|---|---|
| `opensrc` | the cache machine | `mise use -g npm:opensrc` | `PNPM_HOME="$HOME/Library/pnpm" "$HOME/Library/pnpm/bin/pnpm" add -g --config.minimum-release-age=10080 --config.strict-dep-builds=true --allow-build=opensrc opensrc` | `opensrc --version` |
| `uv` | this machine | `mise use -g uv` | `brew install uv` | `uv --version` |
| `rg`, for code search | the cache machine | `mise use -g ripgrep` | `brew install ripgrep` | `rg --version` |

The install commands assume `mise` on Linux, and Homebrew and pnpm on macOS. On another machine, confirm a tool with `ssh <host> '<confirm command>'`.

## Cache machine

When the `fleet` skill is installed, its `references/fleet.toml` names the machine that holds the cache: the one with an `opensrc` key. Pass that file as `--fleet` to every [Workflow](#workflow) run; on another machine, the script runs opensrc through `ssh`. Without `fleet`, the cache is opensrc's default on this machine: `$OPENSRC_HOME`, or `~/.opensrc`.

## Workflow

1. Normalize the repository reference to `owner/repo`:
   - `https://github.com/owner/repo` -> `owner/repo`
   - `https://github.com/owner/repo/tree/main/subdir` -> `owner/repo`, then read `subdir` inside it
   - `git@github.com:owner/repo.git` -> `owner/repo`
   - `github.com/owner/repo` -> `owner/repo`
   - Strip any trailing `.git` suffix
2. Fetch or refresh it:

   ```bash
   uv run <this skill's folder>/scripts/opensrc_sync.py --max-age 24h [--fleet <fleet folder>/references/fleet.toml] <owner>/<repo>
   ```

   It fetches a missing repository and refreshes a copy older than 24 hours. Done when it answers `"ok":true` with `repos[0].path`, and `machine` when the cache is on another machine. On a failure, report its `errors` and read [OpenSrc Operations](references/opensrc-operations.md); never fetch into another folder
3. Report the path, as `<machine>:<path>` when the answer names a `machine`
4. If the request names only a repository, stop here. Do not read the code, summarize it, or ask for a next task
5. If a task needs the code, search and read it at that path. When the answer names a `machine`, run each command there through the `ssh` value of that machine in `fleet.toml`, such as `ssh <ssh> 'rg -n "pattern" <path>'`
6. When the cache is on this machine and a graphical session is available, optionally open the path with `open` on macOS or `xdg-open` on Linux

`opensrc_sync.py` without a repository refreshes every cached repository, downloading each one again; run it so only when the user asks. `--help` lists its options.

## Branches, Tags, and Git History

`opensrc` stores source snapshots without `.git`, for reading code. If the user needs git history, branches, remotes, or a writable checkout, say so and create a task-specific clone or worktree outside the cache.

## Do Not

- Do not edit files inside the cache unless the user explicitly asks to modify that cached source
- Do not delete or replace cached repositories unless the user asks for a refresh or repair
- Do not modify the workspace's `.gitignore`, `tsconfig.json`, or `AGENTS.md` as part of fetching source
