# Skill management

This project manages Pascal's skills. `authoring/` is the source of truth; `skills/` is generated output committed for GitHub readers

## Change a skill

1. Edit `authoring/<category>/<skill-name>/`, including its supporting files
2. Run `just flatten-skills`; if it fails, rerun `just flatten-skills --verbose`
3. Review and commit the source and generated output together

The flattening script maps each package with a root `SKILL.md` to `skills/<skill-name>/`. It includes supporting files, excludes `authoring/commands/` and ignored local artifacts, and fails on duplicate skill names or on files outside a package with a `SKILL.md`

`SKILL.md` frontmatter string values use double quotes; `just check-frontmatter` enforces it

Never edit `skills/` directly. Correct `authoring/` or the flattening script, then run `just flatten-skills` again

Repository-wide scripts live in `scripts/`; the `justfile` exposes routine operations. Scripts belonging to one skill stay in `authoring/<category>/<skill-name>/scripts/` and travel with that skill

## Install skills

`just install-skills` flattens `authoring/`, including uncommitted and branch-only changes, then copies `skills/` into every agent skill directory that `just install-skills --help` lists. Those directories feed Pascal's live agents, so run it only when Pascal asks. `just install-skills --dry-run --verbose` previews the current `authoring/` source without writing

- A manifest in `~/.local/state/install-skills/` records what the script installed. Skills it did not install are never touched, and it removes only its own skills that left `skills/`
- When it stops on a copy edited in place, move the edit into `authoring/`, then rerun with `--force`

## Script conventions

Scripts in `scripts/` are CLIs that agents run, so their output stays small and failures stay obvious. Skill-local scripts follow the same rules when we write or change them

- `-h, --help` prints usage with examples and changes nothing
- Quiet by default: one line on stdout on success
- `-v, --verbose` adds per-item detail and tracebacks on stderr
- `--dry-run` previews anything that writes or deletes
- Failures print `error: <what went wrong and how to fix it>` on stderr, then `rerun with --verbose for details`
- Exit codes: `0` ok, `1` failure, `2` bad usage, `130` interrupted
- Use only the standard library (`argparse`, `logging`) unless a dependency earns its place
- `justfile` recipes forward arguments (`recipe *args`) so flags reach the script

`scripts/_common.py` applies these rules: build the parser, then return `run_script(parser, work)` from `main()`. `work` returns the success line and raises `ScriptError` with one message per problem

Tests live in `scripts/tests/`. `just test` runs them; `just check` is exactly what CI runs on every PR and push to `main`. Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools

`just check` is a list of recipes; a failure names the one to rerun. Add a new CI-safe check as its own recipe, then append it to that list

When `just` is not installed, use `uvx --from rust-just just <recipe>`

## Commit hooks

Run `lefthook install` once per clone. The pre-commit hook calls `just` recipes, so run the same recipe to reproduce a failure

- `just gitleaks-staged` scans staged changes for secrets on every commit
- `just check-frontmatter` runs when a `SKILL.md` is staged
- `just flatten-skills --check` runs when files under `authoring/` or `skills/` are staged

gitleaks uses its built-in rules because the repo has no `.gitleaks.toml`. If you add one for an allowlist, start it with `[extend]` / `useDefault = true`; otherwise the built-in rules are disabled and every scan passes

## Python execution

Use `uv` for all Python runs, checks, and dependency changes, including skill-local scripts; never invoke `python3` or bare `python` directly. Scripts in `scripts/` start with a PEP 723 block, so run them with `uv run scripts/<name>.py`. The [Python sub-skill](authoring/devtools/coding-language/references/Python/MetaSkill.md) covers the details

## Release

1. Choose `vX.Y.Z` using the 0.x policy in `CHANGELOG.md`
2. Run `just release-check vX.Y.Z --verbose` to list changed skills
3. Write that version's `CHANGELOG.md` section and merge it to `main`
4. On `main`, run `just check && just release-check vX.Y.Z`
5. Run `git tag vX.Y.Z && git push origin vX.Y.Z`
6. Never move or delete a pushed tag, or edit or replace a published release
