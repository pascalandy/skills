# OpenSrc Operations

Read this when `opensrc_sync.py` fails, the cache looks inconsistent, or the task needs to list, remove, or clean cached sources.

Run each command on the cache machine that [Cache machine](../SKILL.md#cache-machine) names: through `ssh <ssh>` when it is another machine. When `fleet.toml` gives the cache, prefix each command with `OPENSRC_HOME="$HOME/<opensrc key>"`, so it reaches the same cache as the script. Below, `$CACHE` is that folder, and `opensrc` stands for the command with its prefix.

For repairs that use `trash`, confirm it with `command -v trash` first. If missing, stop and give the user `sudo pacman -S trash-cli` on Arch Linux or `brew install trash` on macOS.

## Commands

```text
opensrc fetch <owner/repo>      Fetch a repository; a cached copy stays as it is
opensrc path <owner/repo>       Print its path; fetches on a cache miss
opensrc list --json             List cached sources
opensrc remove <owner/repo>     Remove one cached source
opensrc clean --repos           Remove every cached repository
```

`opensrc path` fetches on a cache miss, so it is no read-only existence check: read `$CACHE/sources.json` instead. Its `repos[].name` is `github.com/<owner>/<repo>`, and `repos[].path` is relative to `$CACHE`. `opensrc list --json` prints text instead of JSON when the cache is empty.

## Common Issues

### A cached directory is empty or holds only `.DS_Store`

An interrupted fetch can leave it so. Confirm that the directory resolves inside `$CACHE`. If repair is authorized and it holds no source files, rerun `opensrc_sync.py <owner>/<repo>`, which removes and fetches it again.

### A fetch failed after a refresh removed the copy

Rerun `opensrc_sync.py <owner>/<repo>`: the repository is no longer cached, so the run fetches it.

### A directory is on disk but missing from `sources.json`

Report the mismatch before fetching or deleting anything. Do not relocate it or rewrite the registry yourself.

### Remove one cached repository

When removal is authorized, run `opensrc remove <owner/repo>`. If an incomplete directory remains, send only that directory to the trash with `trash`.

### Clean many cached repositories

`opensrc clean --repos` removes every repository. Run it only on the user's explicit request.

## Safety Rules

- Do not send the whole cache to the trash for one broken repository
- Do not edit source files inside the cache unless the user explicitly asks to modify cached source
- Use `trash` rather than `rm -rf` for local cleanup, so the directory is recoverable
- When in doubt, read `sources.json` and inspect the repository directory before deleting anything
