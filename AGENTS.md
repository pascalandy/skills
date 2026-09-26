# Skill management

This project manages Pascal's skills. `authoring/` is the source of truth; `skills/` is generated output committed for GitHub readers

## Change a skill

1. Edit `authoring/<category>/<skill-name>/`, including its supporting files
2. Run `just flatten-skills`
3. Review and commit the source and generated output together

The flattening script maps each package with a root `SKILL.md` to `skills/<skill-name>/`. It includes supporting files, excludes `authoring/commands/` and ignored local artifacts, and fails on duplicate skill names

Repository-wide scripts live in `scripts/`; the `justfile` exposes routine operations. Scripts belonging to one skill stay in `authoring/<category>/<skill-name>/scripts/` and travel with that skill

Never edit `skills/` directly. Correct `authoring/` or the flattening script, then run `just flatten-skills` again
