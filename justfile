# Flatten categorized authoring packages into the published skills directory
flatten-skills *args:
    @uv run scripts/flatten_skills.py {{args}}

# Check SKILL.md frontmatter quoting; lefthook runs it when a SKILL.md is staged
check-frontmatter *args:
    @uv run scripts/check_frontmatter.py {{args}}

# Install skills/ into the agent skill directories
install-skills *args:
    @uv run scripts/install_skills.py {{args}}

# Check native skill discovery after a separately authorized local install
skills-discover *args:
    @uv run scripts/discover_skills.py {{args}}

# Run the same CI verdict as GitHub Actions; --list names each check, --only NAME reruns one
check *args:
    @uv run scripts/check.py {{args}}

# Validate HEAD as a release candidate and optionally extract release notes
release-check version *args:
    @uv run scripts/release_check.py {{version}} {{args}}

# Record one live synthetic Noul through the real TypeSafe API (needs a key and network)
proof-jevgate-live:
    #!/usr/bin/env bash
    set -euo pipefail
    dir=authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts
    sdk=$(grep -om1 'typesafe-sdk==[^"]*' "$dir/jevgate.py")
    uv run --no-project --quiet --with "$sdk" python "$dir/tests/proof_live_noul.py"

# Stamp the canonical jevgate engine with its source hash after an edit
stamp-jevgate *args:
    @uv run authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/stamp_engine.py {{args}}

# Scan staged changes for secrets; lefthook runs it on every commit
gitleaks-staged:
    @gitleaks git --staged --no-banner --redact --log-level warn --verbose --no-color

# Run the ignored local transcript package without using a dotfiles checkout
transcript_impl := justfile_directory() / "_skills_private/integrations/transcript-sk/scripts/transcript.py"

alias ttr := transcript
[positional-arguments]
transcript url *args:
    #!/usr/bin/env bash
    set -Eeuo pipefail
    readonly implementation={{ quote(transcript_impl) }}
    if [[ ! -f "$implementation" ]]; then
        echo "error: private transcript-sk is missing at $implementation" >&2
        exit 1
    fi
    readonly url="$1"
    shift
    uv run "$implementation" run youtube --url "$url" "$@"

transcript-help:
    @test -f {{ quote(transcript_impl) }} || { echo 'error: private transcript-sk is missing from _skills_private/integrations/' >&2; exit 1; }; uv run {{ quote(transcript_impl) }} --help

transcript-models provider='codex':
    @test -f {{ quote(transcript_impl) }} || { echo 'error: private transcript-sk is missing from _skills_private/integrations/' >&2; exit 1; }; uv run {{ quote(transcript_impl) }} list models --provider {{ quote(provider) }}

transcript-prompts:
    @test -f {{ quote(transcript_impl) }} || { echo 'error: private transcript-sk is missing from _skills_private/integrations/' >&2; exit 1; }; uv run {{ quote(transcript_impl) }} list prompts

[positional-arguments]
transcript-doctor source='all' *args:
    #!/usr/bin/env bash
    set -Eeuo pipefail
    readonly implementation={{ quote(transcript_impl) }}
    if [[ ! -f "$implementation" ]]; then
        echo "error: private transcript-sk is missing at $implementation" >&2
        exit 1
    fi
    readonly source="$1"
    shift
    uv run "$implementation" doctor --source "$source" "$@"

check-transcript-youtube-transport url='https://www.youtube.com/watch?v=EIEc43CxIvY':
    @test -f {{ quote(justfile_directory() / "_skills_private/integrations/transcript-sk/scripts/youtube_smoke.py") }} || { echo 'error: private transcript-sk transport check is missing from _skills_private/integrations/' >&2; exit 1; }; uv run {{ quote(justfile_directory() / "_skills_private/integrations/transcript-sk/scripts/youtube_smoke.py") }} {{ quote(url) }}

update-matt-mode *args:
    @uv run authoring/mattpocock/matt-mode/scripts/update_matt_mode.py update {{args}}
