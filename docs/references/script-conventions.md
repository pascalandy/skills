---
name: Script conventions
description: The CLI contract for scripts/ and skill-local scripts, and the shared code and tests that enforce it
tags:
  - area/ea
  - kind/doc
  - topic/scripts
  - status/stable
date_created: 2026-09-26
date_updated: 2026-10-01
---

Every CLI in `scripts/` follows this contract. A skill-local script may follow it too, and its skill's own tests cover it

`<name>` is the command a user types: `just <recipe>` for a `scripts/` tool, its path such as `scripts/sync_private.py` when no recipe runs it, and a skill script's current program name, otherwise its file name. `<NAME>_DEBUG` comes from the file stem, such as `SYNC_FLEET_DEBUG`

## Baseline

Every script meets all of these. No exception waives an exit code, the Rule of Silence, or help behavior.

Output follows the Rule of Silence: when nothing needs saying, print nothing

- stdout holds the primary result only: data, IDs, paths, or change lines. No banners or status lines
- A failure leaves stdout empty. Under `--json`, the error is one JSON object on stderr
- stderr holds every diagnostic. By default, only errors and warnings that need action
- Without a terminal, or with `NO_COLOR` set or `TERM=dumb`: no color, spinners, or progress bars

Exit codes, all listed in `--help`:

- `0` success, including a no-op; `1` runtime failure; `2` usage error: an unknown flag, or a missing, invalid, or out-of-range argument
- `130` on SIGINT and `143` on SIGTERM, without a stack trace; a repeated signal is ignored while cleanup finishes
- `124`–`127`, and every code from `128` up except `130` and `143`, stay reserved for the shell and OS

Help and errors:

- `-h`, `--help`: help on stdout, exit 0, with 2–5 examples. It wins over every other argument before `--`, including unknown flags
- A usage error prints short usage, the error, and `run '<name> --help'` on stderr, then exits 2
- An error says what failed, then the exact command that fixes it. Stack traces appear only with `--debug`

Parsing:

- `--opt value` equals `--opt=value`; `-vn` equals `-v -n`; `--` ends option parsing
- Long options need their full name; argparse abbreviation is off
- Every short flag has a long form. `-v` means verbose, never version
- A boolean flag that defaults to on gets a `--no-<flag>` form
- Secrets arrive through `--<x>-file`, stdin, or an environment variable, never as a flag value

Documentation:

- Flags and defaults are documented once, in the argument parser
- Other docs say "run `<name> --help`" instead of copying flag lists, and keep only what code cannot say: why, where, and dependencies
- A doc line that runs a script may use only flags that script accepts; a test checks every such line in docs, hooks, and CI

## Opt-in

Add a row's flags only when the script has the matching behavior.

| When the script... | Add |
|---|---|
| is installed as a command or has a release version | `--version`: one line on stdout, `<name> <version>` |
| has steps worth reporting | `-v`, `--verbose`: progress and step details on stderr |
| has failures worth diagnosing: network, locks, or subprocesses | `--debug`, also `<NAME>_DEBUG=1`: internals, timings, and stack traces on stderr |
| has output read by programs or agents | `--json`: stdout is one JSON object and nothing else |
| emits color | `--no-color` |
| changes state | `-n`, `--dry-run`: preview in the same format as a real run |
| asks for confirmation | `-y`, `--yes`; `--no-input`: never prompt, and a missing value exits 2 naming the flag |
| has a safety check worth overriding | `-f`, `--force`, separate from `--yes` |
| calls networks or APIs, or takes locks | exit `75` for a temporary, safe-to-retry failure; `--timeout <duration>` with a default |
| reads or writes files | `-` as a filename for stdin or stdout; `-o`, `--output <file>` |
| has subcommands | `<name> help <cmd>`, `<name> <cmd> --help`, and `<name> <cmd> -h` print the same text; global flags work before and after the subcommand; an unknown subcommand exits 2 and suggests the closest match; subcommands need their full name |
| has line-oriented output | `--plain`: tab-separated, no color |
| has several output formats | `--format <fmt>` in place of `--json` |
| reads config files | `-c`, `--config <path>`; precedence: flag, env, project, `~/.config/<name>/`, system |
| has named environments | `--profile <name>` |
| shows progress bars | `--no-progress` |
| walks directories | `-r`, `--recursive` |
| lists filtered items | `-a`, `--all`; `--limit <n>` |

`-v` and `--debug` only add to stderr: stdout and the exit code stay identical at every level. Tiny validators get no `--debug` and never print a stack trace

A dry run changes nothing a user owns, such as a checkout or installed skills. It may write a preview file in the tool's own state folder and refresh caches

