---
name: "headless"
description: "Use when running `codex exec`, Claude Code, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them."
kind: "dev"
---

# Headless CLI agents

Run Codex or Claude Code as a child agent with `scripts/headless.py`. It gives the child the access of an interactive session, waits for it, checks the result, and prints the answer. `<skill-dir>` below is the directory that holds this file. For OpenCode or Pi, read [OpenCode](references/opencode/MetaSkill.md) or [Pi](references/pi/MetaSkill.md) instead.

1. Pick the mode the request asks for: **review** or **fix**
2. Write the task to a prompt file in a `mktemp -d` folder: the scope, the criteria, the expected result, and the check results the child should trust. Paste any fact the child cannot look up
3. Run the matching command below and wait for it to exit, as [Wait for a run](#wait-for-a-run) describes
4. Read the result before you report

## Review

The child reads, runs commands and checks, uses the network, skills, and subagents, and reports. It must leave the checkout unchanged: the run fails when a tracked or untracked file changed. Ignored files, such as caches and build output, don't count.

Ask Codex for a review:

```bash
uv run <skill-dir>/scripts/headless.py codex --mode review \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude for a review:

```bash
uv run <skill-dir>/scripts/headless.py claude --mode review \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Keep the checkout and the reviewed artifact unchanged until the run exits. The launcher reports any change as the child's, and the answer would describe a stale revision.

## Fix

The child gets the same access and may edit files in `--cwd`. It leaves commits, pushes, and comments to you.

Ask Codex to fix:

```bash
uv run <skill-dir>/scripts/headless.py codex --mode fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude to fix:

```bash
uv run <skill-dir>/scripts/headless.py claude --mode fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Read `git diff` and run the relevant checks yourself before you report the fix. To keep working while a fixer runs, point `--cwd` at a separate worktree.

## Models and options

Codex runs GPT-6.1 Sol and Claude runs Opus 5.5, both at `xhigh`. These defaults hold even when `profile-routing-matrix` suggests another model. A model or effort named in the request overrides them through `--model` and `--effort`. Flags after `--` reach the child CLI unchanged, such as `-- -c 'web_search="live"'` for Codex. `uv run <skill-dir>/scripts/headless.py --help` lists every option.

## Read the result

On success, stdout starts with five lines, then the answer:

```text
model: gpt-6.1-sol
effort: xhigh
session: 01a0f7d4-cbcf-7162-869b-94b331ed56b0
changed: nothing
run: /tmp/headless-codex-review.8gcz_axu
```

`model` comes from the child's own output: cite it when the request names a reviewer. Claude lists the model that did the work first, then any helper model it used. `changed` lists the files the child changed. The run folder keeps `prompt.md`, `answer.md`, and the child's logs; read `answer.md` there when your tool cut the output.

Read the whole answer before deciding the run succeeded. A one-line "no findings" without criteria is weak evidence: add the criteria and check results, then rerun.

Exit 1 means the child failed, gave no answer, was denied a tool, or changed the checkout during a review. stderr names the cause and the run folder. Change the cause before a retry. Exit 2 is a usage error, such as an effort the CLI does not accept.

For a follow-up round on the same thread, pass the printed session to `--resume`. A fresh run gives an independent opinion.

## Wait for a run

A run often takes 5 to 15 minutes, and the launcher blocks until the child exits. In Claude Code, start the command in the background and wait for the completion notification. In Codex, run it in the foreground: the shell tool keeps a long command alive and lets you poll it until it exits. Keep the launcher in the command you run, because a harness stops a process that `&` left behind when that command ends.

## Limits

Read the [Codex reference](references/codex/MetaSkill.md) or the [Claude Code reference](references/claude/MetaSkill.md) for what the launcher leaves to you: untrusted repositories, a parent inside a Codex sandbox, images and web search, `@path` mentions in Claude prompts, background tasks in Claude, and testing a changed skill. The [glossary](references/GLOSSARY.md) defines the terms. To maintain this skill, follow the [update checklist](references/UPDATE.md).
