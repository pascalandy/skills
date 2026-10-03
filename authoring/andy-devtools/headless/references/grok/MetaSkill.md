# Run Grok Build headlessly

`scripts/headless.py grok` runs `grok` with `--prompt-file` under `--review-only` and `--review-fix`, since Grok reads no prompt from stdin; read the script for the exact flags. It passes `--always-approve`, so the child keeps your config, skills, MCP servers, and web search, and it names the session so `--resume` can continue it. `--no-leader` and `--no-auto-update` keep each run one process on the installed version. The [headless guide](https://docs.x.ai/build/cli/headless-scripting) and the [CLI reference](https://docs.x.ai/build/cli/reference) own current behavior, and `~/.grok/docs/user-guide/` holds the copy that matches the installed CLI. Check `grok --help` before you pass extra flags after `--`; the [flag lookup](references/FLAGS.md) maps them.

Grok's folder trust gates a repository's `AGENTS.md`, skills, hooks, and MCP servers: Grok loads them only in a folder you trusted. The launcher sets `GROK_FOLDER_TRUST=0` for the child, which turns folder trust off for one run without recording a grant, so run it only in repositories you trust. For another repository, run `grok` yourself without that variable or `--trust`, with `--tools read_file,grep,list_dir`.

## Modes

Each mode passes `-m` and `--reasoning-effort` from the `[grok]` table of [config.toml](../../config.toml) unless `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Grok command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `grok --prompt-file`; the prompt starts with a review-only rule | `--disallowed-tools` removes the file-editing tools, then the change check after the run catches an edit made through the shell |
| `--review-fix` | The same command with every tool; the rule allows edits in `--cwd` | Nothing; read `git diff` yourself |
| `--code-review` | `grok -p "/review --local"` for `--uncommitted`, or `"/review --main"` for `--base origin/main`; the review-only rule arrives through `--rules` | The change check. `/review` keeps its write tool for the review files it saves in the temporary directory |

`/review` is a skill bundled with Grok, in `~/.grok/bundled/skills/review/`. Its `--main` compares the branch with its merge-base on `origin/main`, or `origin/master` when `origin/main` is missing, and refuses a checkout with changes, untracked files included. The launcher refuses another `--base`, such a checkout, and `--commit` before Grok starts. Grok's own report keeps the top issues and the path of the full review, so the rule asks it to end with the whole review. Its `--pr` and `--stack` modes post to GitHub, and the launcher never types them. A skill named `review` in a folder Grok scans replaces the bundled one.

The exit status misses a refusal or an empty answer, so the launcher reads the stream's terminal `result` and fails the run on an error, a stop other than `end_turn`, or no answer. The `model` line comes from the assistant messages, because the stream's first line repeats the requested model even when Grok rejects it. Grok checks each model's reasoning levels itself and exits 1 naming the ones it accepts. A `@path` in a `--prompt-file` prompt stays text; Grok attaches no file. These behaviors were verified on Grok Build 1.0.46.

With a grok.com sign-in, headless runs draw from the plan's usage pool; with `XAI_API_KEY`, they bill API pricing. See the [usage FAQ](https://docs.x.ai/grok/faq).

## Choose optional tools

Web search is on by default. Pass `--disable-web-search` after `--` to remove search and fetch.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.agents/skills/<name>/` with a `.gitignore` holding `*`. With folder trust off, as the launcher runs Grok, a project copy replaces a user copy of the same name, including one in `~/.claude/skills/`. Before a paid run, confirm which copy loads:

```bash
cd /absolute/path/to/repo && GROK_FOLDER_TRUST=0 grok inspect --json \
  | jq '.skills[] | select(.name == "<name>") | .source'
```

## Models

Check the [current model list](https://docs.x.ai/developers/models) for model names and reasoning levels before you change the `[grok]` table. `grok models` lists the models the signed-in account can use.

For maintenance, follow the [update checklist](../UPDATE.md).
