---
name: "headless"
description: "Use when running `codex exec`, Claude Code, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. `headless` may arrive as any voice-to-text spelling that sounds like it, such as `endless` or `adless`."
kind: "dev"
---

# Headless CLI agents

Run Codex or Claude Code as a child agent with `scripts/headless.py`, so every headless run is deterministic: one command shape, a required access flag, defaults the output prints, and fixed exit codes. The launcher gives the child the access of an interactive session, waits for it, checks the result, and prints the answer. `<skill-dir>` below is the directory that holds this file. The launcher does not run OpenCode or Pi yet (#281); read [OpenCode](references/opencode/MetaSkill.md) or [Pi](references/pi/MetaSkill.md) for those.

1. Pick the access the request asks for: `--review-only` or `--review-fix`
2. Write the task to a prompt file in a `mktemp -d` folder: the scope, the criteria, the expected result, and the check results the child should trust. Paste any fact the child cannot look up
3. Run the matching command below and wait for it to exit, as [Wait for a run](#wait-for-a-run) describes
4. Read the result before you report

## Review only

The child reads, runs commands and checks, uses the network, skills, and subagents, and reports. It must leave the checkout unchanged: the run fails when a tracked or untracked file changed. Ignored files, such as caches and build output, don't count. Claude also runs without its file-editing tools; Codex has no such switch, so the check after the run is its guard.

Ask Codex for a review:

```bash
uv run <skill-dir>/scripts/headless.py codex --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude for a review:

```bash
uv run <skill-dir>/scripts/headless.py claude --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Keep the checkout and the reviewed artifact unchanged until the run exits. The launcher reports any change as the child's, and the answer would describe a stale revision.

## Review and fix

The child gets the same access, with every tool, and may edit files in `--cwd` to fix what it finds. It leaves commits, pushes, and comments to you.

Ask Codex to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py codex --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py claude --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Read `git diff` and run the relevant checks yourself before you report the fix. To keep working while a fixer runs, point `--cwd` at a separate worktree.

## Models and options

Codex runs GPT-6.1 Sol and Claude runs Opus 5.5, both at `xhigh`. These defaults hold even when `profile-routing-matrix` suggests another model. A model or reasoning level named in the request overrides them through `--model` and `--effort`. Harnesses name the reasoning level differently: `--effort` reaches Codex as `model_reasoning_effort` and Claude as `--effort`, and a request may say reasoning, effort, or thinking for the same setting. Flags after `--` reach the child CLI unchanged, such as `-- -c 'web_search="live"'` for Codex. `uv run <skill-dir>/scripts/headless.py --help` lists every option.

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

Exit 1 means the child failed, gave no answer, was denied a tool, or changed the checkout under `--review-only`. stderr names the cause and the run folder. Change the cause before a retry. Exit 2 is a usage error, such as an effort the CLI does not accept.

For a follow-up round on the same thread, pass the printed session to `--resume`. A fresh run gives an independent opinion.

## Wait for a run

A run often takes 5 to 15 minutes, and the launcher blocks until the child exits. In Claude Code, start the command in the background and wait for the completion notification. In Codex, run it in the foreground: the shell tool keeps a long command alive and lets you poll it until it exits. Keep the launcher in the command you run, because a harness stops a process that `&` left behind when that command ends.

## Limits

Read the [Codex reference](references/codex/MetaSkill.md) or the [Claude Code reference](references/claude/MetaSkill.md) for what the launcher leaves to you: untrusted repositories, a parent inside a Codex sandbox, images and web search, `@path` mentions in Claude prompts, background tasks in Claude, and testing a changed skill. The [glossary](references/GLOSSARY.md) defines the terms. To maintain this skill, follow the [update checklist](references/UPDATE.md).
