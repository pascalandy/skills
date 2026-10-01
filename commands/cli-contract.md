---
description: cli-contract
---

# CLI contract

Bring the CLI scripts in this project onto the contract below.

Audit every script first and decide which flags each one actually needs. Keep it lean: a flag earns its place only when the script has the matching behavior. The Baseline applies to every script; everything under Opt-in is added only where it fits.

If the project already has a CLI contract doc, shared CLI code, or contract tests, they win over this text: use their wording, their mechanisms, and their migration list. Otherwise this text is the contract.

`<name>` is a script's command name and `<NAME>` its uppercase form, such as `passgen` and `PASSGEN_DEBUG`.

## Process

1. Inventory: list every script and CLI entry point in the project (executables, wrapper scripts, `[project.scripts]` entries, files with a `__main__` block or a shebang). A project that keeps a migration list uses that list as the inventory
2. Batch the inventory into waves by language family: the language of the project's shared CLI code first, then the rest. Each wave gets its own audit and its own approval
3. Audit the wave as one summary table, one row per script: Baseline items that fail, Opt-in flags to add, and breaking changes. Add a table for a single script only where an item fails or a caller breaks. A breaking change is an exit code, a renamed flag, output moved between stdout and stderr, or a moved path
4. Stop and show me the audit. Wait for my approval
5. Implement the approved wave. Use the project's argument parser and its shared CLI code; where the project has neither, use the language's standard library. Where a script cannot meet an item without switching parser, mark the item fail, say why, and ask before switching
6. A script written in another language than the shared code meets what fits, and does not get ported to another language. Only a Parsing item its language genuinely cannot express becomes a one-line documented exception, and the audit says which language limit forces it
7. A wave is done when every approved item passes, the project's own check passes, each migrated script leaves the migration list where the project keeps one, and the report names the breaking changes with the test command and its output

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

## Tests

- Every script: each exit code it can return has a test that triggers it, including `130` through SIGINT and `143` through SIGTERM. A successful default run with no warnings writes nothing to stderr
- A script with `--verbose` or `--debug`: across default and each level it accepts, the same exit code, identical stdout, and stderr holding only what that level allows
- A script with `--json`: stdout parses as exactly one JSON object
- Tests run offline: stub every network call and every external command
- Use the project's test runner. Propose one in the audit only where the project has none
