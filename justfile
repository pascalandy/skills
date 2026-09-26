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

# Check native skill discovery after a separately authorized local install
skills-discover *args:
    @uv run scripts/discover_skills.py {{args}}

# Run the script tests
test *args:
    @uvx pytest@{{pytest_version}} {{args}}

# Run the same CI-safe verdict as GitHub Actions; a failure names the recipe to rerun
check: check-frontmatter (flatten-skills "--check") lint typecheck test lint-workflows check-html-mode check-matt-mode test-distill test-tavily test-transcript test-verify-transcript-sk test-poteto-worktree-audit

# Lint and format-check the repository scripts
lint:
    @uvx ruff@{{ruff_version}} check --quiet scripts
    @uvx ruff@{{ruff_version}} format --quiet --check scripts

# Type-check the repository scripts
typecheck:
    @uvx --with pytest=={{pytest_version}} pyright@{{pyright_version}} --pythonversion 3.11 scripts

# Lint GitHub workflows; optional local linters stay off so every machine agrees
lint-workflows:
    @uvx --from actionlint-py@{{actionlint_version}} actionlint -shellcheck= -pyflakes=

# Validate HEAD as a release candidate and optionally extract release notes
release-check version *args:
    @uv run scripts/release_check.py {{version}} {{args}}

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

test-distill:
    @uvx --from pytest@{{pytest_version}} pytest authoring/knowledge/distill/scripts/tests/ -q

test-tavily:
    @uvx --from pytest@{{pytest_version}} --with httpx --with rich --with respx pytest authoring/web-research/tavily/scripts/tests/ -q

test-poteto-worktree-audit:
    @uvx --from pytest@{{pytest_version}} pytest authoring/pstack/poteto-mode/scripts/tests/test_worktree_audit.py -q

test-transcript:
    @if test -f _skills_private/integrations/transcript-sk/scripts/transcript.py; then uvx --from pytest@{{pytest_version}} --with httpx --with 'yt-dlp==2026.7.4' --with rich pytest _skills_private/integrations/transcript-sk/scripts/tests/ -q; else echo 'skipped: private transcript-sk is absent'; fi

test-verify-transcript-sk:
    @if test -f _skills_private/integrations/verify-transcript-sk/SKILL.md; then uvx --from pytest@{{pytest_version}} pytest _skills_private/integrations/verify-transcript-sk/scripts/tests/ -q; else echo 'skipped: private verify-transcript-sk is absent'; fi

check-transcript-youtube-transport url='https://www.youtube.com/watch?v=EIEc43CxIvY':
    @test -f {{ quote(justfile_directory() / "_skills_private/integrations/transcript-sk/scripts/youtube_smoke.py") }} || { echo 'error: private transcript-sk transport check is missing from _skills_private/integrations/' >&2; exit 1; }; uv run {{ quote(justfile_directory() / "_skills_private/integrations/transcript-sk/scripts/youtube_smoke.py") }} {{ quote(url) }}

check-html-mode:
    @uv run authoring/content/html-mode/scripts/check_html_mode.py

check-matt-mode *args:
    @uv run authoring/mattpocock/matt-mode/scripts/check_matt_mode.py
    @uv run authoring/mattpocock/matt-mode/scripts/update_matt_mode.py check {{args}}

update-matt-mode *args:
    @uv run authoring/mattpocock/matt-mode/scripts/update_matt_mode.py update {{args}}
