# Ruff - Python Linter & Formatter

Python linter and formatter written in Rust. Replaces Black, isort, and many Flake8 plugins.

Run it in the environment that owns the code, as [MetaSkill.md → Choose the environment](../MetaSkill.md#choose-the-environment) explains. [MetaSkill.md → Checks](../MetaSkill.md#checks) has the full verification sequence.

## Core Commands

Verification changes nothing:

```bash
uv run --locked ruff check .                # lint
uv run --locked ruff format --check .       # list files that need formatting
uv run --locked ruff check path/to/file.py  # one file
```

Repair rewrites files. Run it only when asked to fix, then verify again:

```bash
uv run --locked ruff check --fix .  # apply safe fixes
uv run --locked ruff format .       # rewrite formatting
```

## Configuration

In `pyproject.toml`, settings live under `[tool.ruff]`. Leave `target-version` unset; ruff reads it from `requires-python`:

```toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "F",      # pyflakes
    "I",      # isort (import sorting)
    "UP",     # pyupgrade (modern Python syntax)
    "B",      # flake8-bugbear (common bugs)
    "SIM",    # flake8-simplify (simplification)
]
ignore = [
    "E501",   # line too long (formatter handles this)
]
```

In `ruff.toml` or `.ruff.toml`, drop the `tool.ruff` prefix: settings go at the top level and lint rules under `[lint]`. A `ruff.toml` that keeps `[tool.ruff]` fails with exit 2 and `unknown field tool`:

```toml
line-length = 100

[lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]
```

## Rule Categories

Common rule prefixes:

- `E`, `W` - pycodestyle (style violations)
- `F` - Pyflakes (logical errors)
- `I` - isort (import sorting)
- `UP` - pyupgrade (modernize syntax)
- `B` - bugbear (likely bugs)
- `SIM` - simplify (code simplification)
- `C90` - mccabe (complexity)
- `N` - pep8-naming (naming conventions)

## Exit Codes

| Code | Meaning                                                              |
| ---- | -------------------------------------------------------------------- |
| 0    | No findings, or `--fix` fixed them all                               |
| 1    | Findings: lint violations, or files `format --check` would reformat  |
| 2    | Ruff failed: invalid configuration, invalid CLI options, or a crash  |

Exit 2 means the checker setup is broken, not the code. Fix the setup before reading any results.

## Output Interpretation

The default output shows each finding with a code frame. Add `--output-format concise` for one line per finding:

```bash
path/to/file.py:10:5: F841 Local variable `x` is assigned but never used
path/to/file.py:15:1: E302 Expected 2 blank lines, found 1
```

Format: `file:line:column: CODE Message`

## Best Practices

1. **Verify before repairing** - Run `check` and `format --check` first so the original findings stay visible
2. **Fix, then format** - Run `check --fix` before `format`
3. **Ignore sparingly** - Only ignore rules with good reason, and write the reason next to the ignore
4. **Project-wide config** - Keep configuration in `pyproject.toml`

## Common Issues

### Import Sorting Conflicts

Ruff handles import sorting automatically. Remove isort if present.

### Line Length

Formatter respects `line-length` setting. Default is 88 (Black's default).

### Ignore Specific Lines

Put `# noqa` at the end of the offending line and name the rule:

```python
x = 1  # noqa: F841
```

`# ruff: noqa: RULE` on a line of its own exempts the whole file from that rule. For that intent, prefer `per-file-ignores` in the configuration.

## Resources

- Docs: https://docs.astral.sh/ruff/
- Rules: https://docs.astral.sh/ruff/rules/
- Configuration: https://docs.astral.sh/ruff/configuration/
