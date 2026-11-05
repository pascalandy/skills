# Lineage and updating

Maintainer reference. Ordinary use does not load this file.

Corey-mode packages [Corey Haines' Marketing Skills](https://github.com/coreyhaines31/marketingskills) as playbooks under their original names. The route table, the reading rules in `SKILL.md`, and the importer belong to Pascal. This is not an upstream release. The upstream [MIT license](LICENSE) travels with the playbooks.

## What the lock owns

The [upstream lock](../upstream-lock.json) records the imported revision and, for each generated file, its upstream source and SHA-256. The first pin is [5b2c000](https://github.com/coreyhaines31/marketingskills/tree/5b2c0007766c6a1cf1d53fd8fc73e979e0821022). The lock, rather than this note, owns the current revision.

`playbooks/` and `references/LICENSE` are generated. The importer copies each `skills/<name>/` folder except `evals/`, renames `SKILL.md` to `<name>.md`, and keeps its frontmatter. It changes link targets only:

- A link to an imported file points to its copy in this package
- A link to an upstream file left out, such as `tools/` or `evals/`, points to GitHub at the pinned revision
- A link already broken upstream keeps its text

Upstream `tools/`, `evals/`, the README, `AGENTS.md`, `VERSIONS.md`, and the plugin manifests stay out. So does upstream's update check, which asks agents to fetch `VERSIONS.md` and `git pull`.

## Refresh from upstream

The source is the opensrc snapshot of `coreyhaines31/marketingskills`. The importer reads it from disk, so run these steps on the machine that holds the cache, in a checkout of this skills repository. It requires `--upstream` to match that repository's path in the cache's `sources.json`; a missing or invalid registry stops `update` and `check --upstream`. An opensrc snapshot records no commit, so `--revision` comes from GitHub right after the refresh.

1. Confirm `jq --version` and `gh auth status`. If one is missing, stop and give the user `mise use -g jq` or `mise use -g gh` on Linux, or `brew install jq` or `brew install gh` on macOS
2. Refresh the snapshot with the `git-local` script, without `--max-age`, so the copy is new. Continue only on success

```sh
answer="$(uv run authoring/andy/git-local/scripts/opensrc_sync.py coreyhaines31/marketingskills)"
```

3. Right after the refresh, resolve the snapshot path, then the commit of its branch on GitHub: a commit pushed upstream in between would pin links to a revision newer than the snapshot. Stop if either lookup fails or returns no value

```sh
upstream="$(printf '%s' "$answer" | jq -er '.repos[0].path')"
revision="$(gh api repos/coreyhaines31/marketingskills/commits/main --jq .sha)"
```

4. Preview the import with `--dry-run`, inspect the `changes` it answers, then apply and check it. Stop on a failed command

```sh
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision" --dry-run
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision"
uv run authoring/corey-mode/scripts/update_corey_mode.py check --upstream "$upstream"
just compile-skills
just remote-skills
just check
```

`check` fails with `playbook without a route` when upstream adds a skill, and with `route without a playbook` when it removes one. Add or remove the row in `SKILL.md`, reading the new playbook's description for tie-breakers against its neighbors. Then replay the [routing cases](routing-cases.md).

Offline, `check` compares every generated file with the lock, requires one route per playbook, rejects a nested `SKILL.md`, and resolves the links in handwritten files. With `--upstream`, it rebuilds every file from that folder at the lock's revision and compares bytes, so a snapshot newer than the lock shows as differences. Neither proves how an agent routes a request.
