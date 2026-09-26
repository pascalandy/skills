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
    @uvx pytest {{args}}

# Lint, format-check, type-check, and test the repository scripts
check:
    @uvx ruff check --quiet scripts
    @uvx ruff format --quiet --check scripts
    @uvx --with pytest pyright --pythonversion 3.11 scripts
    @just test

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
