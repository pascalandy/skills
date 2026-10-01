---
name: "git-local"
description: "Use when a task requires inspecting or working across an external GitHub repository's code and cloning it into the local cache is more effective than browsing source files online or making repeated GitHub API queries."
kind: "dev"
---

For code-level analysis or implementation, prefer the local repository cache over browsing individual source files online or making repeated `gh` API queries. Continue using `gh` for issues, pull requests, and repository metadata that do not require a local copy of the code.

# Git Repo Local

Use the local `opensrc` repository cache by default for GitHub repositories. Do not clone GitHub repositories anywhere outside this cache (no `/tmp`, no current working directory, no `gh repo clone` to its default path) unless the user explicitly asks for a throwaway checkout.

Install or update opensrc on Mac: `PNPM_HOME="$HOME/Library/pnpm" "$HOME/Library/pnpm/bin/pnpm" add -g --config.minimum-release-age=10080 --config.strict-dep-builds=true --allow-build=opensrc opensrc`

## Cache Location

This configuration is for Pascal's Mac only. Before any cache operation, initialize these variables in that shell, replacing inherited values:

```bash
export OPENSRC_HOME="/Users/andy16/Documents/github_local/SKILLS_MONO/opensrc"
OPENSRC_ROOT="${OPENSRC_HOME%/opensrc}"
```

`OPENSRC_HOME` is the cache itself; `OPENSRC_ROOT` is its parent workspace. The installed CLI uses `OPENSRC_HOME` for storage. Its `--cwd` flag only controls lockfile lookup. Do not use `--cwd` to select the cache, append another `opensrc`, or pass the obsolete `--modify` flag.

Verify that this Mac's cache directory exists, its physical path matches `OPENSRC_HOME`, and the refresh recipe is available:

```bash
test "$(uname -s)" = Darwin &&
  test -d "$OPENSRC_HOME" &&
  test "$(cd "$OPENSRC_HOME" && pwd -P)" = "$OPENSRC_HOME" &&
  just --justfile "$OPENSRC_ROOT/justfile" --working-directory "$OPENSRC_ROOT" --show opensrc-sync
```

If validation fails or a prerequisite is missing, stop and report it. Do not search for another workspace, create a replacement, or fall back to the current directory, `/Users/andy16/opensrc`, or the CLI's default `~/.opensrc`. Do not change shell profiles or the tool installation to configure the cache.

Read repository locations from `$OPENSRC_HOME/sources.json` or `opensrc list --json`. Match `repos[].name` to `github.com/<owner>/<repo>` and resolve its `path` relative to `OPENSRC_HOME`. Existing snapshots may use `repos/github.com/<owner>/<repo>`; new downloads may add a version directory. Do not guess that last component. Before using a recorded path, verify that it resolves inside `OPENSRC_HOME` and contains source files.

## Trigger

Use this skill when:

- The user asks to look on GitHub, inspect a GitHub repo, clone a GitHub repo, or compare against a GitHub repo
- The user provides a GitHub URL such as `https://github.com/owner/repo`
- The user provides GitHub shorthand such as `owner/repo`
- The user provides an SSH form such as `git@github.com:owner/repo.git`
- You encounter a GitHub repository URL while researching or implementing and need local code context

## Workflow

1. Normalize the repository reference to `owner/repo`:
   - `https://github.com/owner/repo` -> `owner/repo`
   - `https://github.com/owner/repo.git` -> `owner/repo`
   - `git@github.com:owner/repo.git` -> `owner/repo`
   - `git@github.com:owner/repo` -> `owner/repo`
   - `github.com/owner/repo` -> `owner/repo`
   - `owner/repo` stays as-is
   - Strip any trailing `.git` suffix
2. Initialize and validate the fixed cache using [Cache Location](#cache-location). Look up the recorded repository path and check for files other than `.DS_Store`. If an unregistered directory already exists for that repository, inspect it and load the troubleshooting reference before fetching over it.

3. If the path exists and contains files other than `.DS_Store`, refresh it through the SKILLS_MONO justfile before reading:

```bash
OPENSRC_HOME="$OPENSRC_HOME" just --justfile "$OPENSRC_ROOT/justfile" --working-directory "$OPENSRC_ROOT" opensrc-sync <owner>/<repo>
```

4. If the path is missing or effectively empty, fetch it with:

```bash
OPENSRC_HOME="$OPENSRC_HOME" opensrc fetch <owner>/<repo>
```

5. After a successful refresh or fetch, reread the recorded path into `repo_path`; it may have changed to include a version directory. Verify its physical location is inside `OPENSRC_HOME` and that it contains source files before using it. If the operation fails, report the failure rather than claiming the cache is current or trying another destination.
6. Optionally open the resolved repository in the local file manager when a graphical session is available:

```bash
case "$(uname -s)" in
  Darwin) open "$repo_path" ;;
  Linux) command -v xdg-open >/dev/null && xdg-open "$repo_path" ;;
esac
```

7. Use that path for `rg`, file reads, analysis, and references.
8. Tell the user the local path you used when reporting findings.

## Existing Checkout Rule

Follow the lookup and refresh sequence in [Workflow](#workflow). A repository mention alone does not justify a direct fetch. Use direct fetch only for a missing or empty checkout; preserve existing source when an operation fails.

## Troubleshooting

When `opensrc` fails, the cache looks inconsistent, or you need to list/remove/clean fetched sources, load `references/opensrc-operations.md` from this skill directory.

## Branches, Tags, and Git History

`opensrc` stores source snapshots for code reading. It may remove `.git` metadata after fetching, so do not assume `git pull` is available in cached repos. Refresh through [Workflow](#workflow), retaining the fixed cache environment. If the user specifically needs git history, branches, remotes, or a writable checkout, say so and create a separate task-specific clone or worktree outside the shared opensrc cache.

For URLs with branch paths, preserve the repository path for cache lookup:

```bash
https://github.com/owner/repo/tree/main/subdir -> owner/repo
```

After resolving the local repo root, inspect the requested subdirectory inside it when applicable.

## Do Not

- Do not default to cloning GitHub repositories outside `$OPENSRC_HOME` (no `/tmp`, no current working directory, no `gh repo clone` / `git clone` to a default path)
- Do not edit files inside the shared opensrc cache unless the user explicitly asks to modify that cached source
- Do not delete or replace cached repositories unless the user asks for a refresh or repair
- Do not modify the workspace's `.gitignore`, `tsconfig.json`, or `AGENTS.md` as part of fetching source
