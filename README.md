# Skills

This is Pascal Andy's collection of reusable instructions for coding agents. It is for people who want to add a focused workflow to an agent without adopting the whole collection.

Each skill is maintained in `authoring/<category>/<skill>/` and published in [`skills/`](skills/). Contributors should read [`AGENTS.md`](AGENTS.md) before changing the source. Browse [`skills/`](skills/) for the full list.

## Examples

- [`concise`](skills/concise/SKILL.md): Use when the user requests to be more concise
- [`html-mode`](skills/html-mode/SKILL.md): Use when the user requests a standalone HTML artifact or HTML presentation
- [`commit`](skills/commit/SKILL.md): Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages
- [`grill-for-unknowns`](skills/grill-for-unknowns/SKILL.md): Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation

## Two ways to call a skill

Most skills are model-invoked: the agent loads one when your request matches its `description`. User-invoked skills wait until you name them, as `$name` in Codex or `/name` in Claude Code. They set `disable-model-invocation: true` in `SKILL.md`, plus `policy.allow_implicit_invocation: false` in `agents/openai.yaml` when that file exists.

## Install one skill

### With the third-party Skills CLI

Replace `<name>` with a folder name from [`skills/`](skills/):

```sh
npx skills add pascalandy/skills --skill <name>
npx skills update
```

The third-party CLI writes to agent skill directories and sends telemetry. Check its prompts and options before using it with your daily agent setup.

### With git and a copy

This route needs only git and standard shell tools. Set `skill` to the folder you want and `agent_skills` to your agent's skills directory:

```sh
skill=concise
agent_skills="$HOME/.agents/skills"
destination="$agent_skills/$skill"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  echo "Refusing to overwrite $destination" >&2
else
  checkout=$(mktemp -d)
  git clone --quiet --depth 1 https://github.com/pascalandy/skills.git "$checkout" &&
    mkdir -p "$agent_skills" &&
    cp -R "$checkout/skills/$skill" "$destination"
  rm -rf "$checkout"
fi
```

To update, repeat with a fresh clone after moving or removing your previous copy yourself. The command above refuses to overwrite it.

### Maintainer bulk install

The repository's installer handles multiple agent directories. Preview its work before running it:

```sh
just install-skills --dry-run --verbose
just install-skills
```

Run `just install-skills --help` for the current targets and ownership rules.

## Releases

See [`CHANGELOG.md`](CHANGELOG.md) for version notes and [GitHub Releases](https://github.com/pascalandy/skills/releases) for published snapshots.

## Reuse

[`LICENSE`](LICENSE) covers Pascal's original work under MIT. Shared upstream notices are kept with [`poteto-mode` for PStack](skills/poteto-mode/references/LICENSE) and [`matt-mode` for Matt Pocock](skills/matt-mode/references/LICENSE). The [`gh-stack`](skills/gh-stack/references/LICENSE) and [`test-audit`](skills/test-audit/LICENSE) notices sit with those skills. See [`html-mode`](skills/html-mode/references/attribution.md), [`grill-for-unknowns`](skills/grill-for-unknowns/LICENSE), and the [`matt-mode` lineage](skills/matt-mode/references/lineage.md) for more provenance. When redistributing an adapted skill alone, include its applicable upstream notice.
