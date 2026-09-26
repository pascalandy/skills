# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run --no-project python scripts/flatten_skills.py {{args}}

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run --no-project python scripts/check_frontmatter.py {{args}}

# Run behavior checks for the repository maintenance scripts
test-scripts *args:
    @uv run --no-project python -m unittest discover -s scripts/tests {{args}}

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color
