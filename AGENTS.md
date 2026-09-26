# Skill management

`authoring/` is the skill source. `skills/` is generated output committed for GitHub readers

## Change a skill

1. For skill content, edit only `authoring/<category>/<skill-name>/`, including supporting files. Even when working from `skills/<skill-name>/`, never edit generated files directly
2. Run `just flatten-skills`; if it fails, rerun `just flatten-skills --verbose`
3. Review and commit the source and generated output together

The flattening script maps each package with a root `SKILL.md` to `skills/<skill-name>/`. It includes supporting files, excludes `authoring/commands/` and ignored local artifacts, and fails on duplicate skill names or files outside a package with a `SKILL.md`

`SKILL.md` frontmatter string values use double quotes; `just check-frontmatter` enforces it

If generated output is wrong, fix `authoring/` or the flattening script, then rerun `just flatten-skills`

Repository-wide scripts live in `scripts/`; skill-specific scripts stay in `authoring/<category>/<skill-name>/scripts/` and travel with the skill. The `justfile` exposes routine operations

## Install skills

`just install-skills` flattens current `authoring/`, including uncommitted and branch-only changes, then copies `skills/` to the agent directories listed by `just install-skills --help`. These feed Pascal's live agents. Run it only when Pascal asks. Preview without writing via `just install-skills --dry-run --verbose`

- A manifest in `~/.local/state/install-skills/` records installed skills. The script never touches others and removes its own skills only after they leave `skills/`
- If a copy was edited in place, move the edit to `authoring/`, then rerun with `--force`

## Script conventions

CLIs in `scripts/` follow these rules. Apply them when writing or changing skill-local scripts:

- `-h, --help` prints usage and examples without changes
- Quiet by default: one line on stdout on success
- `-v, --verbose` adds per-item detail and tracebacks on stderr
- `--dry-run` previews writes and deletions
- Failures print `error: <what went wrong and how to fix it>` on stderr, then `rerun with --verbose for details`
- Exit codes: `0` success, `1` failure, `2` bad usage, `130` interrupted
- Use only the standard library (`argparse`, `logging`) unless a dependency earns its place
- `justfile` recipes forward arguments (`recipe *args`) to scripts

`scripts/_common.py` applies these rules. Build the parser; return `run_script(parser, work)` from `main()`. `work` returns the success line or raises `ScriptError` with one message per problem

Tests live in `scripts/tests/`. `just test` runs them; `just check` is exactly what CI runs on every PR and push to `main`. Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools

`just check` is a list of recipes; a failure names the one to rerun. Add a new CI-safe check as its own recipe, then append it to that list

When `just` is not installed, use `uvx --from rust-just just <recipe>`

## Commit hooks

Run `lefthook install` once per clone. To reproduce a pre-commit failure, run its `just` recipe

- `just gitleaks-staged` scans staged changes for secrets on each commit
- `just check-frontmatter` runs when a `SKILL.md` is staged
- `just flatten-skills --check` runs when files under `authoring/` or `skills/` are staged

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Python execution

Use `uv` for all Python runs, checks, and dependency changes, including skill-local scripts. Never invoke `python3` or bare `python` directly. Scripts in `scripts/` have a PEP 723 block; run them with `uv run scripts/<name>.py`. See the [Python sub-skill](authoring/devtools/coding-language/references/Python/MetaSkill.md)

## Release

1. Choose `vX.Y.Z` using the 0.x policy in `CHANGELOG.md`
2. Run `just release-check vX.Y.Z --verbose` to list changed skills
3. Write that version's `CHANGELOG.md` section and merge it to `main`
4. On `main`, run `just check && just release-check vX.Y.Z`
5. Run `git tag vX.Y.Z && git push origin vX.Y.Z`
6. Never move or delete a pushed tag, or edit or replace a published release
7. If the tag run fails, rerun it once only when the failure was transient; otherwise fix on `main` and release the next patch
