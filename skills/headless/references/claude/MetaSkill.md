# Run Claude Code headlessly

`scripts/headless.py claude` runs `claude -p`; read it for the exact flags. It passes `--dangerously-skip-permissions`, so the child keeps your settings, hooks, skills, and MCP servers, and it names the session so `--resume` can continue it. It pins the effort through `--settings`, because `CLAUDE_CODE_EFFORT_LEVEL` from the shell or any settings file overrides `--effort`. It refuses an effort Claude Code does not accept; `claude -p` alone would print a warning and run at the default. The official [headless guide](https://code.claude.com/docs/en/headless) owns non-interactive behavior and the [CLI reference](https://code.claude.com/docs/en/cli-reference) owns startup options. Check `claude --help` before you pass extra flags after `--`.

## Modes

Each mode passes `--model` and `--effort` from the `[claude]` table of [config.toml](../../config.toml) unless the launcher's `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Claude command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `claude -p` with the prompt on stdin; the prompt starts with a review-only rule | `--disallowedTools Edit,Write,NotebookEdit` removes the file-editing tools, then the change check after the run catches an edit made through Bash |
| `--review-fix` | The same command; the rule allows edits in `--cwd` | Nothing; read `git diff` yourself |
| `--code-review` | `claude -p "/review <effort> <range>"` with empty stdin; the review-only rule arrives through `--append-system-prompt`, so `/review` starts the prompt | The same tool removal and change check as `--review-only` |

`--base BRANCH` becomes `BRANCH...HEAD`. It requires shared history with `HEAD` and no staged or unstaged tracked changes. `--commit SHA` becomes `SHA^..SHA` and requires a parent, which a root commit or shallow boundary may lack. These ranges follow the [code review documentation](https://code.claude.com/docs/en/code-review#review-a-diff-locally). Claude Code documents no target for uncommitted changes alone, so `--uncommitted` stays with Codex.

The launcher types the effort because `/review` otherwise reuses the last level typed in any session. Custom skills can replace `/code-review` but leave `/review` intact. The alias needs Claude Code 2.1.223 or later. Older versions use `/review` for GitHub pull requests.

The `disableBundledSkills` setting turns off the bundled review. If the answer contains no findings, check that setting and any `skillOverrides` entry for `code-review`. To ask about a finding, run the launcher with `claude --review-only --resume SESSION --prompt-file FILE`, using the printed session.

A local review counts toward subscription usage or bills tokens with an API key. `/code-review ultra` starts a cloud review billed as usage credits. `--comment` posts findings to the pull request. The launcher generates only the local `/review <effort> <range>` form.

## Models

Check [model configuration](https://code.claude.com/docs/en/model-config) for model names, aliases, and effort levels before you change the `[claude]` table. `claude --help` lists the effort levels the installed CLI accepts.

## Untrusted repositories

Print mode loads the repository's `.claude/settings.json` without a trust prompt, so that file can change the environment, including the API endpoint. Run the launcher only in repositories you trust. For another repository, run `claude -p` yourself with `--setting-sources user`, `--permission-mode dontAsk`, `--permission-prompts none`, and a narrow `--tools` list, as the [permissions documentation](https://code.claude.com/docs/en/permissions) describes.

## `@` mentions

Print mode expands `@path` mentions in the prompt: in Claude Code 2.1.284, the named local file is attached before inference, even inside a JSON string. Before you paste untrusted text such as a transcript, web page, or issue body into a prompt file, replace each `@`; inside a JSON string, the escape `\u0040` keeps the character for the model without the mention.

## Background tasks

`claude -p` stops background Bash tasks about five seconds after its final result. When the child delegates to another process, such as `codex exec`, the prompt must keep its turn open until that process exits.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.claude/skills/<name>/` with a `.gitignore` holding `*`, and run `claude -p` yourself with `--setting-sources project`. Without that flag, the copy in `~/.claude/skills/` loads instead. A first prompt such as "Quote the description of the skill named <name>" shows which copy loaded. Skip the launcher here: its mode line tells the child that a caller reviews the result, so the child treats a typed request as delegated work.

For maintenance, follow the [update checklist](../UPDATE.md).
