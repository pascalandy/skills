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

# Run the same CI-safe verdict as GitHub Actions
check:
    @just check-frontmatter
    @just flatten-skills --check
    @uvx ruff@{{ruff_version}} check --quiet scripts
    @uvx ruff@{{ruff_version}} format --quiet --check scripts
    @uvx --with pytest=={{pytest_version}} pyright@{{pyright_version}} --pythonversion 3.11 scripts
    @uvx pytest@{{pytest_version}}
    @uvx --from actionlint-py@{{actionlint_version}} actionlint

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color
