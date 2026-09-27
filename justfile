# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run scripts/flatten_skills.py {{args}}

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py {{args}}

# Install skills/ into the agent skill directories
install-skills *args:
    @uv run scripts/install_skills.py {{args}}

# Pull main and the private tree, then install every skill on this machine; previews skip the pulls
[positional-arguments]
sync *args:
    #!/usr/bin/env bash
    set -Eeuo pipefail
    for arg in "$@"; do
        case "${arg}" in
            --dry-run | --check | -h | --help) exec uv run scripts/install_skills.py "$@" ;;
        esac
    done
    git pull --quiet --ff-only
    if [[ -d _skills_private/.git ]]; then git -C _skills_private pull --quiet --ff-only; fi
    uv run scripts/install_skills.py "$@"

# Install published main on every machine in _skills_private/fleet.toml, or on named ones
sync-fleet *args:
    @uv run scripts/sync_fleet.py {{args}}

# Check native skill discovery after a separately authorized local install
skills-discover *args:
    @uv run scripts/discover_skills.py {{args}}

# Run the same CI verdict as GitHub Actions; --list names each check, --only NAME reruns one
check *args:
    @uv run scripts/check.py {{args}}

# Validate HEAD as a release candidate and optionally extract release notes
release-check version *args:
    @uv run scripts/release_check.py {{version}} {{args}}

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color

transcript_impl := justfile_directory() / "authoring/content/transcript-sk/scripts/transcript.py"

alias ttr := transcript

# Transcribe one YouTube URL; extra flags go to `transcript.py run youtube`
[positional-arguments]
transcript url *args:
    @uv run {{ quote(transcript_impl) }} run youtube --url "$@"

# Run any transcript-sk command, such as `--help`, `list prompts`, or `doctor --source all`
[positional-arguments]
transcript-cli *args:
    @uv run {{ quote(transcript_impl) }} "$@"
