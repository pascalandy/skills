# Skill management

`authoring/` is the skill source. `skills/` is generated output committed for GitHub readers

## Change a skill

Load `writing-great-skills` before creating, changing, or refactoring a skill. It decides how a skill is written, including its trigger; this file decides where the skill lives and how it ships

Never set `disable-model-invocation: true` in skill frontmatter or `policy.allow_implicit_invocation: false` in Codex metadata. Agents may invoke skills when relevant

1. For skill content, edit only `authoring/<category>/<skill-name>/`, including supporting files. Even when working from `skills/<skill-name>/`, never edit generated files directly
2. Run `just flatten-skills`; if it fails, rerun `just flatten-skills --verbose`
3. Review and commit the source and generated output together

The flattening script maps each package with a root `SKILL.md` to `skills/<skill-name>/`. It includes supporting files, excludes `authoring/commands/` and ignored local artifacts, and fails on duplicate skill names or files outside a package with a `SKILL.md`

`SKILL.md` frontmatter string values use double quotes; `just check-frontmatter` enforces it

`scripts/tests/test_skill_invocation.py` checks every authored skill for metadata that disables agent invocation

If generated output is wrong, fix `authoring/` or the flattening script, then rerun `just flatten-skills`

Repository-wide scripts live in `scripts/`; skill-specific scripts stay in `authoring/<category>/<skill-name>/scripts/` and travel with the skill. The `justfile` exposes routine operations

## Python execution

Use `uv` for all Python runs, checks, and dependency changes, including skill-local scripts. Never invoke `python3` or bare `python` directly. Scripts in `scripts/` have a PEP 723 block; run them with `uv run scripts/<name>.py`. See the [Python sub-skill](authoring/devtools/coding-language/references/Python/MetaSkill.md)

## Checks

- `just check` is exactly what CI runs; a failure names the `just check --only NAME` to rerun
- Run `lefthook install` once per clone. To reproduce a pre-commit failure, run its `just` recipe
- When `just` is not installed, use `uvx --from rust-just just <recipe>`

## Install skills

`just install-skills` flattens current public `authoring/`, including uncommitted and branch-only changes, then installs the selected skills and `authoring/commands/*.md` into Pascal's live agents. `just sync` pulls first. On om1, the hub, `just sync-fleet` sends om1's `main` and private tree to every registered machine over SSH, and `--check` compares them. On om1, lefthook runs both after a commit or pull on `main` in the main checkout. Otherwise run apply, `sync`, or `sync-fleet` only when Pascal asks; `--dry-run` and `--check` preview without writing. Before any other install work, read [install skills](docs/maintainer/references/install-skills.md)

## Read on demand

- Before writing or changing a script in `scripts/` or a skill's `scripts/`, read [script conventions](docs/maintainer/references/script-conventions.md)
- Before adding or changing a check, hook, or CI step, read [checks](docs/maintainer/references/checks.md)
- To release, follow [release](docs/maintainer/references/release.md). Never move or delete a pushed tag
