# Run Codex headlessly

`scripts/headless.py codex` runs `codex exec` with the same tools under `--review-only` and `--review-fix`; read it for the exact flags. It passes `--dangerously-bypass-approvals-and-sandbox`, so the child keeps your config, skills, network, and subagents, and it saves the session for `--resume`. The prompt arrives on stdin, so no run waits on an open terminal. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and the [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) own current CLI behavior. Check `codex exec --help` on the installed version before you pass extra flags after `--`; the [flag lookup](references/FLAGS.md) maps them.

Run the launcher only in repositories you trust. For another repository, run `codex exec -s read-only -c 'approval_policy="never"'` yourself.

## Run from inside a Codex session

A Codex parent runs shell commands inside its own sandbox, and the child inherits it. When that sandbox blocks the network or writes outside the checkout, run the launcher outside it through the parent's escalation control.

## Choose optional tools

Pass these after `--`:

| Task | Flags after `--` |
| --- | --- |
| Verify a claim against current official documentation | `-c 'web_search="live"'`, and ask for source links |
| Inspect local screenshots or diagrams named in the prompt | `-c 'features.view_image=true'` |
| Supply an image with the prompt | `-i /absolute/path/screenshot.png` |

`features.view_image` lets the child open local images during the task; `-i` attaches an image directly. Neither generates images. Installed CLI 0.159.0 ignores the `tools.view_image` setting still shown in the configuration reference; confirm the effective value with `codex -c 'features.view_image=true' features list`.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.agents/skills/<name>/` and disable every installed copy in one array after `--`:

```bash
-- -c 'skills.config=[{path="/absolute/path/.codex/skills/<name>/SKILL.md",enabled=false}]'
```

Add one `{path=...,enabled=false}` entry per installed copy, such as `~/.agents/skills/<name>/SKILL.md` when that folder exists. On CLI 0.159.3, a low-effort run that reads the skill a request needs, then stops and names its path, shows which copy loads.

Write a `.gitignore` holding `*` into the copied skill folder, so neither git nor the tested agent counts the copy as an uncommitted change.

## Models

Check the [current Codex model list](https://learn.chatgpt.com/docs/models) for model names and supported reasoning levels. An installed CLI's catalog can differ by sign-in and rollout; `codex debug models` shows it.

For maintenance, follow the [update checklist](../UPDATE.md).
