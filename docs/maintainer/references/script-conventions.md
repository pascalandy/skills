---
name: Script conventions
description: Rules for CLIs in scripts/ and in skill-local scripts/ folders
tags:
  - area/ea
  - kind/doc
  - topic/scripts
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-26
---

CLIs in `scripts/` follow these rules. Apply them when writing or changing skill-local scripts

## Rules

- `-h, --help` prints usage and examples without changes
- Quiet by default: one line on stdout on success
- `-v, --verbose` adds per-item detail and tracebacks on stderr
- `--dry-run` previews writes and deletions
- Failures print `error: <what went wrong and how to fix it>` on stderr, then `rerun with --verbose for details`
- Exit codes: `0` success, `1` failure, `2` bad usage, `130` interrupted
- Use only the standard library (`argparse`, `logging`) unless a dependency earns its place
- `justfile` recipes forward arguments (`recipe *args`) to scripts

## Shared entry point

`scripts/_common.py` applies these rules. Build the parser; return `run_script(parser, work)` from `main()`. `work` returns the success line or raises `ScriptError` with one message per problem

## Tests

Tests live in `scripts/tests/`. `just check --only test` runs them, and [[checks]] explains how they join CI

The `jevgate` engine in `create-a-jev-cli-decision-wrapped-in-a-skill` has its own suite in the skill's `scripts/tests/`. `just check --only jevgate` runs its ruff, pyright, and offline behavior tests. After editing the engine, run `uvx ruff format` on it, then `uv run authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/stamp_engine.py`, so vendored copies can detect local edits

## Related

- [[checks]]
- [[release]]
