---
name: "python"
description: "Use when writing, running, testing, or packaging Python with uv: PEP 723 single-file scripts, uv projects, one-off tools, and ruff, pyright, and pytest checks."
---

# Python with uv

`uv` runs everything: scripts, projects, tools, and Python itself. Never call `python`, `python3`, or `pip` directly.

Everything here must work on Linux and macOS, and should work on Windows.

Needs uv 0.12 or later. Check with `uv --version`; update with `uv self update`, or `brew upgrade uv` for a Homebrew install.

## Scripts (default)

Start with a single-file script that declares its needs in a PEP 723 block:

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
- `uv lock --script script.py` writes `script.py.lock`, which `uv run` then follows; commit it when the script must resolve the same way next month

## Projects

Move to a project when the code spans several modules or ships as a package:

```bash
uv init --package my-app && cd my-app  # app with a my-app command; swap in --lib for a library or --no-package for a bare app
uv add httpx                           # runtime dependency
uv add --dev pytest ruff pyright       # dev group in [dependency-groups]
uv run my-app                          # locks, syncs .venv, then runs
```

- `uv run` keeps `uv.lock` and `.venv` in sync; never create or activate a venv by hand
- Commit `uv.lock`; in CI, `uv sync --locked` fails when it is stale
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

Run from the project root so the project's pinned versions apply:

```bash
uv run ruff check --fix .
uv run ruff format .
uv run pyright
uv run pytest
```

A standalone script has no project, so point pyright at the script's own environment; otherwise every third-party import fails to resolve:

```bash
uvx ruff check script.py
uv sync --script script.py
uvx pyright --pythonpath "$(uv python find --script script.py)" script.py
```

- Type-hint every function signature; pyright does not require annotations, but `ruff check --extend-select ANN` flags missing ones
- `uv audit` (experimental) scans locked dependencies for known vulnerabilities
- Details: `references/ruff.md`, `references/pyright.md`, `references/pytest.md`

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

Keep tests next to the script and run it as a subprocess, the way agents do:

```
scripts/
├── tool.py
└── tests/
    └── test_tool.py
```

```python
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "tool.py"


def run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def test_help_exits_zero() -> None:
    assert run("--help").returncode == 0
```

Run with `uv run pytest` inside a project, or `uvx pytest scripts/tests` for a standalone script. See `references/pytest.md` for fixtures and patterns.

## Secrets

- Read secrets from environment variables and fail at startup when one is missing
- Keep local values in a git-ignored `.env` and load it with `uv run --env-file .env` for local runs; the flag errors when the file is missing, so keep it out of CI and shared recipes
- Never print, log, or hardcode them
