# Bare `just` lists these in file order: the commands you run most, then checks.
# Each recipe is one line that calls one script or tool; logic lives in scripts/
set positional-arguments

[private]
default:
    @{{ just_executable() }} --list --unsorted

# Pull main, save and pull the private clone, then install every skill on this machine; silent on success, previews skip the pulls
[group('commands')]
[no-exit-message]
sync *args:
    @uv run scripts/sync.py "$@"

alias ttr := transcript

# Transcribe one YouTube URL; extra flags go to `transcript.py run youtube`
[group('commands')]
transcript url *args:
    @uv run authoring/content/transcript-sk/scripts/transcript.py run youtube --url "$@"

# From any machine, sync every machine in _skills_private/fleet.toml, or named ones, to GitHub's main; --check compares them
[group('commands')]
[no-exit-message]
sync-fleet *args:
    @uv run scripts/sync_fleet.py "$@"

# Install skills/ into the agent skill directories
[group('commands')]
[no-exit-message]
install-skills *args:
    @uv run scripts/install_skills.py "$@"

# Flatten categorized authoring packages into the published skills directory
[group('commands')]
flatten-skills *args:
    @uv run scripts/flatten_skills.py "$@"

# Run any transcript-sk command, such as `--help`, `list prompts`, or `doctor --source all`
[group('commands')]
transcript-cli *args:
    @uv run authoring/content/transcript-sk/scripts/transcript.py "$@"

# Run the same CI verdict as GitHub Actions; --list names each check, --only NAME reruns one
[group('checks')]
check *args:
    @uv run scripts/check.py "$@"

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
[group('checks')]
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py "$@"

# Scan staged changes for secrets; lefthook runs it on every commit
[group('checks')]
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color

# Check native skill discovery after a separately authorized local install
[group('checks')]
skills-discover *args:
    @uv run scripts/discover_skills.py "$@"

# Validate HEAD as a release candidate and optionally extract release notes
[group('checks')]
release-check version *args:
    @uv run scripts/release_check.py "$@"

# Lefthook runs this after a commit or pull and before a push; it acts only in a main checkout with the registry
[private]
[no-exit-message]
sync-hook *args:
    @uv run scripts/sync_fleet.py --hook "$@"
