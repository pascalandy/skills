---
name: "commit"
description: "Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages."
---

# Skill: Commit

Create atomic commits: 1 logical change/commit

## Rule

If commit cannot be described in 1 sentence without "and", split it

## Req behavior

- Review full working tree before commit
- Never combine unrelated changes
- Stage and commit each logical group separately
- Use commit body for non-trivial commits
- When splitting commits, never use `git add .` or `git add -A`
- Never bypass configured hooks with `--no-verify` unless the user explicitly authorizes it

## Validation

- Match validation to the logical change
- Run targeted checks when the repository provides them
- Run a full-repository suite only when the user requests it, repository policy requires it, or the change affects shared validation or broad behavior
- Do not run a full suite such as `just ci` by default for a routine commit
- Treat unrelated pre-existing failures as findings, not proof that the requested change failed
- After staging, run `git diff --cached --check` and inspect the staged diff before committing

## Workflow

1. Run `git status` and `git diff --stat`
2. Review all files, not only prior work target
3. Group changes by logical purpose
4. Split by purpose, feature, type, or rollback boundary
5. Run validation proportional to the current group
6. Stage only 1 group paths: `git add <paths>`
7. Verify the exact staged content with `git diff --cached --check` and `git diff --cached`
8. Commit each group in order and let configured hooks run
9. Verify the created commits with `git log -n <count> --oneline` and report their hashes and subjects

## Push authorization

A commit request authorizes local commits only. The workflow is complete after local verification and reporting.

Run `git push` as a separate action only when the user requests it or an existing authorization in the conversation covers that push. Reuse applicable authorization without asking again. Without it, finish locally without prompting for a push.

## Split when

- Changes serve different purposes
- Changes belong to different features
- Changes use different commit types
- Changes would not revert together
- Docs/config/tooling changes unrelated to code change

## Commit types

- `✨ feat`
- `🚑 fix`
- `♻️ refactor`
- `📚 docs`
- `🧰 skill`
- `🧪 test`
- `🎨 style`
- `⚡️ perf`
- `🧑‍💻 chore`
- `🧹 remove`
- `🔒 security`
- `🚧 wip`

## Skills vs docs

Skill updates get their own type.

Prefer `🧰 skill` for changes under `dot_config/ai_templates/skills/**`, including:
- `SKILL.md` behavior or instructions
- skill references, examples, metadata, or helper scripts
- creating, editing, normalizing, or maintaining skills

Use `📚 docs` for general documentation, wiki pages, READMEs, or reference prose outside skill behavior.

Use `♻️ refactor` when the skill change is mostly structural, such as moving or renaming skill bundles.

Examples:
- `🧰 skill: commit: classify skill edits explicitly`
- `🧰 skill: tavily: use skill-relative paths`
- `♻️ refactor: toolbox: move commit skill`

## Format

```text
<emoji> <type>: <scope>: <imperative summary>

- Purpose: <why change exists>
- Impact: <effect on users, system, or future work>
```

Optional fields when useful:
- `File(s) changed:` for multi-file or non-obvious commits
- `Nature of changes:` when category needs clarification

## Style

- Imperative mood
- Active voice
- Specific and concrete
- Cut filler
- Avoid vague claims like `improve`, `enhance`, `streamline`, `optimize` unless concrete
- Subject <72 chars
- No periods at body line ends

## Final check

Before commit, confirm:
- 1 logical change
- No unrelated files staged
- Staged diff was reviewed and passes `git diff --cached --check`
- Validation was proportional to the change
- Subject says what changed
- Body says why it matters
- Skill changes use `🧰 skill` (or `♻️ refactor` if structural)
