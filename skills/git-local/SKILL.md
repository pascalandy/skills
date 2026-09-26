---
name: "git-local"
description: "Use when a task requires inspecting or working across an external GitHub repository's code and cloning it into the local cache is more effective than browsing source files online or making repeated GitHub API queries."
---

For code-level analysis or implementation, prefer the local repository cache over browsing individual source files online or making repeated `gh` API queries. Continue using `gh` for issues, pull requests, and repository metadata that do not require a local copy of the code.

# Git Repo Local

Use the local `opensrc` repository cache by default for GitHub repositories. Do not clone GitHub repositories anywhere outside this cache (no `/tmp`, no current working directory, no `gh repo clone` to its default path) unless the user explicitly asks for a throwaway checkout.

Install or update opensrc on Mac: `PNPM_HOME="$HOME/Library/pnpm" "$HOME/Library/pnpm/bin/pnpm" add -g --config.minimum-release-age=10080 --config.strict-dep-builds=true --allow-build=opensrc opensrc`

## Cache Location

Resolve the local `SKILLS_MONO` workspace once at the start of the task, then reuse its absolute path as `OPENSRC_ROOT` in every shell that needs it.

1. If `OPENSRC_ROOT` is non-empty, validate that directory and use it. An explicit path may be outside `$HOME`. If it is invalid, report the problem and ask for the correct path rather than silently choosing another workspace.
2. Otherwise, search beneath `$HOME` for directories named exactly `SKILLS_MONO`, including hidden and Git-ignored directories. Use `fd` when available, or `find` as a fallback. Do not assume a parent directory or choose a path based on the operating system.
3. Validate each candidate by checking that its `justfile` exists and that `just --justfile "<candidate>/justfile" --working-directory "<candidate>" --show opensrc-sync` succeeds. This inspects the required recipe without running it. If `just` is unavailable, report the missing prerequisite before continuing.
4. Resolve candidates to physical absolute paths and deduplicate them. Use the sole valid candidate. If several remain, show their paths and ask which to use. If none remain, ask for the workspace location. Report search errors as incomplete discovery rather than treating them as proof that no other workspace exists.

Finish resolution before any cache operation. Keep the resolved path for the current task; do not create a workspace or persist machine-specific configuration as part of discovery.

GitHub repositories are stored under:

```bash
"$OPENSRC_ROOT/opensrc/repos/github.com/<owner>/<repo>"
```

Example resolution:

```bash
github.com/anomalyco/opencode -> $OPENSRC_ROOT/opensrc/repos/github.com/anomalyco/opencode
```

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
2. Resolve `OPENSRC_ROOT` using [Cache Location](#cache-location), then check the expected local path:

```bash
repo_path="$OPENSRC_ROOT/opensrc/repos/github.com/<owner>/<repo>"
test -d "$repo_path" && find "$repo_path" -mindepth 1 -maxdepth 1 ! -name .DS_Store | head -1
```

3. If the path exists and contains files other than `.DS_Store`, refresh it through the SKILLS_MONO justfile before reading:

```bash
just --justfile "$OPENSRC_ROOT/justfile" --working-directory "$OPENSRC_ROOT" opensrc-sync <owner>/<repo>
```

4. If the path is missing or effectively empty, fetch it with:

```bash
opensrc --cwd "$OPENSRC_ROOT" --modify=false <owner>/<repo>
```

5. After refresh or fetch, verify the expected path exists and contains content before using it.
6. Optionally open the resolved repository in the local file manager when a graphical session is available:

```bash
case "$(uname -s)" in
  Darwin) open "$repo_path" ;;
  Linux) command -v xdg-open >/dev/null && xdg-open "$repo_path" ;;
esac
```

7. Use that path for `rg`, file reads, analysis, and references.
8. Tell the user the local path you used when reporting findings.

`--modify=false` is the default for direct `opensrc` fetches so `opensrc` does not silently update `.gitignore`, `tsconfig.json`, or `AGENTS.md` inside `$OPENSRC_ROOT`. Drop the flag only when the user explicitly opts in.

## Existing Checkout Rule

Do not run direct `opensrc` just because a repository was mentioned. First check whether this path already exists:

```bash
"$OPENSRC_ROOT/opensrc/repos/github.com/<owner>/<repo>"
```

If it exists and is non-empty, refresh it with the SKILLS_MONO justfile:

```bash
just --justfile "$OPENSRC_ROOT/justfile" --working-directory "$OPENSRC_ROOT" opensrc-sync <owner>/<repo>
```

Optionally open the resolved repo path using the platform command in step 6.

Use the direct `opensrc --cwd "$OPENSRC_ROOT" --modify=false <owner>/<repo>` fetch path only for missing or empty checkouts.

## Troubleshooting

When `opensrc` fails, the cache looks inconsistent, or you need to list/remove/clean fetched sources, load `references/opensrc-operations.md` from this skill directory.

## Branches, Tags, and Git History

`opensrc` stores source snapshots for code reading. It may remove `.git` metadata after fetching, so do not assume `git pull` is available in cached repos. Use `just opensrc-sync <owner>/<repo>` from `$OPENSRC_ROOT` to refresh existing cached repos. If the user specifically needs git history, branches, remotes, or a writable checkout, say so and create a separate task-specific clone or worktree outside the shared opensrc cache.

For URLs with branch paths, preserve the repository path for cache lookup:

```bash
https://github.com/owner/repo/tree/main/subdir -> owner/repo
```

After resolving the local repo root, inspect the requested subdirectory inside it when applicable.

## Do Not

- Do not default to cloning GitHub repositories outside `$OPENSRC_ROOT` (no `/tmp`, no current working directory, no `gh repo clone` / `git clone` to a default path)
- Do not edit files inside the shared opensrc cache unless the user explicitly asks to modify that cached source
- Do not delete or replace cached repositories unless the user asks for a refresh or repair
- Do not pass `--modify=true` (or omit `--modify=false`) unless the user opts in to letting `opensrc` rewrite `.gitignore`, `tsconfig.json`, or `AGENTS.md` in the workspace
