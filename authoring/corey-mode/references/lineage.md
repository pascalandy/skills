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

The source is the opensrc snapshot of `coreyhaines31/marketingskills`. Its revision comes from the cache's `sync-state.json`.

1. Load `git-local` and follow its workflow for `coreyhaines31/marketingskills`. Keep its validated `OPENSRC_HOME` and `OPENSRC_ROOT` in the same shell for the commands below
2. Confirm `jq --version`. If it is missing, stop and give the user `mise use -g jq` on Linux or `brew install jq` on macOS
3. If `git-local` fetched the snapshot directly, run the cache's refresh recipe below to record its commit. Continue only on success. Otherwise, proceed to step 4

```sh
OPENSRC_HOME="$OPENSRC_HOME" just --justfile "$OPENSRC_ROOT/justfile" --working-directory "$OPENSRC_ROOT" opensrc-sync coreyhaines31/marketingskills
```

4. From this skills repository checkout, resolve the snapshot path and revision. Stop if either lookup fails or returns no value

```sh
upstream="$OPENSRC_HOME/$(jq -er '.repos[] | select(.name == "github.com/coreyhaines31/marketingskills") | .path' "$OPENSRC_HOME/sources.json")"
revision="$(jq -er '.repos["github.com/coreyhaines31/marketingskills"].commitSha' "$OPENSRC_HOME/sync-state.json")"
```

5. Preview the import with `--dry-run`, inspect the `changes` it answers, then apply and check it. Stop on a failed command

```sh
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision" --dry-run
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision"
uv run authoring/corey-mode/scripts/update_corey_mode.py check --upstream "$upstream"
just compile-skills
just remote-skills
just check
```

`check` fails with `playbook without a route` when upstream adds a skill, and with `route without a playbook` when it removes one. Add or remove the row in `SKILL.md`, reading the new playbook's description for tie-breakers against its neighbors. Then replay the [routing cases](routing-cases.md).

Offline, `check` compares every generated file with the lock, requires one route per playbook, rejects a nested `SKILL.md`, and resolves the links in handwritten files. With `--upstream`, it also rebuilds every file from that folder and compares bytes. Neither proves how an agent routes a request.