A command that changes state prints one change line per change, `<action>\t<object>`, with an optional third tab-separated detail. A real run and its dry run print the same lines; a no-op prints nothing. `--check` is a dry run that exits 1 when a change is pending, with the change lines on stderr. Hooks stay silent

Decide at the failing boundary whether a failure is temporary. A network error from git, a timeout, or a held lock exits 75; bad credentials or configuration exit 1. A paid request that may have completed is never reported as safe to retry. A script that runs several steps exits 75 only when every failure was temporary

A duration is `30s`, `5m`, `2h`, or bare seconds

## Exceptions

Opt-in flags that would give no real choice are left out, and a script outside the shared block's language drops only a Parsing item its language cannot express. Each exception gets one line:

- `scripts/` tools have no `--version`: they ship with the checkout, not as versioned commands
- Change lines are already tab-separated and colorless, so no `scripts/` tool has `--plain`
- `just check-frontmatter`, `just compile-skills`, `just remote-skills`: no `-r`; each walks one fixed tree
- `just compile-skills`, `just install-skills`, `just remote-skills`: no `-o` or `-`; they write fixed paths: `skills/`, the agent directories, and the skill tables
- `just install-skills`: no `--force`; it would delete entries the installer does not own
- `just install-skills`: accepts a hidden `-q/--quiet` and ignores it, because a `just sync` or `just sync-fleet` started before this contract passes it; remove it once every machine has synced
- `just release-check`: `--notes FILE` names what `-o` would write; `--notes -` writes to stdout
- `just sync-fleet`: no `-c/--config`; `--fleet PATH` is the one registry
- `scripts/check_cli_block.py`: no `-n/--dry-run`; it changes nothing without `--fix`
- `watch-pr` in `poteto-mode` streams JSON Lines by default, with `--pretty` for people; the one-object rule applies to `--status-only`
- `transcript`: no `-o` or `-`; a run writes a folder of several files, named by `--output-dir`
- `transcript`: no `--plain`; `list` already prints one item per line, tab-separated and colorless
- `transcript`: `--profile` names an inference profile, a provider, model, and effort, not an environment
- `transcript`: a JSON error keeps `{"ok": false, "error": {"code", "message", "hint"}}`, which its agents and `verify-transcript` read, instead of the shared `errors` list; `hint` is the command that fixes it

## Shared code

`scripts/_cli.py` holds the contract pieces: the parser, the help pre-scan, signal handling, `<NAME>_DEBUG`, color detection, the duration parser, the exit-code table, and `ScriptError` (1), `UsageError` (2), and `TemporaryError` (75). Everything below its `cli-block` marker is the block a skill script pastes whole; `just check --only cli-block` fails when a copy differs, and `uv run scripts/check_cli_block.py --fix` rewrites the copies. Keep the block on the standard library and Python 3.10

`scripts/_common.py` builds the `scripts/` entry point on it. Build a `Parser` with the script's `exit_codes(...)` table, then return `run_script(parser, work, argv, debug="<NAME>_DEBUG")` from `main()`. `work` returns what stdout holds, or "" to stay silent, and raises one of the error classes with one message per problem. `run_script` adds `-v` and `--debug`, prints output only on success, and turns each outcome into its exit code. Run each child through `_common.run()`: on a timeout or an interrupt it sends SIGTERM, so the child can clean up, and SIGKILL 10 seconds later. Functions other scripts import print nothing and install no signal handlers

Use only the standard library unless a dependency earns its place. Each `justfile` recipe is one line that forwards its arguments (`recipe *args`, passed as `"$@"`) to one script or tool through `uv run --quiet`; branching and chaining belong in the script. Bare `just` lists recipes in file order: the `commands` group, most-run first, then the `checks` group; hook-only recipes are `[private]`. `scripts/tests/test_justfile.py` enforces it

## Tests

Repository test modules live in `scripts/tests/` as `test_<stem>.py`. Each module has one `test-<stem>` check in `scripts/check.py`, with underscores in the stem written as hyphens in the check name. The registry must cover every module. A skill's tests live inside its `authoring/` package and run when that package changes. [[checks]] explains root test selection, batching, and reruns

`test_cli.py` and `test_common.py` test the shared contract code once. `test_cli_contract.py` fails on a `scripts/` entry point missing from its `ENTRIES`, and runs each script's `--help` once: the help must come from the shared parser, and every doc line that runs the script, in docs, hooks, CI, and `scripts/`, may use only flags the help lists. A script's own tests cover what it does, not the shared contract again

## Related

- [[checks]]
- [[release]]
