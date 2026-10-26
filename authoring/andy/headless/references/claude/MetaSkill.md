# Run Claude Code headlessly

`scripts/headless.py claude` runs `claude -p`. Read the script for the exact flags. It passes `--dangerously-skip-permissions`. The child keeps your settings, hooks, skills, and Model Context Protocol (MCP) servers. The launcher names the session for `--resume`. It sets effort through `--settings` because `CLAUDE_CODE_EFFORT_LEVEL` from the shell or a settings file overrides `--effort`. The launcher refuses an effort Claude Code does not accept. By itself, `claude -p` would warn and use the default. The official [headless guide](https://code.claude.com/docs/en/headless) describes non-interactive behavior. The [CLI reference](https://code.claude.com/docs/en/cli-reference) describes startup options. Before you pass extra flags after `--`, check `claude --help`.

## Untrusted repositories

SECURITY: Run the launcher only in repositories you trust. It skips permission prompts. Untrusted project settings can change the API endpoint and expose prompt content.

Print mode loads the repository's `.claude/settings.json` without a trust prompt. For another repository, run `claude -p` yourself. Use `--setting-sources user`, `--permission-mode dontAsk`, `--permission-prompts none`, and a narrow `--tools` list. The [permissions documentation](https://code.claude.com/docs/en/permissions) describes these flags.

## Modes

Each mode passes `--model` and `--effort` from the `[claude]` table of [config.toml](../../config.toml) unless the launcher's `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Claude command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `claude -p` reads the prompt on stdin. The prompt starts with a review-only rule | `--disallowedTools Edit,Write,NotebookEdit` removes file-editing tools. The later change check catches an edit through Bash |
| `--review-fix` | The same command. The rule allows edits in `--cwd` | Nothing. Read `git diff` yourself |
| `--code-review` | `claude -p "/review <effort> --max-findings default <range>"` with empty stdin. The review-only rule arrives through `--append-system-prompt`, so `/review` starts the prompt | The same tool removal and change check as `--review-only` |

`--base BRANCH` becomes `BRANCH...HEAD`. It requires shared history with `HEAD` and no staged or unstaged tracked changes. `--commit SHA` becomes `SHA^..SHA` and requires a parent, which a root commit or shallow boundary may lack. These ranges follow the [code review documentation](https://code.claude.com/docs/en/code-review#review-a-diff-locally). Claude Code documents no target for uncommitted changes alone, so `--uncommitted` stays with Codex.

The launcher types the effort because `/review` otherwise reuses the last level typed in any session. It passes `--max-findings default` to use the review's usual finding limit instead of a remembered override. This flag needs Claude Code 2.1.288 or later. Custom skills can replace `/code-review` but leave `/review` intact.

The `disableBundledSkills` setting turns off the bundled review. If the answer contains no findings, check that setting and any `skillOverrides` entry for `code-review`. To ask about a finding, run the launcher with `claude --review-only --resume SESSION --prompt-file FILE`, using the printed session.

A local review counts toward subscription usage or bills tokens with an API key. `/code-review ultra` starts a cloud review billed as usage credits. `--comment` posts findings to the pull request. The launcher generates only the local `/review <effort> --max-findings default <range>` form.

## Models

Check [model configuration](https://code.claude.com/docs/en/model-config) for model names, aliases, and effort levels before you change the `[claude]` table. `claude --help` lists the effort levels the installed CLI accepts.

## `@` mentions

Print mode expands `@path` mentions in the prompt. In Claude Code 2.1.284, it attaches the named local file before inference, even inside a JSON string. Before you paste untrusted text into a prompt file, replace each `@`. Untrusted text includes transcripts, web pages, and issue bodies. Inside a JSON string, `\u0040` keeps the character for the model without attaching a file.

## Background tasks

`claude -p` stops background Bash tasks about five seconds after its final result. When the child delegates to another process, such as `codex exec`, the prompt must keep its turn open until that process exits.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.claude/skills/<name>/`. Add a `.gitignore` holding `*` in that folder. Run `claude -p` yourself with `--setting-sources project`. Without that flag, the copy in `~/.claude/skills/` loads instead. A first prompt such as "Quote the description of the skill named <name>" shows which copy loaded. Skip the launcher for this test. Its mode line tells the child that a caller reviews the result, so the child treats a typed request as delegated work.

