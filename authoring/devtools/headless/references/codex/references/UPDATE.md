# Update This Skill

## Intro

Triggered when the user says something like "skill headless-codex, check if we need to update".

**Important:** This updates the skill documentation from official docs — NOT the CLI tool itself. To update the CLI, use your package manager.

To keep this skill current with the latest documentation, check the official docs using `npx nia-docs`.

## Configuration

```bash
DOC_URL="https://developers.openai.com/codex/cli/reference"
```

Then, use `npx nia-docs` for command patterns and usage guidance.

## What to Check For

When updating this skill, verify:

1. **New flags or options** — check the main CLI/command reference
2. **New subcommands** — look for additions to the command tree
3. **Output format changes** — verify JSON/text output behavior
4. **Configuration changes** — new env vars or config file options
5. **Examples and use cases** — new patterns in the docs

## Update Checklist

- [ ] Run `npx nia-docs "$DOC_URL" -c "cat ./cli.md"` (or main reference file) and compare flags/options
- [ ] Verify all referenced items match the current implementation
- [ ] run cli --help and check for any gaps
- [ ] Check for new examples or use cases in the docs
- [ ] Update the Gotchas section if new pitfalls are discovered
- [ ] Test any new commands before documenting them
