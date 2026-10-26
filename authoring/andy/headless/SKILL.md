---
name: "headless"
description: "Use when running `codex exec`, `codex exec review`, Claude Code, Grok, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. `headless` may arrive as any voice-to-text spelling that sounds like it, such as `endless` or `adless`."
kind: "dev"
---

# Headless CLI agents

SECURITY: Run the launcher only in repositories you trust. Its unsandboxed modes can run untrusted commands or expose credentials.

Run Codex, Claude Code, or Grok as a child agent with `scripts/headless.py`. The launcher uses one command form, a required mode flag, one config file, and fixed exit codes. It waits for the child, checks the result, and prints the path to the saved answer. `<skill-dir>` is the directory that holds this file.

The launcher does not run OpenCode or Pi yet (#281). For those CLIs, read [OpenCode](references/opencode/MetaSkill.md) or [Pi](references/pi/MetaSkill.md).

1. Pick the requested mode: `--review-only`, `--review-fix`, or `--code-review` for the CLI's own reviewer
2. For `--review-only` or `--review-fix`, create a prompt file in a `mktemp -d` folder
3. In that file, give the scope, criteria, expected result, and trusted check results
4. Add facts the child cannot find to the prompt file
5. For `--code-review`, select the diff as [Code review](#code-review) describes
6. Run the matching command below
7. Wait for the command to exit as [Wait for a run](#wait-for-a-run) describes
8. If the CLI is unavailable, report that failure and show the command
9. If the CLI is unavailable, give the prompt file or selected diff to the session's own subagent tool
10. If the CLI is unavailable, tell that subagent to use the same access
11. If the CLI is unavailable, state that the requested model did not review
12. Read the answer before you report, as [Read the result](#read-the-result) describes

## Review only

The child can read, run commands and checks, use the network, skills, and subagents, and report.

It must leave the checkout unchanged. The launcher fails the run if a tracked or untracked file changes. Ignored files, such as caches and build output, do not count. Claude Code and Grok also run without their file-editing tools. Codex has no such switch, so the change check guards its run.

Ask Codex for a review:

```bash
uv run <skill-dir>/scripts/headless.py codex --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude Code for a review:

```bash
uv run <skill-dir>/scripts/headless.py claude --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Grok for a review:

```bash
uv run <skill-dir>/scripts/headless.py grok --review-only \
  --prompt-file /tmp/review.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Without a CLI name, the launcher runs the config's `harness`, as [Defaults](#defaults) describes. Keep the checkout and reviewed artifact unchanged until the run exits. The launcher attributes any change to the child. A concurrent change would also make the answer describe a stale revision.

## Review and fix

The child gets the same access, with every tool. It may edit files in `--cwd` to fix its findings. You make the commits, pushes, and comments.

For `--review-only` and `--review-fix`, the launcher runs `codex exec` without a sandbox. If the request asks for a sandboxed fixer, run `codex exec` yourself. Use the `model` and `reasoning-level` from the config's `[codex]` table. For example, `-s workspace-write` keeps `.git` read-only and blocks network access. After the child exits, run the checks it could not run offline. Then commit its changes:

```bash
codex exec -C /absolute/path/to/repo -s workspace-write -c approval_policy="never" -m <model> \
  -c model_reasoning_effort="<reasoning-level>" -o /tmp/fix.a1B2c3/answer.md - < /tmp/fix.a1B2c3/prompt.md
```

Ask Codex to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py codex --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Claude Code to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py claude --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Ask Grok to review and fix:

```bash
uv run <skill-dir>/scripts/headless.py grok --review-fix \
  --prompt-file /tmp/fix.a1B2c3/prompt.md --cwd /absolute/path/to/repo
```

Read `git diff` and run the relevant checks before you report the fix. To work while a fixer runs, point `--cwd` at a separate worktree.

## Code review

`--code-review` runs the CLI's built-in reviewer on one diff. The launcher fails the run if the checkout changes. Without a CLI name, it runs Codex. Fetch first because a worktree's local `main` often lags `origin/main`. The launcher rejects missing refs before it starts the child.

- **Codex** runs `codex exec review` in a read-only sandbox. The launcher rejects sandbox-bypass flags before the child starts. Give Codex one diff: `--base BRANCH`, `--uncommitted`, or `--commit SHA`. Custom instructions from `--prompt-file` replace the diff because Codex refuses both together
- **Claude Code** runs `/review` without its file-editing tools. Give Claude Code `--base BRANCH` or `--commit SHA`. Claude Code reviews commits only, so `--base` refuses uncommitted tracked changes
- **Grok** runs its bundled `/review` in a read-only sandbox. Give Grok `--uncommitted` or `--base origin/main` on an unchanged checkout, including untracked files. Grok has no other base or commit target

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

[config.toml](config.toml) holds the defaults. Each run prints the model and reasoning level that ran. Change defaults in the skill's source copy of `config.toml`. Do not change defaults in a skill's prose. An installation overwrites its own copy. For one run, pass `--model`, `--effort`, or `--config FILE`. `harness` names the CLI that runs when the command names none. The `[codex]`, `[claude]`, and `[grok]` tables set each CLI's `model` and `reasoning-level`. The `[pi]` and `[opencode]` tables also set a `provider` because several providers can serve one model. Their references build commands from these values.

A model or reasoning level in the request overrides the file through `--model` or `--effort`. The CLIs use different names for reasoning level. The launcher sends `--effort` to Codex as `model_reasoning_effort`, to Claude Code as `--effort`, and to Grok as `--reasoning-effort`. The request may call this setting reasoning, effort, or thinking. Flags after `--` reach the child CLI unchanged, such as `-- -c 'web_search="live"'` for Codex. Run `uv run <skill-dir>/scripts/headless.py --help` to list every option.

## Read the result

On success, stdout holds one JSON line:

```json
{"ok":true,"file":"/tmp/headless-codex-review-only.8gcz_axu/answer.md","model":"gpt-6-luna","effort":"medium","session":"01a0f7d4-cbcf-7162-869b-94b331ed56b0","changed":[]}
```

`file` holds the child's answer in every mode. Read that file to get the whole answer. Its folder also holds `prompt.md` and the child's logs.

`model` comes from the child's output. Cite it when the request names a reviewer. Claude Code lists the primary model first, followed by helper models.

`changed` lists the files the child changed. Outside Git, it is `null` because the launcher cannot check file changes.

Read the whole answer before deciding the run succeeded. A one-line "no findings" without criteria is weak evidence: add the criteria and check results, then rerun.

On failure, stdout stays empty. The last line of stderr is `{"ok":false,"errors":[…]}`, with one message per cause. Exit 1 can mean that the child failed, gave no answer, or was denied a tool. It also covers a changed checkout under `--review-only` or `--code-review`, or an invalid config. A failure found after the launcher saves the run result also carries `file` and the other fields above. Any other failure after the run folder exists carries `files`, including a timeout, interrupt, or failed write. This field lists the paths the folder holds so far. An earlier failure carries only `errors`. Exit 2 is a usage error, such as an unsupported effort. Change the cause before a retry.

For a follow-up round on the same thread, pass the `session` to `--resume`. A fresh run gives an independent opinion.

## Wait for a run

A run often takes 5 to 15 minutes. The launcher blocks until the child exits. In Claude Code, set the Bash tool's `run_in_background` to `true`. Set its `timeout` to the maximum, `7200000` milliseconds. Then wait for the completion notification. Bash's 30-minute background default would otherwise stop a run before the launcher's 2-hour `--timeout`. In Codex, run the launcher in the foreground. The shell tool keeps a long command alive and lets you poll it until it exits. Keep the launcher in the command you run. A harness stops a process left behind with `&` when that command ends.

That completion notification, or in Codex the command's exit, is the only wait. The child never posts to the PR, so nothing it does would wake a PR watch. Never monitor or babysit the PR for a headless run, such as with T3 Code's `watch_pull_request`.

## Limits

Read the reference for the CLI you use:

- [Codex](references/codex/MetaSkill.md) covers untrusted repositories, a parent inside a Codex sandbox, images, web search, and testing a changed skill
- [Claude Code](references/claude/MetaSkill.md) covers untrusted repositories, `@path` mentions, background tasks, and testing a changed skill
- [Grok](references/grok/MetaSkill.md) covers folder trust, web search, and testing a changed skill

The [glossary](references/GLOSSARY.md) defines the terms.

For installed flags, read the [Codex flag lookup](references/codex/references/FLAGS.md) or [Grok flag lookup](references/grok/references/FLAGS.md).

To maintain this skill, follow the [update checklist](references/UPDATE.md).
