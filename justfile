ruff_version := "0.16.9"
pyright_version := "1.1.414"
pytest_version := "9.1.1"
actionlint_version := "1.7.12.25"

# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run scripts/flatten_skills.py {{args}}

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py {{args}}

# Install skills/ into the agent skill directories
install-skills *args:
    @uv run scripts/install_skills.py {{args}}

# Run the script tests
test *args:
    @uvx pytest@{{pytest_version}} {{args}}

# Run the same CI-safe verdict as GitHub Actions; a failure names the recipe to rerun
check: check-frontmatter (flatten-skills "--check") lint typecheck test lint-workflows

# Lint and format-check the repository scripts
lint:
    @uvx ruff@{{ruff_version}} check --quiet scripts
    @uvx ruff@{{ruff_version}} format --quiet --check scripts

# Type-check the repository scripts
typecheck:
    @uvx --with pytest=={{pytest_version}} pyright@{{pyright_version}} --pythonversion 3.11 scripts

# Lint GitHub workflows; optional local linters stay off so every machine agrees
lint-workflows:
    @uvx --from actionlint-py@{{actionlint_version}} actionlint -shellcheck= -pyflakes=

# Validate HEAD as a release candidate and optionally extract release notes
release-check version *args:
    @uv run scripts/release_check.py {{version}} {{args}}

# Lint, type-check, and run the jevgate engine's offline behavior suite; flags reach pytest
[positional-arguments]
test-jevgate *args:
    #!/usr/bin/env bash
    set -euo pipefail
    dir=authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts
    sdk=$(grep -om1 'typesafe-sdk==[^"]*' "$dir/jevgate.py")
    uvx ruff@0.15.7 check --quiet "$dir"
    uvx ruff@0.15.7 format --quiet --check "$dir"
    uvx --with "$sdk" --with pytest pyright --pythonversion 3.11 "$dir"
    uv run --no-project --quiet --with "$sdk" --with pytest pytest "$dir/tests" "$@"

# Stamp the canonical jevgate engine with its source hash after an edit
stamp-jevgate *args:
    @uv run authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/stamp_engine.py {{args}}

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color
