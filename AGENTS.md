# Skill management

`authoring/` is the skill source. `skills/` is generated output committed for GitHub readers

## Change a skill

Load `writing-great-skills` before creating, changing, or refactoring a skill. It decides how a skill is written, including its trigger; this file decides where the skill lives and how it ships

Never set `disable-model-invocation: true` in skill frontmatter or `policy.allow_implicit_invocation: false` in Codex metadata. Agents may invoke skills when relevant

1. For skill content, edit only the skill's package in `authoring/`, including supporting files. Even when working from `skills/<skill-name>/`, never edit generated files directly
2. Run `just compile-skills`, then `just remote-skills`; if compiling fails, rerun `just compile-skills --debug`
3. Review and commit the source and generated output together. The output includes `docs/references/skill-count.md`, the skills per category and kind; confirm each count change matches the skills you added, removed, or moved

The compile script maps each package, a folder with a root `SKILL.md` at `authoring/<category>/<skill-name>/` or `authoring/<skill-name>/`, to `skills/<skill-name>/`. It includes supporting files, excludes ignored local artifacts, and fails on duplicate skill names, a package inside another package, or files outside a package

`SKILL.md` frontmatter string values use double quotes; `just check-frontmatter` enforces it

`SKILL.md` frontmatter sets `kind: "general"` when someone who never writes code would ask for the skill, and `kind: "dev"` otherwise. A `general` skill must not need a `dev` skill to run. When `kind` is missing, compiling publishes `kind: "unknown"` and no check fails; `docs/references/remote-skills.md` lists those skills under Unknown

`scripts/tests/test_skill_invocation.py` checks every authored skill for metadata that disables agent invocation

If generated output is wrong, fix `authoring/` or the compile script, then rerun `just compile-skills`

Repository-wide scripts live in `scripts/`; skill-specific scripts stay in the package's `scripts/` and travel with the skill. The `justfile` exposes routine operations

## Python execution

Use `uv` for all Python runs, checks, and dependency changes, including skill-local scripts. Never invoke `python3` or bare `python` directly. Scripts in `scripts/` have a PEP 723 block; run them with `uv run scripts/<name>.py`. See the [Python sub-skill](authoring/andy-devtools/coding-language/references/Python/MetaSkill.md)

## Checks

- Use plain `just check` for routine work and signoff. The manual CI workflow uses `just check --sweep` to run unrelated suites too. A failure names the `just check --only NAME` to rerun
- `just check` always runs direct repository validators and two cheap project-rule tests, then selects other root tests and skill checks by changed inputs. Root tests use named `test-<stem>` checks; skill tests belong in their authoring package. See [checks](docs/references/checks.md) and [script conventions](docs/references/script-conventions.md) for routing details
- `main` merges a PR only when its head commit carries a green `signoff` status; GitHub Actions runs only when started by hand. After pushing a PR branch, run `just signoff`. When Pascal says to merge a PR, run `just merge` on its branch; a request to write code does not authorize a merge. Never merge with `gh pr merge --admin`
- Run `lefthook install` once per clone. To reproduce a pre-commit failure, run its `just` recipe
- When `just` is not installed, use `uvx --from rust-just just <recipe>`

## Install skills

`just install-skills` compiles current public `authoring/`, including uncommitted and branch-only changes, then installs the selected skills and `commands/*.md` into Pascal's live agents. `just sync` pulls first and saves and pulls `_skills_private/`, a clone of the private repository `pascalandy/skills-private` that `.gitignore` keeps out of this one. From any machine, `just sync-fleet` brings every registered machine to GitHub's `main` over SSH, each machine saves and pulls its private clone, and `--check` compares them. In each machine's main checkout, lefthook installs after a commit or pull on `main` and syncs the other machines after a pull or a push of `main`. `just merge` ends with `just deploy`, an alias of `just sync-fleet`, which runs from the main checkout, so keep each machine's main checkout on `main` and do branch work in a worktree. Otherwise run apply, `sync`, or `sync-fleet` only when Pascal asks; `--dry-run` and `--check` preview without writing. Before any other install work, read [install skills](docs/references/install-skills.md)

## Read on demand

- Before writing or changing a script in `scripts/` or a skill's `scripts/`, read [script conventions](docs/references/script-conventions.md)
- Before adding or changing a check, hook, or CI step, or when `just signoff` or a merge is refused, read [checks](docs/references/checks.md)
- After changing `compile_skills.py`, `remote_skills.py`, `install_skills.py`, `discover_skills.py`, or a module they import in `scripts/`, load `verify-skills` and run it before opening the PR
- To release, follow [release](docs/references/release.md). Never move or delete a pushed tag
