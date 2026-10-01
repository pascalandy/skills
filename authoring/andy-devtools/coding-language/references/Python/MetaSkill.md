---
name: "python"
description: "Use when writing, running, testing, or packaging Python with uv: PEP 723 single-file scripts, uv projects, one-off tools, and ruff, pyright, and pytest checks."
---

# Python with uv

`uv` runs everything: scripts, projects, tools, and Python itself. Never call `python`, `python3`, or `pip` directly.

Everything here must work on Linux and macOS, and should work on Windows.

Needs uv 0.12 or later. Check with `uv --version`; update with `uv self update`, or `brew upgrade uv` for a Homebrew install.

## Choose the environment

Decide which environment owns the dependencies before running, checking, or changing anything. How the code runs decides it, not how many files it has:

- **Project code** belongs to an existing project, a `pyproject.toml` with a `[project]` table. It uses the project's declared dependencies, interpreter, `uv.lock`, tool configuration, and repository recipes. Run it with the repository's recipe, or `uv run path/to/file.py`
- **An independent script** runs on its own, so it declares its needs in a PEP 723 block, even when it sits inside a project. Run it with `uv run script.py`
- **A one-off tool** runs with `uvx TOOL`. Project checks use the project's declared tools instead, such as `uv run --locked ruff`

A PEP 723 block makes `uv run script.py` ignore the enclosing project's dependencies. Adding one to project code creates a second dependency owner and cuts the file off from the project's packages, so never add one to fix an import.

### When an import fails

1. Check which interpreter ran: `uv python find` for project code, `uv python find --script script.py` for a script
2. Check that the owner declares the package: `dependencies` or `[dependency-groups]` in `pyproject.toml`, or the script's block
3. Declare it with that owner only: `uv add PACKAGE` for project code, `uv add --script script.py PACKAGE` for a script

## Independent scripts

Write new standalone code as a single-file script with a PEP 723 block:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""One-line purpose.

Usage:
    uv run script.py --help
"""
```

- Run with `uv run script.py`, the one form that reads the block on every OS
- Never `uv run python script.py` on a script with a block: it ignores the block and fails on the first third-party import
- The shebang lets Linux and macOS run `./script.py` directly; Windows ignores it
- `uv init --script script.py --python 3.12` writes the block; `uv add --script script.py httpx` edits it
- Keep `dependencies = []` when the standard library is enough, which should be most of the time

Add a cooldown so a release published in the last week can't reach the script:

```python
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# [tool.uv]
# exclude-newer = "1 week"
# ///
```

- `exclude-newer` skips releases newer than the cutoff, a cheap guard against freshly compromised packages
- `uv lock --script script.py` writes `script.py.lock`; commit it when the script must resolve the same way next month
- Verify with `uv run --locked script.py`: it fails on a stale lock and leaves the lock unchanged. Plain `uv run script.py` rewrites a stale lock silently, so a committed lock alone does not enforce freshness

## Projects

Create a project when new code spans several modules or ships as a package:

```bash
uv init --package my-app && cd my-app  # app with a my-app command; swap in --lib for a library or --no-package for a bare app
uv add httpx                           # runtime dependency
uv add --dev pytest ruff pyright       # dev group in [dependency-groups]
uv run my-app                          # locks, syncs .venv, then runs
```

- `uv run` keeps `uv.lock` and `.venv` in sync; never create or activate a venv by hand
- Commit `uv.lock`; with `--locked`, `uv run` and `uv sync` fail on a stale lock instead of rewriting it
- `uv python pin 3.12` writes `.python-version`; uv downloads missing interpreters on its own
- Releases: `uv version --bump minor`, `uv build`, `uv publish`

## Tools

```bash
uvx ruff check .                  # one-off tool in a cached, isolated env (alias of `uv tool run`)
uv tool install ruff              # persistent command on PATH
uv run --with rich script.py      # extra package for this run only
uv run --env-file .env script.py  # load env vars without python-dotenv; errors if .env is missing
```

## Checks

Verify before repairing. Verification leaves source and lockfiles unchanged, so the original failures stay visible. Existing repository recipes, such as `just check`, take precedence over these commands.

For project code with a committed `uv.lock` and these tools in its dev group:

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pyright
uv run --locked pytest
```

An independent script has no project, so sync its environment and point pyright at it; otherwise every third-party import fails to resolve:

```bash
uvx ruff check script.py
uvx ruff format --check script.py
uv sync --script script.py  # add --locked when script.py.lock is committed
uvx pyright --pythonpath "$(uv python find --script script.py)" script.py
```

Sync first: until the script's environment exists, `uv python find --script` returns some other interpreter.

Repair only when asked to fix, or once verification shows findings you mean to repair, then verify again. Keep dependency updates (`uv lock`, `uv add`) a separate step:

```bash
uv run --locked ruff check --fix .
uv run --locked ruff format .
```

- Type-hint every function signature; pyright does not require annotations, but `ruff check --extend-select ANN` flags missing ones
- `uv audit` (experimental) scans locked dependencies for known vulnerabilities
- Before changing ruff settings, read [ruff.md → Configuration](references/ruff.md#configuration)
- When a checker fails, read [ruff.md → Exit codes](references/ruff.md#exit-codes) or [pyright.md → Exit codes](references/pyright.md#exit-codes) to tell a code finding from a broken setup
- Before silencing a diagnostic, read [pyright.md → Suppressing errors](references/pyright.md#suppressing-errors)

## Cross-platform

- Build paths with `pathlib.Path`, never by joining strings with `/`
- Pass `encoding="utf-8"` to `open`, `read_text`, and `write_text`; Windows does not default to UTF-8
- Give `subprocess` a list of arguments, never `shell=True`; locate executables with `shutil.which`

## Script conventions

Agents run these scripts, so keep output small and failures obvious:

- Standard library first (`argparse`, `logging`, `pathlib`, `json`, `subprocess`); add a dependency only when it earns its place
- When one does: `httpx` for HTTP, `pydantic-settings` for typed config, `polars` or `duckdb` for data
- `-h, --help` prints usage with examples and changes nothing
- Quiet by default: one line on stdout on success
- `-v, --verbose` adds per-item detail and tracebacks on stderr
- `--dry-run` for anything that writes or deletes
- Failures print `error: <what went wrong and how to fix it>` on stderr, then `rerun with --verbose for details`
- Build incrementally: write `--help` first and run it, then add one feature at a time and run again

| Code | Meaning              |
| ---- | -------------------- |
| 0    | Success              |
| 1    | Runtime failure      |
| 2    | Bad usage            |
| 130  | Interrupted (Ctrl+C) |

## Tests

Keep tests in `scripts/tests/` next to the script. Test CLI behavior through the command line, the way agents run it, and internal computations directly when a subprocess adds nothing.

- Before writing or changing tests, read [pytest.md → Test structure](references/pytest.md#test-structure) for the subprocess helper
- Then read [pytest.md → Proving behavior](references/pytest.md#proving-behavior) for what each test must assert
- Run them with `uv run --locked pytest` for project code, or `uvx --with-requirements scripts/tool.py pytest -o pythonpath=scripts scripts/tests` for an independent script

## Secrets

- Read secrets from environment variables and fail at startup when one is missing
- Keep local values in a git-ignored `.env` and load it with `uv run --env-file .env` for local runs; the flag errors when the file is missing, so keep it out of CI and shared recipes
- Never print, log, or hardcode them
