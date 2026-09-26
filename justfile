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

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color
