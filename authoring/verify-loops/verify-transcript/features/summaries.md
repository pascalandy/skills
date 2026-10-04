# Summaries

Summary mode discovers profiles and prompts, resolves one explicit summary plan, and writes Markdown after a successful real transcription.

## Sub-features

- `configuration.prompts` lists bundled prompts and their transcript input kinds
- `configuration.profiles` lists the ordered inference profiles and their complete configurations
- `configuration.models` lists low-level Claude, Codex, and OpenRouter suggestions
- `dry-runs.transcript-only` proves both sources can disable summary configuration without calling a summary model
- `youtube.dry-run-summary` resolves provider, model, effort, and prompt without paid calls
- `zoom.dry-run` resolves the Zoom-specific `opus` and `synthese-rencontre` defaults without paid calls
- `youtube.real-summary` proves a real summary from the `sonnet` test profile and its metadata after transcription

## How to get to it (user POV)

- Run `transcript list prompts --json`
- Run `transcript list profiles --json`
- Pass `--profile` and `--prompt` to a run command
- Pass `--no-summary` to skip the summary while retaining paid transcription

## Driving it with verify-transcript

Preconditions:

- Free discovery and dry-run checks need no paid authorization
- The real summary check needs a signed-in `claude`. The transcript README's `Test videos` rule pre-authorizes its paid calls

- **Discovery.** Run the default `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --json`. Require all three providers and all bundled prompts
- **Plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.dry-run-summary --json`. Require the `glm` profile, OpenRouter, `z-ai/glm-5.3-flash`, `medium`, and `summary_with_quotes`
- **Transcript only.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature dry-runs.transcript-only --json`. Require `summary.enabled: false` and null provider, model, effort, and prompt values for both sources
- **Zoom plan.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature zoom.dry-run --json`. Require the `opus` profile, Claude, `claude-opus-5-5`, `high`, and `synthese-rencontre`
- **Real summary.** Run `uv run "$VERIFY_DIR/scripts/verify_transcript.py" verify --feature youtube.real-summary --allow-paid --json`. Require `summary.status: succeeded`, `summary.profile: sonnet`, non-empty Markdown, and `Summary status: succeeded` in metadata

## Gotchas

- Suggested model lists are discovery aids, not strict allowlists
- `summary_with_quotes` consumes timestamped sentences while the other bundled prompts consume plain text
- A summary failure can publish valid raw artifacts and exit `1`
- The eval requires full success for `youtube.real-summary`
