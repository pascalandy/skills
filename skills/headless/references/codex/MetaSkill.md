# Run Codex headlessly

`scripts/headless.py codex` runs `codex exec` with the same tools under `--review-only` and `--review-fix`; read it for the exact flags. It passes `--dangerously-bypass-approvals-and-sandbox`, so the child keeps your config, skills, network, and subagents, and it saves the session for `--resume`. The prompt arrives on stdin, so no run waits on an open terminal. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and the [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) own current CLI behavior. Check `codex exec --help` on the installed version before you pass extra flags after `--`; the [flag lookup](references/FLAGS.md) maps them.

Run the launcher only in repositories you trust. For another repository, run `codex exec -s read-only -c 'approval_policy="never"'` yourself.

## Modes

Each mode takes `-m` and `model_reasoning_effort` from the `[codex]` table of [config.toml](../../config.toml) unless `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Codex command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `codex exec` without sandbox; the prompt starts with a review-only rule | The change check after the run. Codex has no switch that removes its editing tools |
| `--review-fix` | The same command; the rule allows edits in `--cwd` | Nothing; read `git diff` yourself |
| `--code-review` | `codex exec review` with `sandbox_mode="read-only"`, `approval_policy="never"`, and the diff flag | The read-only sandbox, then the change check |

The first two modes use `exec` because `codex exec review` refuses custom instructions together with a diff flag: `--base`, `--uncommitted`, and `--commit` each conflict with its prompt argument. A run that carries the caller's criteria, such as a premortem, needs `exec`.

`codex exec review` reads its model from `review_model`, not `-m`. `-m` only sets the `model:` line Codex prints, so the launcher passes the same model to both and the line stays true. When the review fails, Codex can still exit 0 and write `Review was interrupted. Please re-run /review…` as its answer; the launcher counts that as a failure. To ask about a finding, pass the review's printed session to `--review-only --resume`; `--code-review` itself takes no `--resume`. These behaviors were verified on Codex CLI 0.159.3.

The separate Code Review allowance on a ChatGPT plan applies only when Codex reviews through GitHub, such as `@codex review` on a pull request or automatic reviews on a repository. A local `--code-review` counts toward general usage like the other modes; see [Codex pricing](https://learn.chatgpt.com/docs/pricing).

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

Check the [current Codex model list](https://learn.chatgpt.com/docs/models) for model names and supported reasoning levels before you change the `[codex]` table. An installed CLI's catalog can differ by sign-in and rollout; `codex debug models` shows it.

For maintenance, follow the [update checklist](../UPDATE.md).
