---
name: "commit"
description: "Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages."
kind: "dev"
---

# Commit

Create atomic commits: one logical change per commit. If a commit cannot be described in one sentence without "and", split it.

## Split when

- Changes serve different purposes or features
- Changes use different commit types
- Changes would not revert together
- Docs, config, or tooling changes are unrelated to the code change

## Workflow

1. Run `git status`, then read `git diff` and `git diff --cached`. Review untracked files too. Done when every staged, unstaged, and untracked change is accounted for
2. Group the changes by the rules in Split when. Done when each path, or each hunk of a file that mixes groups, belongs to one group
3. Run the checks the repository provides for the current group, sized to the change. Run a full suite such as `just ci` only when the user requests it, repository policy requires it, or the change affects shared validation or broad behavior. Done when applicable checks pass or only unrelated pre-existing failures remain; report those failures separately
4. Stage only the current group by path with `git add <paths>`, never `git add .` or `git add -A`. If the index already holds changes outside this group, unstage them with `git restore --staged <paths>`, which keeps them in the working tree. For a file that mixes groups, `git apply --cached` a patch holding only this group's hunks
5. Run `git diff --cached --check` and read `git diff --cached`. Done when the check passes and the staged diff holds only this group
6. Commit in the format below and let the configured hooks run. Pass `--no-verify` only when the user explicitly authorizes it. If a hook fails, review its changes and return to step 3. Done when the commit succeeds and `git show HEAD` contains only the validated group
7. Repeat steps 3 to 6 for each group, in order
8. Run `git log -n <count> --oneline` and report each commit's hash and subject exactly as `git log` prints them. Done when every group is committed

## Push authorization

A commit request authorizes local commits only. The workflow is complete after local verification and reporting.

Run `git push` as a separate action only when the user requests it or an existing authorization in the conversation covers that push. Reuse applicable authorization without asking again. Without it, finish locally without prompting for a push.

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

Use `🧰 skill` for changes to skill packages, such as `authoring/**` in `pascalandy/skills`: instructions, references, examples, metadata, or helper scripts. Use `♻️ refactor` when a skill change is mostly structural, such as moving or renaming skill bundles, and `📚 docs` for documentation outside skill behavior, such as wiki pages and READMEs.

## Format

```text
<emoji> <type>: <scope>: <imperative summary>

- Purpose: <why change exists>
- Impact: <effect on users, system, or future work>
```

Examples:

- `🧰 skill: commit: classify skill edits explicitly`
- `♻️ refactor: toolbox: move commit skill`

Write the body for non-trivial commits. Optional fields, when useful: `File(s) changed:` for multi-file or non-obvious commits, and `Nature of changes:` when the type needs clarification.

## Style

- Subject in the imperative mood, under 72 characters, naming what changed
- Body says why the change matters
- Name the concrete change instead of `improve`, `enhance`, `streamline`, or `optimize`
- No periods at body line ends
