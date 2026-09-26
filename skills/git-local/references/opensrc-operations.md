# OpenSrc Operations

Use this reference when `opensrc` fails, the local cache looks inconsistent, or the task needs listing/removal/cleanup behavior.

Before running these commands, resolve `OPENSRC_ROOT` using [Cache Location](../SKILL.md#cache-location). Reuse the task's resolved path if it is already available.

## Help Surface

```text
Usage: opensrc [options] [command] [packages...]

Fetch source code for packages to give coding agents deeper context

Arguments:
  packages                           packages or repos to fetch (e.g., zod, pypi:requests,
                                     crates:serde, owner/repo)

Options:
  -V, --version                      output the version number
  --cwd <path>                       working directory (default: current directory)
  --modify [value]                   allow/deny modifying .gitignore, tsconfig.json, AGENTS.md
  -h, --help                         display help for command

Commands:
  list [options]                     List all fetched package sources
  remove|rm [options] <packages...>  Remove fetched source code for packages or repos
  clean [options]                    Remove all fetched packages and/or repos
```

## Standard Commands

Always pass the shared workspace via `--cwd "$OPENSRC_ROOT"` and keep `--modify=false` unless the user opts in to letting `opensrc` rewrite workspace files:

```bash
opensrc --cwd "$OPENSRC_ROOT" --modify=false owner/repo
opensrc list --cwd "$OPENSRC_ROOT"
opensrc list --json --cwd "$OPENSRC_ROOT"
opensrc remove --cwd "$OPENSRC_ROOT" owner/repo
opensrc clean --repos --cwd "$OPENSRC_ROOT"
```

`--modify=false` keeps `opensrc` from updating `.gitignore`, `tsconfig.json`, or `AGENTS.md` in `$OPENSRC_ROOT`. Drop it only when the user explicitly asks for those edits.

## Existing Repo Check

Before fetching, check for real content:

```bash
repo_path="$OPENSRC_ROOT/opensrc/repos/github.com/owner/repo"
test -d "$repo_path" && find "$repo_path" -mindepth 1 -maxdepth 1 ! -name .DS_Store | head -1
```

If this prints a path, use the existing cache. If it prints nothing, treat the cache as absent or incomplete.

## Common Issues

### Existing directory is empty or only contains `.DS_Store`

This can happen after an interrupted or failed fetch. If the directory has no useful source files, send only that repository directory to the trash and fetch again:

```bash
trash "$OPENSRC_ROOT/opensrc/repos/github.com/owner/repo"
opensrc --cwd "$OPENSRC_ROOT" --modify=false owner/repo
```

### `ENOTEMPTY` while fetching

`opensrc` may fail while trying to replace a directory that already exists. First inspect the directory. If it contains real source files, use it instead of refetching. If it is incomplete, send only that one repository directory to the trash and fetch again.

### Need to verify what `opensrc` knows

Use:

```bash
opensrc list --json --cwd "$OPENSRC_ROOT"
```

Compare `repos[].name` and `repos[].path` with the filesystem path under `$OPENSRC_ROOT/opensrc/repos/github.com/owner/repo`.

### Need to remove one cached repo

Prefer the command-level removal when possible:

```bash
opensrc remove --cwd "$OPENSRC_ROOT" owner/repo
```

If that does not clear an incomplete directory, send only that specific repository directory to the trash:

```bash
trash "$OPENSRC_ROOT/opensrc/repos/github.com/owner/repo"
```

### Need to clean many cached repos

`clean` is broad. Do not use it without explicit user intent:

```bash
opensrc clean --repos --cwd "$OPENSRC_ROOT"
```

## Safety Rules

- Do not run `opensrc clean` unless the user explicitly wants broad cleanup
- Do not send the whole `opensrc/` directory to the trash for a single broken repo
- Do not edit source files inside `opensrc/repos/...` unless the user explicitly asks to modify cached source
- Use `trash` rather than `rm -rf` for any local cleanup so the directory is recoverable
- When in doubt, list sources and inspect the specific repo directory before deleting anything
