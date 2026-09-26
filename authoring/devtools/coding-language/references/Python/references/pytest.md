# Pytest - Python Test Framework

Modern, feature-rich testing framework for Python. Industry standard for Python testing.

## Why Pytest

- **Simple syntax**: Plain `assert` statements (no `self.assertEqual`)
- **Auto-discovery**: Finds tests automatically
- **Rich ecosystem**: Thousands of plugins available
- **Detailed output**: Clear failure messages with context
- **Fixtures**: Powerful dependency injection for test setup

## Core Commands

```bash
# Run all tests
uv run pytest

# Run specific file
uv run pytest path/to/test_file.py

# Run specific test class
uv run pytest path/to/test_file.py::TestClass

# Run specific test function
uv run pytest path/to/test_file.py::TestClass::test_method

# Verbose output
uv run pytest -v

# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Run last failed tests
uv run pytest --lf
```

## Test Discovery

Pytest automatically finds tests matching these patterns:

- Files: `test_*.py` or `*_test.py`
- Classes: `Test*`
- Functions: `test_*`

## Test Structure

```python
# test_example.py
import subprocess
from pathlib import Path

# Helper function (run once per file), same as in MetaSkill.md
SCRIPT = Path(__file__).parent.parent / "script.py"


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


# Test class (groups related tests)
class TestVersion:
    """Test --version flag."""

    def test_version_flag(self) -> None:
        """--version should output version and exit with 0."""
        result = run("--version")
        assert result.returncode == 0
        assert "version" in result.stdout.lower()

    def test_version_short_flag(self) -> None:
        """-V should be equivalent to --version."""
        result = run("-V")
        assert result.returncode == 0
        assert "version" in result.stdout.lower()
```

## Assertions

```python
# Basic assertions
assert value == expected
assert value != unexpected
assert value in collection
assert value is None
assert value is not None

# String assertions
assert "substring" in text
assert text.startswith("prefix")
assert text.endswith("suffix")

# Numeric assertions
assert count > 0
assert 0 <= percentage <= 100

# Exception assertions
import pytest
with pytest.raises(ValueError):
    function_that_should_raise()

with pytest.raises(ValueError, match="specific message"):
    function_that_should_raise()
```

## Exit Code Testing Pattern

```python
class TestExitCodes:
    """Test exit code standards."""

    def test_success_returns_zero(self) -> None:
        """Successful execution returns 0."""
        assert run("--help").returncode == 0

    def test_validation_error_returns_two(self) -> None:
        """Validation errors return 2."""
        assert run("--invalid-flag").returncode == 2

    def test_runtime_error_returns_one(self) -> None:
        """Runtime errors return 1."""
        assert run("--api-call").returncode == 1
```

## Fixtures

Fixtures provide reusable setup/teardown:

```python
import pytest
import tempfile
from collections.abc import Iterator
from pathlib import Path

@pytest.fixture
def temp_file() -> Iterator[Path]:
    """Create temporary file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        temp_path = Path(f.name)

    yield temp_path  # Test runs here

    # Cleanup after test
    temp_path.unlink(missing_ok=True)

def test_file_processing(temp_file: Path) -> None:
    """Test processes file correctly."""
    temp_file.write_text("test content", encoding="utf-8")
    assert run("--input", str(temp_file)).returncode == 0
```

## Parametrized Tests

Run same test with different inputs:

```python
import pytest

@pytest.mark.parametrize("size,expected", [
    ("1024x1024", 0),
    ("512x512", 0),
    ("invalid", 2),
])
def test_size_validation(size: str, expected: int) -> None:
    """Test size parameter validation."""
    assert run("--size", size).returncode == expected
```

## Configuration

Located in `pyproject.toml`:

Substitute the actual project-relative test path; TOML does not expand `<skill_dir>` placeholders.

```toml
[tool.pytest.ini_options]
testpaths = [
    "scripts/tests",  # Example when pyproject.toml lives at the skill root
]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

Options:

- `testpaths` - Directories to search for tests
- `python_files` - Test file patterns
- `python_functions` - Test function patterns
- `addopts` - Default command-line options
  - `-v` - Verbose output
  - `--tb=short` - Shorter traceback format
  - `-x` - Stop on first failure
  - `--lf` - Run last failed tests

## Output Interpretation

```bash
# Success
test_example.py::TestVersion::test_version_flag PASSED

# Failure
test_example.py::TestVersion::test_version_flag FAILED
>       assert code == 0
E       assert 1 == 0

# Summary
===== 5 passed, 1 failed in 0.50s =====
```

## Common Patterns

### Testing Environment Variables

`run()` passes `env` to the subprocess; copy `os.environ` so `PATH` still finds `uv`:

```python
import os

def test_missing_api_key() -> None:
    """Script fails gracefully without API key."""
    env = os.environ.copy()
    env.pop("API_KEY", None)
    result = run(env=env)
    assert result.returncode == 1
    assert "API_KEY" in result.stderr
```

### Testing File Operations

```python
import tempfile
from pathlib import Path

def test_output_file() -> None:
    """Script creates output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output = Path(tmpdir) / "output.txt"
        assert run("--output", str(output)).returncode == 0
        assert output.exists()
        assert output.read_text(encoding="utf-8") == "expected content"
```

## Test Organization

```
my-skill/
├── SKILL.md
└── scripts/
    ├── my_script.py
    └── tests/
        ├── test_my_script.py
        ├── TEST_PLAN.md       # Optional: planned tests
        └── README.md          # Optional: test documentation
```

## Best Practices

1. **One assertion per test** - Makes failures clear
2. **Descriptive test names** - `test_invalid_size_returns_error`
3. **Use classes to group** - `TestVersion`, `TestValidation`
4. **Test exit codes** - Verify success (0) and error codes (1, 2)
5. **Test error messages** - Ensure helpful error output
6. **Use fixtures for setup** - Avoid repetitive setup code
7. **Clean up resources** - Use fixtures or try/finally

## Common Issues

### Tests Not Found

- Check file naming: `test_*.py`
- Check function naming: `test_*`
- Verify `testpaths` in `pyproject.toml`

### Import Errors

- Ensure script dependencies are installed
- Check `SCRIPT` points to correct file
- Verify running from correct directory

### Assertion Failures

- Use `-v` for verbose output
- Use `-s` to see print statements
- Check actual vs expected values in output

## Resources

- Docs: https://docs.pytest.org/
- Fixtures: https://docs.pytest.org/en/stable/fixture.html
- Parametrize: https://docs.pytest.org/en/stable/parametrize.html
- Plugins: https://docs.pytest.org/en/stable/plugins.html
