# Skill management

This project manages Pascal's skills

## Source of truth

- Edit skill definitions and their supporting files in `authoring/`
- Treat `skills/` as generated output rendered from `authoring/` by the project's `justfile`
- After changing `authoring/`, use the `justfile` render recipe and review the resulting `skills/` output
- Correct generated content by changing `authoring/` or the render recipe, then render again
- If the render recipe is unavailable, leave `skills/` untouched and report the missing build step

Never edit files in `skills/` directly
