---
name: Script output
description: How a script answers in one JSON line, how agents and scripts read the answer, and why each choice was made
tags:
  - area/ea
  - kind/doc
  - topic/scripts
  - status/stable
date_created: 2026-10-04
date_updated: 2026-10-05
---

A script answers in one line of JSON, so an agent or another script knows the outcome from one read. The rule needs no Python, so a project in Bash or TypeScript can apply it as written. [State](#state) lists the scripts here that follow it today

## The rule

- Everything passed: `{"ok":true}` on stdout, exit code 0
- Anything else: stdout stays empty, the last line of stderr is `{"ok":false,"errors":["…"]}`, and the exit code is not 0. Each error says what failed and the command that fixes it
- `ok` always agrees with the exit code
- A success with a warning is not a success: what needs action fails the command, and the rest moves to `-v`

## Read the answer

An agent runs the command and reads the line. It adds nothing after the command, since `| jq … >/dev/null` brings the silence back

A script tests the exit code, or pipes stdout to `jq -e .ok`:

| stdout | `jq -e .ok` exits, with jq 1.8 |
|---|---|
| `{"ok":true}` | 0 |
| `{"ok":false,…}` | 1 |
| empty, from a failure | 4 |
| an object without `ok` | 1 |
| text before the JSON | 5 |

To read a failure's errors, merge the streams and keep the last line: `just check 2>&1 | tail -n1 | jq .errors`

## Examples

Real runs in this repository. A success, the check names `--list` asks for, and a usage error, which exits 2:

```console
$ just check
{"ok":true}
$ just check --list --only lint --only typecheck
{"ok":true,"checks":["lint","typecheck"]}
```

```json
{"ok":false,"errors":["unrecognized arguments: --typo"],"help":"just check --help"}
```

A failure, after a SKILL.md quoted its `name` with single quotes. stderr replays the failing check's output, which here ends with that check's own answer, then the verdict. The exit code is 1, and the verdict is always the last line:

```console
$ just check --only frontmatter
==> frontmatter: uv run scripts/check_frontmatter.py
{"ok":false,"errors":["authoring/andy-devtools/code-review-mode/SKILL.md:2: name uses single quotes; use double quotes"]}
{"ok":false,"errors":["frontmatter failed; rerun: just check --only frontmatter"]}
```

A change, after a pasted cli block went stale. The diagnostic line names the change, then `--fix` reports it under `changes`:

```console
$ uv run scripts/check_cli_block.py
update	authoring/andy-devtools/headless/scripts/headless.py
{"ok":false,"errors":["1 pasted cli block differs from scripts/_cli.py; run: uv run scripts/check_cli_block.py --fix"]}
$ uv run scripts/check_cli_block.py --fix
{"ok":true,"changes":[["update","authoring/andy-devtools/headless/scripts/headless.py"]]}
```

## How this repository does it

- `answer()` in `scripts/_common.py` prints the line and derives `ok` from the exit code. `run_script(..., json_answer=True)` sends every outcome through it: a success, an expected failure, a usage error, a bug, and an interrupt, which answers `{"ok":false,"errors":["interrupted"]}` with exit code 130. The script's `work` function returns the data beside `ok`, usually `{}`
- Each `justfile` recipe that runs such a script carries `[no-exit-message]`, for decision 10
- A pytest or pyright warning fails `just check`: `scripts/check.py` runs pytest with `-W error` and pyright with `--warnings` (#487). When a dependency starts to warn, filter that one warning in its check, with a comment that says why

## Why

Decided on 2026-10-04, while planning #430

1. **One compact JSON line.** `{"ok":true}` costs about 5 tokens. A silent success made agents rerun `just check` 3 or 4 times in 3 sessions out of 3 (#424, #444, #482): behind a filter that condenses output, silence reads as lost output. Pascal wants the shortest answer, the same in every project
2. **The key is `ok`, and its value is the boolean `true` or `false`, never a string.** It is the shortest, the Slack API uses it, and `transcript` already does. Rejected: `success`, longer for the same meaning. Rejected: `"exit": 0`, which repeats the exit code and lies under jq, since jq treats the number 1 as true: `jq -e .exit` reports success on `{"exit":1}`
3. **`ok` agrees with the exit code.** One function builds the success object and the failure object
4. **A success goes to stdout; a failure leaves stdout empty and ends stderr, after the diagnostics.** Failures already worked this way, and the code that reported them is reused
5. **One line rather than indented JSON.** The verdict is always the last line, so `tail -n1 | jq` works. Indented JSON grows with its lists, to about 48 lines for `just check --sweep`. Pascal compared one line, indented, and one key per line, and chose the line
6. **Data only when it is the command's job**: `--list`, `--dry-run`, or `changes` for a command that changes state. The checks that ran stay visible with `-v`. A change is an array such as `["install","andy-mode"]`, which costs fewer tokens than an object
7. **A failure gives `errors`, one message per problem, each with the command that fixes it.** `help`, `retry`, or `rerun` follow only when they add something
8. **A warning is never a success.** What needs action fails the command, and the rest moves to `-v`. This covers pytest and pyright warnings too (#487). #491 makes `just merge` exit 1 when the merge landed but the deploy missed a machine, since a rerun only deploys
9. **No `--json` flag, since JSON is the default. `--help` stays text**, because it is documentation
10. **Every recipe that runs a script carries `[no-exit-message]`.** Without it, `just` prints `error: Recipe '…' failed on line N` after the object, which is then no longer the last line
11. **An agent reads the line; a script reads the exit code or `jq -e .ok`**, as [Read the answer](#read-the-answer) shows. A script never parses text, and an agent that hides the line is back to silence
12. **rtk passes the line through unchanged.** Checked on 2026-10-04 with a one-line and an indented object from a `just` recipe, on success and on failure; `rtk proxy` prints the same lines, so agents need no workaround
13. **#492 puts the lock in `test_cli_contract.py`, not in a new check**, because that test already lists every script
14. **Rejected: a sentence in `AGENTS.md` that explains the silence** (the first proposal in #430), because it fixes one script in one repository. **Rejected: text in a terminal and JSON elsewhere**, because the agent and the human would see two different outputs

## State

The rule rolls out script by script, after Pascal validates `just check` in production (#496). A script not marked "now" still follows the older output rules in [[script-conventions]]: a silent success, one change line per change, and under `--json` an indented error object without `ok`. That object stays until #490, because `scripts/sync_fleet.py` reads the installer's failures in that form

| Script | Answers in one JSON line |
|---|---|
| `just check`, `just check-frontmatter`, `scripts/check_cli_block.py`, `just api-keys-validation` | now |
| `just signoff`, `just release-check`, `just skills-discover`, `just replay-routing` | #489 |
| `just compile-skills`, `just remote-skills`, `just install-skills`, `just sync`, `scripts/sync_private.py`, `just sync-fleet`, `just merge` | #490 |
| scripts inside skills | #494 |

#492 removes this section once every script follows the rule

## Related

- [[script-conventions]]
- [[checks]]
