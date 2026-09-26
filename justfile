# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run --no-project python scripts/flatten_skills.py {{args}}
