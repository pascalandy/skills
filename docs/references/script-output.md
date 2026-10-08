---
name: Script output
description: The output rule: what a script answers in one JSON line, its keys, how agents and scripts read it, and why each choice was made
tags:
  - area/ea
  - kind/doc
  - topic/scripts
  - status/stable
date_created: 2026-10-04
date_updated: 2026-10-07
---

A script answers in one line of JSON, so an agent or another script knows the outcome from one read. The rule needs no Python, so a project in Bash or TypeScript can apply it as written.

## The rule

This section is the normative definition. Other pages and skills link here instead of restating it

- Everything passed: `{"ok":true}` on stdout, exit code 0
- Anything else: stdout stays empty, the last line of stderr is `{"ok":false,"errors":["…"]}`, on a line of its own after any diagnostic, and the exit code is not 0. Each error says what failed and the command that fixes it
- `ok` always agrees with the exit code
- A success with a warning is not a success: what needs action fails the command, and the rest moves to `-v`
- `--help` and `--version` are documentation and stay text on stdout, exit 0 (decision 9)

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

Read the answer as a JSON object: key order carries no meaning, so a reader never matches a prefix such as `{"ok":`. `answer_in()` and `changes_in()` in `scripts/_common.py` read it that way

Behind rtk, a long answer is cut and ends with `[full output: rtk recall ID]`. Run that recall, or rerun the command as `rtk proxy <command>`, to read the whole line (decision 12)

## Keys

Every answer uses only these keys beside a command's own data, so a caller never guesses what a key means:

| Key | When | Holds |
|---|---|---|
| `ok` | always | `true` exactly when the exit code is 0 |
| `errors` | a failure | one message per problem, each ending with the command that fixes it |
| `help` | a usage error, exit 2 | `<name> --help` |
| `retry` | a temporary failure, exit 75 | the same command, safe to run again as is |
| `rerun` | an unexpected error | the same command with `--debug` |
| `changes` | a command that changes state, on success, dry run, `--check`, or a failure, interrupt, or bug after a change landed | one array per change, `[action, object]` with an optional detail |
| `file`, `files` | a command whose job is content, on success or failure | the path it wrote, or a list of what it wrote: paths, or objects with a `path` and the command's details, as `image-creator` answers |

Any other key is the data the command exists to return, such as `checks` for `just check --list` (decision 6). A new key that means the same as one above reuses that name

In a failed apply, `changes` and `files` hold what already happened. Each command keeps them on the failures it expects. `just sync`, `just install-skills`, `just merge`, `just sync-fleet`, and `scripts/sync_private.py` keep them on an interrupt or a bug too, as do the skill scripts that write files or packages: mermaid's `render_examples.py`, image-creator, and the corey-mode and matt-mode updaters. Each records an effect as it lands: a pull before any other git call, a replaced skill before its old copy is deleted, a private commit once HEAD moves, even when the stop lands during `git commit`, and a step's answer even when the step then dies from a signal. What stays outside: a child stopped while it runs, such as the private sync and the installer under `just sync`, the deploy under `just merge`, or a machine's steps under `just sync-fleet`, loses what it had done, even what it had already answered, since the parent discards a stopped child's output; a fast-forward stopped mid-run goes unrecorded; and a readback right after an effect, such as `just merge` reading the PR it merged or the private sync reading HEAD after its pull, can fail before the effect is recorded. In a preview, `--dry-run` or `--check`, `changes` holds what an apply would do

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

