# Run Grok Build headlessly

`scripts/headless.py grok` runs `grok` with `--prompt-file` under `--review-only` and `--review-fix`. Grok does not read prompts from stdin. Read the script for the exact flags. It passes `--always-approve`, so the child keeps your config, skills, Model Context Protocol (MCP) servers, and web search. The launcher names the session for `--resume`. The `--no-leader` and `--no-auto-update` flags keep each run one process on the installed version. The [headless guide](https://docs.x.ai/build/cli/headless-scripting) and [CLI reference](https://docs.x.ai/build/cli/reference) describe current behavior. The copy in `~/.grok/docs/user-guide/` matches the installed CLI. Before you pass extra flags after `--`, check `grok --help`.

Grok's folder trust controls how it loads a repository's `AGENTS.md`, skills, hooks, and MCP servers. Grok loads them only in a folder you trusted. The launcher sets `GROK_FOLDER_TRUST=0` for the child. That setting turns folder trust off for one run without recording a grant.

SECURITY: Run the launcher only in repositories you trust. Without folder trust, untrusted project instructions or hooks can run and cause harm.

For another repository, run `grok` yourself without `GROK_FOLDER_TRUST=0` or `--trust`. Use `--tools read_file,grep,list_dir`.

## Modes

Each mode passes `-m` and `--reasoning-effort` from the `[grok]` table of [config.toml](../../config.toml) unless `--model` or `--effort` overrides them. `-v` prints the exact command a run used.

| Mode | Grok command | What keeps the checkout unchanged |
| --- | --- | --- |
| `--review-only` | `grok --prompt-file`. The prompt starts with a review-only rule | `--disallowed-tools` removes file-editing tools. The later change check catches shell edits |
| `--review-fix` | The same command with every tool. The rule allows edits in `--cwd` | Nothing. Read `git diff` yourself |
| `--code-review` | `grok -p "/review --local"` for `--uncommitted`, or `"/review --main"` for `--base origin/main`, with `--sandbox read-only`. The review-only rule arrives through `--rules` | The read-only sandbox, then the change check. `/review` keeps its write tool for review files in the writable temp directory |

`/review` is a skill bundled with Grok in `~/.grok/bundled/skills/review/`. Its `--main` compares the branch with its merge-base on `origin/main`. The `--main` mode uses `origin/master` when `origin/main` is missing. It refuses a checkout with changes, including untracked files. The launcher rejects another `--base`, a changed checkout, and `--commit` before Grok starts. Grok's report contains the top issues and the path to the full review. The review rule asks Grok to end with the whole review. The `--pr` and `--stack` modes post to GitHub. The launcher never types them. A skill named `review` in a folder Grok scans replaces the bundled skill.

The read-only sandbox lets Grok write only to `~/.grok` and the temp directories. On Linux, it also cuts network access for commands Grok runs. On macOS, it blocks the same writes but leaves command network access open. Only the rule stops a child from posting with `gh`. A checkout inside a temp directory stays writable. `/review` fails when `TMPDIR` points outside the temp directories because it saves files there. Grok refuses a second `--sandbox`, so `-- --sandbox off` stops before the model runs. A resumed session keeps its sandbox. After `--review-only --resume` on a code-review session, the child can answer questions. A test that writes a cache in the checkout fails.

The exit status misses a refusal or an empty answer. The launcher reads the stream's terminal `result`. It fails the run on an error, a stop other than `end_turn`, or no answer. The launcher's `model` comes from assistant messages. The stream's first line repeats the requested model even when Grok rejects it. Grok checks each model's reasoning levels itself. On rejection, it exits 1 and names the levels it accepts. A `@path` in a `--prompt-file` prompt stays text. Grok attaches no file. These behaviors were verified on Grok Build 1.0.46.

With a grok.com sign-in, headless runs draw from the plan's usage pool. With `XAI_API_KEY`, they bill API pricing. See the [usage FAQ](https://docs.x.ai/grok/faq).

## Choose optional tools

Web search is on by default. Pass `--disable-web-search` after `--` to remove search and fetch.

## Test a changed skill

To compare a changed skill with its installed copy, copy the variant into `<cwd>/.agents/skills/<name>/`. Add a `.gitignore` holding `*` in that folder. The launcher runs Grok with folder trust off. Then a project copy replaces a user copy of the same name, including one in `~/.claude/skills/`. Before a paid run, confirm which copy loads:

```bash
cd /absolute/path/to/repo && GROK_FOLDER_TRUST=0 grok inspect --json \
  | jq '.skills[] | select(.name == "<name>") | .source'
```

## Models

Check the [current model list](https://docs.x.ai/developers/models) for model names and reasoning levels before you change the `[grok]` table. `grok models` lists the models the signed-in account can use.

