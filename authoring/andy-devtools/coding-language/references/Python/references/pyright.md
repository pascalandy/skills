# Pyright - Python Static Type Checker

Static type checker for Python. Catches type errors before runtime.

Run it in the environment that owns the code: `uv run --locked pyright` for project code; for an independent script, follow [MetaSkill.md → Checks](../MetaSkill.md#checks).

## Core Commands

```bash
uv run --locked pyright                  # check the configured files
uv run --locked pyright path/to/file.py  # check one file
uv run --locked pyright --stats          # timing and file counts
uv run --locked pyright --watch          # recheck on every change
```

## Type Checking Modes

Set in `pyproject.toml`:

```toml
[tool.pyright]
typeCheckingMode = "basic"  # or "standard" or "strict"
```

- **basic**: Minimal type checking (recommended for most projects)
- **standard**: Moderate type checking (catches more issues)
- **strict**: Maximum type checking (requires extensive type annotations)

## Configuration

Starter configuration in `pyproject.toml`. It keeps every diagnostic at its default, so an unresolved import still fails the check:

```toml
[tool.pyright]
typeCheckingMode = "basic"

include = [
    "src",
    "tests",
]

exclude = [
    "**/__pycache__",
    "**/.venv",
    "**/node_modules",
]
```

Pyright takes the Python version from the environment's interpreter.

## Common Error Types

### Import Errors

```
error: Import "requests" could not be resolved (reportMissingImports)
```

**Cause**: The package is missing from the environment pyright checks, or pyright is checking the wrong environment
**Fix**: Follow [MetaSkill.md → When an import fails](../MetaSkill.md#when-an-import-fails). Never silence `reportMissingImports`; that hides real failures

### Type Mismatch

```
ERROR: Argument of type "str" cannot be assigned to parameter "x" of type "int"
```

**Cause**: Passing wrong type to function
**Fix**: Convert type or update type hints

### Attribute Access

```
WARNING: "error" is not a known attribute of module "urllib"
```

**Cause**: Missing import or incorrect attribute access
**Fix**: Import correct submodule (e.g., `urllib.error`)

### Optional Member Access

```
ERROR: "read" is not a known attribute of "None"
```

**Cause**: Accessing attribute on potentially None value
**Fix**: Add None check before access

## Exit Codes

| Code | Meaning                                  |
| ---- | ---------------------------------------- |
| 0    | No errors                                |
| 1    | Errors found in the code                 |
| 2    | Fatal error inside pyright               |
| 3    | Config file could not be read or parsed  |
| 4    | Invalid command-line arguments           |

Codes 2 to 4 mean the checker setup is broken, not the code. Fix the setup before reading any results.

## Output Interpretation

```bash
# Example output
path/to/file.py:10:5 - error: "str" is not assignable to "int" (reportArgumentType)
path/to/file.py:15:8 - error: Import "requests" could not be resolved (reportMissingImports)
```

Format: `file:line:column - level: message (ruleCode)`

## Diagnostic Rules

Common diagnostic rules:

- `reportMissingImports` - Unresolved imports
- `reportArgumentType` - Type mismatch in function arguments
- `reportAttributeAccessIssue` - Invalid attribute access
- `reportOptionalMemberAccess` - Accessing members on Optional types
- `reportGeneralTypeIssues` - General type inconsistencies

## Suppressing Errors

Fix the cause first. Suppress only a diagnostic you have confirmed is wrong, as narrowly as possible, with the reason next to it.

### Inline Suppression

Put the comment at the end of the line that has the error; on a line of its own it does nothing. Always name the rule, since a bare `# pyright: ignore` hides every error on the line:

```python
result = legacy_call("42")  # pyright: ignore[reportArgumentType]  # accepts str at runtime; stubs say int
```

### File-Level Suppression

One rule for one file, with the reason:

```python
# pyright: strict, reportPrivateUsage=false
# Tests exercise private helpers on purpose.
```

### Configuration Suppression

Only for a rule that is wrong for the whole codebase, and never for `reportMissingImports`:

```toml
[tool.pyright]
reportPrivateImportUsage = "warning"  # vendored SDK re-exports names without __all__
```

## Best Practices

1. **Start with basic mode** - Gradually increase strictness
2. **Fix errors before warnings** - Prioritize actual type errors
3. **Use type hints incrementally** - Don't annotate everything at once
4. **Exclude generated code** - Add to exclude list in config
5. **Run in CI/CD** - Catch type errors before deployment

## Common Patterns

### Checking an Independent Script

Follow [MetaSkill.md → Checks](../MetaSkill.md#checks): sync the script's environment, then pass its interpreter with `--pythonpath`.

### Checking Specific Directories

Paths are relative to `pyproject.toml`:

```toml
[tool.pyright]
include = [
    "scripts",  # Example: a skill's bundled scripts
]
```

## Resources

- Docs: https://microsoft.github.io/pyright/
- Configuration: https://microsoft.github.io/pyright/#/configuration
- Type Checking Modes: https://microsoft.github.io/pyright/#/type-checking-modes
