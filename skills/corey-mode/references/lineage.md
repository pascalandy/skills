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

The source is the opensrc cache that the `git-local` skill keeps current. Its snapshot has no Git history, so the revision comes from the cache's `sync-state.json`. Refresh the cache first, then run these from the skills repository checkout:

```sh
upstream="$OPENSRC_HOME/repos/github.com/coreyhaines31/marketingskills/main"
revision="$(jq -r '.repos["github.com/coreyhaines31/marketingskills"].commitSha' "$OPENSRC_HOME/sync-state.json")"
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision" --dry-run
uv run authoring/corey-mode/scripts/update_corey_mode.py update --upstream "$upstream" --revision "$revision"
uv run authoring/corey-mode/scripts/update_corey_mode.py check --upstream "$upstream"
just flatten-skills
just remote-skills
just check
```

`check` fails with `playbook without a route` when upstream adds a skill, and with `route without a playbook` when it removes one. Add or remove the row in `SKILL.md`, reading the new playbook's description for tie-breakers against its neighbors. Then replay the [routing cases](routing-cases.md).

Offline, `check` compares every generated file with the lock, requires one route per playbook, rejects a nested `SKILL.md`, and resolves the links in handwritten files. With `--upstream`, it also rebuilds every file from that folder and compares bytes. Neither proves how an agent routes a request.