- `answer()` prints the line and derives `ok` from the exit code. `run_script()` sends every outcome through it. Both live in the cli block of `scripts/_cli.py`, so a skill script that pastes the block answers the same way: a success, an expected failure, a usage error, a bug, and an interrupt, which answers `{"ok":false,"errors":["interrupted"]}` with exit code 130. The script's `work` function returns the data beside `ok`, usually `{}`
- A command that changes state appends each change as it lands, inside `receipt()` from `scripts/_common.py`, so a failure, an interrupt, or a bug still answers it. `run_script()` answers the `report` any exception carries
- A command that replays a child's output goes through `replay()` from `scripts/_common.py`, which ends the child's last line, so the answer stays the last line
- Each `justfile` recipe that runs such a script carries `[no-exit-message]`, for decision 10
- The lock, decision 13: `scripts/tests/test_cli_contract.py` fails when a script in `scripts/` writes to stdout anywhere but in `answer()`, logs a warning, or answers a usage error in another form, and `scripts/tests/test_justfile.py` fails when a recipe that runs one lacks `[no-exit-message]`. pyright checks that `work` returns a dict
- A pytest or pyright warning fails `just check`: `scripts/check.py` runs pytest with `-W error` and pyright with `--warnings` (#487). When a dependency starts to warn, filter that one warning in its check, with a comment that says why

## Why

Decided on 2026-10-04, while planning #430

1. **One compact JSON line.** `{"ok":true}` costs about 5 tokens. A silent success made agents rerun `just check` 3 or 4 times in 3 sessions out of 3 (#424, #444, #482): behind a filter that condenses output, silence reads as lost output. Pascal wants the shortest answer, the same in every project
2. **The key is `ok`, and its value is the boolean `true` or `false`, never a string.** It is the shortest, the Slack API uses it, and `transcript` already does. Rejected: `success`, longer for the same meaning. Rejected: `"exit": 0`, which repeats the exit code and lies under jq, since jq treats the number 1 as true: `jq -e .exit` reports success on `{"exit":1}`
3. **`ok` agrees with the exit code.** One function builds the success object and the failure object
4. **A success goes to stdout; a failure leaves stdout empty and ends stderr, after the diagnostics.** Failures already worked this way, and the code that reported them is reused
5. **One line rather than indented JSON.** The verdict is always the last line, so `tail -n1 | jq` works. Indented JSON grows with its lists, to about 48 lines for `just check --sweep`. Pascal compared one line, indented, and one key per line, and chose the line
6. **Data only when it is the command's job**: `--list`, `--dry-run`, or `changes` for a command that changes state. The checks that ran stay visible with `-v`. A change is an array such as `["install","andy-mode"]`, which costs fewer tokens than an object
7. **A failure gives `errors`, one message per problem, each with the command that fixes it.** `help`, `retry`, or `rerun` follow only when they add something. A failure also keeps the data a caller needs to recover: the `changes` that already happened, such as a merge that landed before its deploy failed, or the `files` a run wrote before it failed. An interrupt or a bug keeps them too
8. **A warning is never a success.** What needs action fails the command, and the rest moves to `-v`. This covers pytest and pyright warnings too (#487). `just merge` exits 1 when the merge landed but the deploy missed a machine, since a rerun only deploys (#491)
9. **No `--json` flag, since JSON is the default. `--help` and `--version` stay text**, because they are documentation. `--version` prints one line, `<name> <version>`, the form tools read by convention. Pascal confirmed `--version` on 2026-10-07
10. **Every recipe that runs a script carries `[no-exit-message]`.** Without it, `just` prints `error: Recipe '…' failed on line N` after the object, which is then no longer the last line
11. **An agent reads the line; a script reads the exit code or `jq -e .ok`**, as [Read the answer](#read-the-answer) shows. A script never parses text, and an agent that hides the line is back to silence
12. **rtk passes a short line through unchanged, and cuts a long one.** Checked on 2026-10-04 with short answers, on success and on failure. On 2026-10-07, rtk 0.49.0 cut the 714-byte answer of `rtk just check --list` to about 150 characters and added `[full output: rtk recall ID]`; [Read the answer](#read-the-answer) says how to recover the line. A script reads the exit code or `jq`, never rtk's output
13. **The lock lives in `test_cli_contract.py`, not in a new check** (#492), because that test already lists every script
14. **Rejected: a sentence in `AGENTS.md` that explains the silence** (the first proposal in #430), because it fixes one script in one repository. **Rejected: text in a terminal and JSON elsewhere**, because the agent and the human would see two different outputs
15. **A script whose job is content writes the content to a file and answers with its path**, such as `{"ok":true,"file":"…"}`, so the line stays one line an agent reads whole. A script that streams events, such as a watcher, writes them to stderr and ends with its answer on stdout. Pascal decided on 2026-10-06 that skill scripts follow the rule too, these included (#494)

## Related

- [[script-conventions]]
- [[checks]]
