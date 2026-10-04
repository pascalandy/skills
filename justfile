# Bare `just` lists these in file order: the commands you run most, then checks.
# Each recipe is one line that calls one script or tool; logic lives in scripts/
set positional-arguments

[private]
default:
    @{{ just_executable() }} --justfile {{ quote(justfile()) }} --list --unsorted

# Pull main, save and pull the private clone, then install skills here
[group('commands')]
[no-exit-message]
sync *args:
    @uv run --quiet scripts/sync.py "$@"

alias ttr := transcript

# Transcribe YouTube videos sequentially
[group('commands')]
transcript url *args:
    @uv run --quiet authoring/andy/transcript/scripts/transcript.py run youtube --url "$@"

alias deploy := sync-fleet

# Bring every fleet machine, or the named ones, to GitHub's main
[group('commands')]
[no-exit-message]
sync-fleet *args:
    @uv run --quiet scripts/sync_fleet.py "$@"

# Sign off this branch's PR head if needed, squash-merge that commit, then deploy
[group('commands')]
[no-exit-message]
merge *args:
    @uv run --quiet scripts/merge.py "$@"

# Install skills/ into the agent skill directories
[group('commands')]
[no-exit-message]
install-skills *args:
    @uv run --quiet scripts/install_skills.py "$@"

# Compile authoring/ packages into skills/
[group('commands')]
compile-skills *args:
    @uv run --quiet scripts/compile_skills.py "$@"

# Rebuild the skill lists that agents without these skills read on GitHub
[group('commands')]
remote-skills *args:
    @uv run --quiet scripts/remote_skills.py "$@"

# Run any transcript command, such as `--help` or `doctor`
[group('commands')]
transcript-cli *args:
    @uv run --quiet authoring/andy/transcript/scripts/transcript.py "$@"

# Run the checks that cover changed inputs
[group('checks')]
check *args:
    @uv run --quiet scripts/check.py "$@"

# Run just check on the pushed HEAD, then mark that commit green on GitHub
[group('checks')]
[no-exit-message]
signoff *args:
    @uv run --quiet scripts/signoff.py "$@"

# Check SKILL.md frontmatter quoting
[group('checks')]
check-frontmatter *args:
    @uv run --quiet scripts/check_frontmatter.py "$@"

# Scan staged changes for secrets
[group('checks')]
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color

# Check that agents discover the installed skills
[group('checks')]
skills-discover *args:
    @uv run --quiet scripts/discover_skills.py "$@"

# Replay a skill's routing cases through headless Codex
[group('checks')]
replay-routing *args:
    @uv run --quiet scripts/replay_routing.py "$@"

# Validate HEAD as a release candidate
[group('checks')]
release-check version *args:
    @uv run --quiet scripts/release_check.py "$@"

# Lefthook's sync entry point; it acts only in a main checkout with the private clone
[private]
[no-exit-message]
sync-hook *args:
    @uv run --quiet scripts/sync_fleet.py --hook "$@"
