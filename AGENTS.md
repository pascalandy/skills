# Skill management

This project manages Pascal's skills. `authoring/` is the source of truth; `skills/` is generated output committed for GitHub readers

## Change a skill

1. Edit `authoring/<category>/<skill-name>/`, including its supporting files
2. Run `just render`
3. Review and commit the source and generated output together

The renderer maps each package with a root `SKILL.md` to the flat path `skills/<skill-name>/`. It includes the package's supporting files, excludes `authoring/commands/` and ignored local artifacts, and fails on duplicate skill names

Never edit `skills/` directly. Correct `authoring/` or the renderer and render again
