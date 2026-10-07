# Pytest - Python Test Framework

Test runner for Python: plain `assert` statements, automatic discovery, and fixtures for setup.

Run tests in the environment that owns the code, as [MetaSkill.md → Choose the environment](../MetaSkill.md#choose-the-environment) explains: `uv run --locked pytest` for project code, and the command in [Direct Tests](#direct-tests) for an independent script.

## Core Commands

```bash
uv run --locked pytest                                # all tests
uv run --locked pytest path/to/test_file.py           # one file
uv run --locked pytest path/to/test_file.py::test_fn  # one test
uv run --locked pytest -x                             # stop on first failure
uv run --locked pytest --lf                           # rerun last failures
uv run --locked pytest -v -s                          # verbose, show print output
```

## Test Discovery

Pytest automatically finds tests matching these patterns:

- Files: `test_*.py` or `*_test.py`
- Classes: `Test*`
- Functions: `test_*`

## Test Structure

Test CLI behavior through a subprocess, the way agents run the script. This is the helper to copy; every example below uses it:

```python
# scripts/tests/test_tool.py
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "tool.py"
TIMEOUT = 60  # seconds; the first run may install the script's dependencies


def run(
    *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", str(SCRIPT), *args],
        check=False,  # tests assert on returncode themselves
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        timeout=TIMEOUT,
    )
```

A hung child raises `subprocess.TimeoutExpired` after `TIMEOUT`, which fails the test instead of stalling the run. Size `TIMEOUT` to the command.

## Proving Behavior

Each test proves one observable behavior with a literal expected value. An exit code alone, or a passing `--help`, does not prove the script did its work.

The examples test a `tool.py` that writes an input file uppercased to `--output FILE` and answers in one JSON line, as [script-output](https://github.com/pascalandy/skills/blob/main/docs/references/script-output.md) defines. Assert all of it: the content file, the answer, an empty stdout on failure, the last line of stderr, and the exit code. This helper reads the answer wherever it went:

```python
import json


def answer(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    """The one-line answer: stdout on success, else the last line of stderr."""
    if result.returncode == 0:
        assert result.stdout.count("\n") == 1, result.stdout
        return json.loads(result.stdout)
    assert result.stdout == ""
    return json.loads(result.stderr.splitlines()[-1])
```

### Processing Input

```python
def test_uppercases_input_file(tmp_path: Path) -> None:
    source = tmp_path / "in.txt"
    source.write_text("hello\n", encoding="utf-8")
    output = tmp_path / "out.txt"
    result = run(str(source), "--output", str(output))
    assert result.returncode == 0
    assert answer(result) == {"ok": True, "file": str(output)}
    assert output.read_text(encoding="utf-8") == "HELLO\n"
```

A script that exits 0 without reading the file fails the content assertion.

### Runtime Failure

```python
def test_missing_input_reports_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.txt"
    result = run(str(missing), "--output", str(tmp_path / "out.txt"))
    assert result.returncode == 1
    assert answer(result)["errors"] == [f"input file not found: {missing}"]
```

The arguments are valid, and the test expects exit 1 with a specific error, so a usage error (exit 2) cannot satisfy it.

### Usage Errors

```python
def test_unknown_flag_is_usage_error() -> None:
    result = run("--no-such-flag")
    assert result.returncode == 2
    assert answer(result)["help"] == "tool.py --help"
```

### Environment Variables

For a script that reads `API_KEY` at startup, copy `os.environ` so `PATH` still finds `uv`, then remove the variable:

```python
import os


def test_missing_api_key_reports_error(tmp_path: Path) -> None:
    source = tmp_path / "in.txt"
    source.write_text("hello\n", encoding="utf-8")
    env = os.environ.copy()
    env.pop("API_KEY", None)
    result = run(str(source), "--output", str(tmp_path / "out.txt"), env=env)
    assert result.returncode == 1
    assert answer(result)["errors"] == ["API_KEY is not set; export it, then rerun"]
```

## Fixtures

Use the built-in `tmp_path` for files; pytest creates a fresh directory per test. Build shared setup on top of it:

```python
import pytest


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "in.txt"
    path.write_text("hello\n", encoding="utf-8")
    return path


def test_uppercases_fixture_file(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "out.txt"
    assert answer(run(str(source), "--output", str(output)))["ok"] is True
    assert output.read_text(encoding="utf-8") == "HELLO\n"
```

## Parametrized Tests

```python
@pytest.mark.parametrize(
    ("text", "expected"),
    [("hello\n", "HELLO\n"), ("Mixed Case\n", "MIXED CASE\n")],
)
def test_uppercases_text(tmp_path: Path, text: str, expected: str) -> None:
    source = tmp_path / "in.txt"
    source.write_text(text, encoding="utf-8")
    output = tmp_path / "out.txt"
    run(str(source), "--output", str(output))
    assert output.read_text(encoding="utf-8") == expected
```

## Direct Tests

Test an internal computation directly when a subprocess adds nothing. The script's `main()` must sit behind `if __name__ == "__main__":` so importing it runs nothing:

```python
# scripts/tests/test_shout.py
from tool import shout


def test_shout_uppercases() -> None:
    assert shout("hello") == "HELLO"
```

- For expected exceptions: `with pytest.raises(ValueError, match="literal message"):`
- Put the script's directory on `pythonpath` so `import tool` resolves: `pythonpath = ["scripts"]` in the configuration below, or `-o pythonpath=scripts` on the command line
- Direct tests run in pytest's environment, not the script's. For an independent script with dependencies, run `uvx --with-requirements scripts/tool.py pytest -o pythonpath=scripts scripts/tests`

## Configuration

In `pyproject.toml`, with paths relative to it:

```toml
[tool.pytest.ini_options]
testpaths = ["scripts/tests"]
pythonpath = ["scripts"]  # lets direct tests import the script
addopts = "-v --tb=short"
```

- `testpaths` - Directories to search for tests
- `pythonpath` - Directories added to `sys.path`
- `addopts` - Default command-line options

## Output Interpretation

```bash
# Success
scripts/tests/test_tool.py::test_uppercases_input_file PASSED

# Failure
scripts/tests/test_tool.py::test_uppercases_input_file FAILED
>       assert output.read_text(encoding="utf-8") == "HELLO\n"
E       AssertionError: assert '' == 'HELLO\n'

# Summary
===== 5 passed, 1 failed in 0.50s =====
```

## Test Organization

```
my-skill/
├── SKILL.md
└── scripts/
    ├── tool.py
    └── tests/
        └── test_tool.py
```

## Best Practices

1. **One observable behavior per test** - Name it: `test_missing_input_reports_error`
2. **Assert literal output** - Compare written files, the JSON answer, an empty stdout on failure, and the last line of stderr with exact expected values
3. **Make failures deterministic** - Trigger runtime errors with valid arguments, such as a missing file under `tmp_path`
4. **Bound every subprocess** - Keep the helper's `timeout`
5. **Subprocess for CLI, direct for internals** - Import a function when a subprocess adds nothing
6. **Use `tmp_path`** - A fresh directory per test, no cleanup code

## Common Issues

### Tests Not Found

- Check file naming: `test_*.py`
- Check function naming: `test_*`
- Verify `testpaths` in `pyproject.toml`

### Import Errors

- In the test: check that `SCRIPT` points to the script and that `pythonpath` covers direct imports
- In the script: follow [MetaSkill.md → When an import fails](../MetaSkill.md#when-an-import-fails)

### Assertion Failures

- Use `-v` for verbose output
- Use `-s` to see print statements
- Compare the literal expected value with the written file and the answer from `answer(result)`

## Resources

- Docs: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Parametrize: https://docs.pytest.org/en/stable/parametrize.html
- Plugins: https://docs.pytest.org/en/stable/plugins.html
