# OpenSrc Operations

Use this reference when `opensrc` fails, the local cache looks inconsistent, or the task needs listing/removal/cleanup behavior.

Before running these commands in any shell, initialize and validate `OPENSRC_HOME` and `OPENSRC_ROOT` using [Cache Location](../SKILL.md#cache-location). That section owns the fixed destination; do not inherit a different cache or rely on the current directory.

## Help Surface

```text
Usage: opensrc <command>

Commands:
  fetch <packages...>    Fetch package or repository sources
  path <packages...>     Print source paths; fetches on cache miss
  list [--json]          List cached sources
  remove <packages...>   Remove cached sources
  clean [--repos]        Remove all sources, or only repositories
```

This is the installed native CLI's interface. `fetch --cwd` and `path --cwd` select the directory for lockfile lookup, not storage. There is no `--modify` option. If local help differs, stop and resolve the mismatch before using these commands.

## Standard Commands

Pass the initialized cache explicitly to every command, including destructive operations when authorized:

```bash
OPENSRC_HOME="$OPENSRC_HOME" opensrc fetch owner/repo
OPENSRC_HOME="$OPENSRC_HOME" opensrc list
OPENSRC_HOME="$OPENSRC_HOME" opensrc list --json
OPENSRC_HOME="$OPENSRC_HOME" opensrc remove owner/repo
OPENSRC_HOME="$OPENSRC_HOME" opensrc clean --repos
```

## Existing Repo Check

Use the recorded path and refresh sequence in [Workflow](../SKILL.md#workflow). `opensrc path` can fetch on a cache miss, so it is not a read-only existence check. Resolve the path again after an update; a version directory may have been added.

## Common Issues

### Existing directory is empty or only contains `.DS_Store`

This can happen after an interrupted or failed fetch. Resolve `repo_path` from the cache metadata and verify it stays inside `OPENSRC_HOME`. If repair is authorized and the directory has no useful source files, send only that directory to the trash and fetch again:

```bash
trash "$repo_path"
OPENSRC_HOME="$OPENSRC_HOME" opensrc fetch owner/repo
```

### `ENOTEMPTY` while fetching

`opensrc` may fail while trying to replace a directory that already exists. First inspect the directory. If it contains real source files, preserve them and report that the update failed. If it is incomplete, follow the authorized repair procedure above.

### Need to verify what `opensrc` knows

Use:

```bash
OPENSRC_HOME="$OPENSRC_HOME" opensrc list --json
```

Compare `repos[].name` and `repos[].path` with the filesystem beneath `OPENSRC_HOME`. If a populated repository directory is missing from the registry, report the mismatch before fetching or deleting anything. Do not silently relocate it or rewrite the registry.

### Need to remove one cached repo

When removal is authorized, resolve and validate `repo_path` using [Cache Location](../SKILL.md#cache-location) first. Keep that value for any fallback cleanup, since removal may delete the registry entry. Prefer the command-level removal:

```bash
OPENSRC_HOME="$OPENSRC_HOME" opensrc remove owner/repo
```

If that does not clear an incomplete directory, send only that specific repository directory to the trash:

```bash
trash "$repo_path"
```

### Need to clean many cached repos

`clean` is broad. Do not use it without explicit user intent:

```bash
OPENSRC_HOME="$OPENSRC_HOME" opensrc clean --repos
```

## Safety Rules

- Do not run `opensrc clean` unless the user explicitly wants broad cleanup
- Do not send the whole `opensrc/` directory to the trash for a single broken repo
- Do not edit source files inside `opensrc/repos/...` unless the user explicitly asks to modify cached source
- Use `trash` rather than `rm -rf` for any local cleanup so the directory is recoverable
- When in doubt, list sources and inspect the specific repo directory before deleting anything
