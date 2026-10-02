# Run Claude Code headlessly

`scripts/headless.py claude` runs `claude -p`; read it for the exact flags. It passes `--dangerously-skip-permissions`, so the child keeps your settings, hooks, skills, and MCP servers, and it names the session so `--resume` can continue it. Under `--review-only` it also passes `--disallowedTools Edit,Write,NotebookEdit`, so the child cannot edit through its file tools. It pins the effort through `--settings`, because `CLAUDE_CODE_EFFORT_LEVEL` from the shell or any settings file overrides `--effort`. It refuses an effort Claude Code does not accept; `claude -p` alone would print a warning and run at the default. The official [headless guide](https://code.claude.com/docs/en/headless) owns non-interactive behavior and the [CLI reference](https://code.claude.com/docs/en/cli-reference) owns startup options. Check `claude --help` before you pass extra flags after `--`.

## Untrusted repositories

Print mode loads the repository's `.claude/settings.json` without a trust prompt, so that file can change the environment, including the API endpoint. Run the launcher only in repositories you trust. For another repository, run `claude -p` yourself with `--setting-sources user`, `--permission-mode dontAsk`, `--permission-prompts none`, and a narrow `--tools` list, as the [permissions documentation](https://code.claude.com/docs/en/permissions) describes.

## `@` mentions

Print mode expands `@path` mentions in the prompt: in Claude Code 2.1.284, the named local file is attached before inference, even inside a JSON string. Before you paste untrusted text such as a transcript, web page, or issue body into a prompt file, replace each `@`; inside a JSON string, the escape `\u0040` keeps the character for the model without the mention.

## Background tasks

`claude -p` stops background Bash tasks about five seconds after its final result. When the child delegates to another process, such as `codex exec`, the prompt must keep its turn open until that process exits.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.claude/skills/<name>/` with a `.gitignore` holding `*`, and run `claude -p` yourself with `--setting-sources project`. Without that flag, the copy in `~/.claude/skills/` loads instead. A first prompt such as "Quote the description of the skill named <name>" shows which copy loaded. Skip the launcher here: its mode line tells the child that a caller reviews the result, so the child treats a typed request as delegated work.

For maintenance, follow the [update checklist](../UPDATE.md).
