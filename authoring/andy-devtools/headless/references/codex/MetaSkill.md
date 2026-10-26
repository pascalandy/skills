# Run Codex headlessly

`scripts/headless.py codex` runs `codex exec` with the same tools under `--review-only` and `--review-fix`. Read the script for the exact flags. It passes `--dangerously-bypass-approvals-and-sandbox`. The child keeps your config, skills, network, and subagents. The launcher saves the session for `--resume`. The prompt arrives on stdin, so the run does not wait on an open terminal. The [non-interactive guide](https://learn.chatgpt.com/docs/non-interactive-mode) and [`codex exec` reference](https://learn.chatgpt.com/docs/developer-commands#codex-exec) describe current CLI behavior. Before you pass extra flags after `--`, check the installed `codex exec --help`.

SECURITY: Run the launcher only in repositories you trust. It bypasses approvals and the sandbox. Untrusted instructions can run commands or expose credentials.

For another repository, run `codex exec -s read-only -c 'approval_policy="never"'` yourself.

## Modes

Each mode takes `-m` and `model_reasoning_effort` from the `[codex]` table of [config.toml](../../config.toml) unless `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Codex command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `codex exec` without sandbox. The prompt starts with a review-only rule | The change check after the run. Codex has no switch that removes its editing tools |
| `--review-fix` | The same command. The rule allows edits in `--cwd` | Nothing. Read `git diff` yourself |
| `--code-review` | `codex exec review` with `sandbox_mode="read-only"`, `approval_policy="never"`, and the diff flag | The read-only sandbox, then the change check |

The first two modes use `exec` because `codex exec review` refuses custom instructions with a diff flag. The `--base`, `--uncommitted`, and `--commit` flags each conflict with its prompt argument. A run with the caller's criteria, such as a premortem, needs `exec`.

`codex exec review` reads its model from `review_model`, not `-m`. The `-m` flag sets only the `model:` line Codex prints. The launcher passes the same model to both, so that line stays true. When the review fails, Codex can still exit 0. It can write `Review was interrupted. Please re-run /review…` as its answer. The launcher counts that answer as a failure. To ask about a finding, pass the printed session to `--review-only --resume`. The `--code-review` mode itself takes no `--resume`. These behaviors were verified on Codex CLI 0.159.3.

The separate Code Review allowance on a ChatGPT plan applies only to reviews through GitHub. These include `@codex review` on a pull request and automatic repository reviews. A local `--code-review` counts toward general usage like the other modes. See [Codex pricing](https://learn.chatgpt.com/docs/pricing).

## Run from inside a Codex session

A Codex parent runs shell commands inside its own sandbox, and the child inherits it. When that sandbox blocks the network or writes outside the checkout, run the launcher outside it through the parent's escalation control.

## Choose optional tools

Pass these after `--`:

| Task | Flags after `--` |
| --- | --- |
| Verify a claim against current official documentation | `-c 'web_search="live"'`, and ask for source links |
| Inspect local screenshots or diagrams named in the prompt | `-c 'features.view_image=true'` |
| Supply an image with the prompt | `-i /absolute/path/screenshot.png` |

`features.view_image` lets the child open local images during the task. The `-i` flag attaches an image directly. Neither option generates images. Installed CLI 0.159.0 ignores the `tools.view_image` setting still shown in the configuration reference. Confirm the effective value with `codex -c 'features.view_image=true' features list`.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.agents/skills/<name>/`. Then disable every installed copy in one array after `--`:

```bash
-- -c 'skills.config=[{path="/absolute/path/.codex/skills/<name>/SKILL.md",enabled=false}]'
```

Add one `{path=...,enabled=false}` entry per installed copy. Include `~/.agents/skills/<name>/SKILL.md` when that folder exists. On CLI 0.159.3, a low-effort run can show which copy loads. Ask it to read the required skill, stop, and name its path.

Write a `.gitignore` holding `*` into the copied skill folder, so neither git nor the tested agent counts the copy as an uncommitted change.

## Models

Before you change the `[codex]` table, check the [current Codex model list](https://learn.chatgpt.com/docs/models) for names and reasoning levels. An installed CLI's catalog can differ by sign-in and rollout. The `codex debug models` command shows that catalog.

