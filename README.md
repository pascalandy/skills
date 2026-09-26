# Skills

This is Pascal Andy's collection of reusable instructions for coding agents. It is for people who want to add a focused workflow to an agent without adopting the whole collection.

Each skill is maintained in `authoring/<category>/<skill>/` and published in [`skills/`](skills/). Contributors should read [`AGENTS.md`](AGENTS.md) before changing the source. Browse [`skills/`](skills/) for the full list.

## Examples

- [`concise`](skills/concise/SKILL.md): Use when the user requests to be more concise
- [`html-mode`](skills/html-mode/SKILL.md): Use when the user requests a standalone HTML artifact or HTML presentation
- [`technical-writing`](skills/technical-writing/SKILL.md): Use when writing or reviewing docs, RFCs, readmes, PR descriptions, or commit messages
- [`grill-for-unknowns`](skills/grill-for-unknowns/SKILL.md): Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation

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
checkout=$(mktemp -d)
git clone --depth 1 https://github.com/pascalandy/skills.git "$checkout/repo"
destination="$agent_skills/$skill"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  echo "Refusing to overwrite $destination" >&2
  exit 1
fi
mkdir -p "$agent_skills"
cp -R "$checkout/repo/skills/$skill" "$destination"
```

To update, repeat with a fresh clone after moving or removing your previous copy yourself. The command above refuses to overwrite it.

### Maintainer bulk install

The repository's installer handles multiple agent directories. Preview its work before running it:

```sh
just install-skills --dry-run --verbose
just install-skills
```

Run `just install-skills --help` for the current targets and ownership rules.

## Reuse

[`LICENSE`](LICENSE) covers Pascal's original work under MIT. Adapted third-party material keeps its upstream terms; see the notices for [`html-mode`](skills/html-mode/references/attribution.md), [`grill-for-unknowns`](skills/grill-for-unknowns/LICENSE), and [`matt-mode`](skills/matt-mode/references/lineage.md). Upstream terms for the `pstack` packages have not yet been recorded here.
