---
name: "headless"
description: "Use when running `codex exec`, `codex exec review`, Claude Code, Grok, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. `headless` may arrive as any voice-to-text spelling that sounds like it, such as `endless` or `adless`."
kind: "dev"
---

# Headless CLI agents

Run Codex, Claude Code, or Grok as a child agent with `scripts/headless.py`, so every headless run is deterministic: one command shape, a required mode flag, defaults from one file, and fixed exit codes. The launcher waits for the child, checks the result, and saves the answer to a file whose path it prints. `<skill-dir>` below is the directory that holds this file. The launcher does not run OpenCode or Pi yet (#281); read [OpenCode](references/opencode/MetaSkill.md) or [Pi](references/pi/MetaSkill.md) for those.

1. Pick the mode the request asks for: `--review-only`, `--review-fix`, or `--code-review`, the CLI's own reviewer
2. For `--review-only` and `--review-fix`, write the task to a prompt file in a `mktemp -d` folder: the scope, the criteria, the expected result, and the check results the child should trust. Paste any fact the child cannot look up. For `--code-review`, pick the diff it reviews, as [Code review](#code-review) describes
3. Run the matching command below and wait for it to exit, as [Wait for a run](#wait-for-a-run) describes. If the CLI it names is not installed, say so, show the command, give the same prompt file to the session's own subagent tool with the same access, and report that the requested model did not review
4. Read the answer before you report, as [Read the result](#read-the-result) describes

## Review only

The child reads, runs commands and checks, uses the network, skills, and subagents, and reports. It must leave the checkout unchanged: the run fails when a tracked or untracked file changed. Ignored files, such as caches and build output, don't count. Claude and Grok also run without their file-editing tools; Codex has no such switch, so the check after the run is its guard.

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

Ask Grok for a review:

```bash
uv run <skill-dir>/scripts/headless.py grok --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Without a CLI name, the launcher runs the config's `harness`, as [Defaults](#defaults) describes. Keep the checkout and the reviewed artifact unchanged until the run exits. The launcher reports any change as the child's, and the answer would describe a stale revision.

## Review and fix

The child gets the same access, with every tool, and may edit files in `--cwd` to fix what it finds. It leaves commits, pushes, and comments to you.

For `--review-only` and `--review-fix`, the launcher runs `codex exec` without a sandbox. When a request asks for a sandboxed fixer, such as `-s workspace-write` with `.git` read-only and no network, run `codex exec` yourself with the `model` and `reasoning-level` of the config's `[codex]` table, then run the checks the child could not run offline and commit its changes:

```bash
codex exec -C /absolute/path/to/repo -s workspace-write -m <model> \
  -c model_reasoning_effort="<reasoning-level>" -o /tmp/fix.a1B2c3/answer.md - < /tmp/fix.a1B2c3/prompt.md
```

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

Ask Grok to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py grok --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Read `git diff` and run the relevant checks yourself before you report the fix. To keep working while a fixer runs, point `--cwd` at a separate worktree.

## Code review

`--code-review` runs the CLI's built-in reviewer on one diff. The run fails if the checkout changes. Without a CLI name, it runs Codex. Fetch first, since a worktree's local `main` often lags `origin/main`. The launcher rejects missing refs before starting the child.

- **Codex** runs `codex exec review` in a read-only sandbox, and the launcher rejects sandbox-bypass flags before the child starts. Give it exactly one diff: `--base BRANCH`, `--uncommitted`, or `--commit SHA`. Custom review instructions from `--prompt-file` replace the diff, because Codex refuses both together
- **Claude** runs Claude Code's `/review` without its file-editing tools. Give it `--base BRANCH` or `--commit SHA`. It reviews commits only, so `--base` refuses a checkout whose tracked files have uncommitted changes
- **Grok** runs its bundled `/review` in its read-only sandbox. Give it `--uncommitted`, or `--base origin/main` on a checkout with no changes, untracked files included. It has no other base and no commit target

```bash
git -C /absolute/path/to/repo fetch origin
uv run <skill-dir>/scripts/headless.py --code-review --base origin/main \
  --cwd /absolute/path/to/repo
uv run <skill-dir>/scripts/headless.py claude --code-review --base origin/main \
  --cwd /absolute/path/to/repo
uv run <skill-dir>/scripts/headless.py grok --code-review --uncommitted \
  --cwd /absolute/path/to/repo
```

To apply your own criteria, use `--review-only`. For mode commands and billing, read [Codex](references/codex/MetaSkill.md#modes), [Claude Code](references/claude/MetaSkill.md#modes), or [Grok](references/grok/MetaSkill.md#modes).

## Defaults

[config.toml](config.toml) holds the defaults, and each run prints the model and reasoning level that ran. Change a default in the skill's source copy of that file, never in a skill's prose; the next install overwrites an installed copy. For one run, pass `--model`, `--effort`, or `--config FILE` instead. `harness` names the CLI the launcher runs when the command names none. The `[codex]`, `[claude]`, and `[grok]` tables set each CLI's `model` and `reasoning-level`. The `[pi]` and `[opencode]` tables add a `provider`, since several providers serve one model, and their references build the command from them.

A model or reasoning level named in the request overrides the file through `--model` and `--effort`. Harnesses name the reasoning level differently: `--effort` reaches Codex as `model_reasoning_effort`, Claude as `--effort`, and Grok as `--reasoning-effort`, and a request may say reasoning, effort, or thinking for the same setting. Flags after `--` reach the child CLI unchanged, such as `-- -c 'web_search="live"'` for Codex. `uv run <skill-dir>/scripts/headless.py --help` lists every option.

## Read the result

On success, stdout holds one JSON line:

```json
{"ok":true,"file":"/tmp/headless-codex-review-only.8gcz_axu/answer.md","model":"gpt-6-luna","effort":"medium","session":"01a0f7d4-cbcf-7162-869b-94b331ed56b0","changed":[]}
```

`file` holds the child's answer in every mode. Read it with your file-reading tool, since an output filter such as RTK cuts long output. `model` comes from the child's own output: cite it when the request names a reviewer. Claude lists the model that did the work first, then any helper model it used. `changed` lists the files the child changed; outside Git it is `null`, because the launcher cannot check them. The answer file's folder also keeps `prompt.md` and the child's logs.

Read the whole answer before deciding the run succeeded. A one-line "no findings" without criteria is weak evidence: add the criteria and check results, then rerun.

On failure, stdout stays empty and the last line of stderr is `{"ok":false,"errors":[…]}`, one message per cause. Exit 1 means the child failed, gave no answer, was denied a tool, or changed the checkout under `--review-only` or `--code-review`, or the config is invalid. A failure found after the launcher saved the run result also carries `file` and the other fields above. Any other failure after the run folder exists, such as a timeout, an interrupt, or a failed write, carries `files`, the paths that folder holds so far; an earlier failure carries only `errors`. Change the cause before a retry. Exit 2 is a usage error, such as an effort the CLI does not accept.

For a follow-up round on the same thread, pass the `session` to `--resume`. A fresh run gives an independent opinion.

## Wait for a run

A run often takes 5 to 15 minutes, and the launcher blocks until the child exits. In Claude Code, start the command with the Bash tool's `run_in_background` set to `true` and `timeout` set to its maximum, `7200000` milliseconds, then wait for the completion notification. Bash's 30-minute background default would otherwise stop a run before the launcher's 2-hour `--timeout`. In Codex, run it in the foreground: the shell tool keeps a long command alive and lets you poll it until it exits. Keep the launcher in the command you run, because a harness stops a process that `&` left behind when that command ends.

That completion notification, or in Codex the command's exit, is the only wait. The child never posts to the PR, so nothing it does would wake a PR watch. Never monitor or babysit the PR for a headless run, such as with T3 Code's `watch_pull_request`.

## Limits

Read the [Codex reference](references/codex/MetaSkill.md), the [Claude Code reference](references/claude/MetaSkill.md), or the [Grok reference](references/grok/MetaSkill.md) for what the launcher leaves to you: untrusted repositories, a parent inside a Codex sandbox, images and web search, `@path` mentions in Claude prompts, background tasks in Claude, Grok's folder trust, and testing a changed skill. The [glossary](references/GLOSSARY.md) defines the terms. To maintain this skill, follow the [update checklist](references/UPDATE.md).
