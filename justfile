# Recipes pass their arguments to scripts as "$@", so each one arrives intact
set positional-arguments

# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run scripts/flatten_skills.py "$@"

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py "$@"

# Install skills/ into the agent skill directories
[no-exit-message]
install-skills *args:
    @uv run scripts/install_skills.py "$@"

# Pull main, save and pull the private clone, then install every skill on this machine; silent on success, previews skip the pulls
[no-exit-message]
sync *args:
    @uv run scripts/sync.py "$@"

# From any machine, sync every machine in _skills_private/fleet.toml, or named ones, to GitHub's main; --check compares them
[no-exit-message]
sync-fleet *args:
    @uv run scripts/sync_fleet.py "$@"

# Lefthook runs this after a commit or pull and before a push; it acts only in a main checkout with the registry
[no-exit-message]
sync-hook *args:
    @uv run scripts/sync_fleet.py --hook "$@"

# Check native skill discovery after a separately authorized local install
skills-discover *args:
    @uv run scripts/discover_skills.py "$@"

# Run the same CI verdict as GitHub Actions; --list names each check, --only NAME reruns one
check *args:
    @uv run scripts/check.py "$@"

# Validate HEAD as a release candidate and optionally extract release notes
release-check version *args:
    @uv run scripts/release_check.py "$@"

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color

alias ttr := transcript

# Transcribe one YouTube URL; extra flags go to `transcript.py run youtube`
transcript url *args:
    @uv run authoring/content/transcript-sk/scripts/transcript.py run youtube --url "$@"

# Run any transcript-sk command, such as `--help`, `list prompts`, or `doctor --source all`
transcript-cli *args:
    @uv run authoring/content/transcript-sk/scripts/transcript.py "$@"
