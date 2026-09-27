# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run scripts/flatten_skills.py {{args}}

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py {{args}}

# Install skills/ into the agent skill directories
install-skills *args:
    @uv run scripts/install_skills.py {{args}}

# Pull main, save and pull the private clone, then install every skill on this machine; silent on success, previews skip the pulls
[positional-arguments]
sync *args:
    #!/usr/bin/env bash
    set -Eeuo pipefail
    verbose=()
    for arg in "$@"; do
        case "${arg}" in
            --dry-run | --check | -h | --help) exec uv run scripts/install_skills.py "$@" ;;
            -v | --verbose) verbose=(--verbose) ;;
        esac
    done
    branch=$(git symbolic-ref --short -q HEAD || true)
    if [[ "${branch}" != main ]]; then
        echo "error: this checkout is on ${branch:-a detached HEAD}; switch to main, then rerun just sync" >&2
        exit 1
    fi
    git pull --quiet --ff-only
    uv run scripts/sync_private.py ${verbose[@]+"${verbose[@]}"}
    uv run scripts/install_skills.py --quiet "$@"

# From the hub, sync every machine in _skills_private/fleet.toml, or named ones; --check compares them
sync-fleet *args:
    @uv run scripts/sync_fleet.py {{args}}

# Lefthook runs this after a commit or pull; it acts only in the hub's main checkout
sync-hook *args:
    @uv run scripts/sync_fleet.py --hook {{args}}

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
