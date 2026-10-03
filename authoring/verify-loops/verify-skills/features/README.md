# Skills repository verification map

This map pairs each recipe a skills change goes through with the exact commands and the proof they must produce.

## Baseline preconditions

- Launch and Doctor in [SKILL.md](../SKILL.md) passed, and `RUN` holds the printed run folder

## Proof and skip reporting

- A feature passes when every `.exit` and `.out` file it names matches its page
- Report a failure with its command and its `.err` file, then stop: fixing belongs to the change, not to its verification
- Report a feature you did not run as not run, never as covered by another feature

## Feature entry contract

Each feature page has exactly four H2 sections in this order: `Sub-features`, `How to get to it (user POV)`, `Driving it with just`, and `Gotchas`.

## Features

- `compile.md` covers `skills/`, the skill count, and the generated skill tables: whether they match `authoring/`, and whether the recipes rebuild them
- `install.md` covers skills and commands landing in every agent folder of the profile
- `discovery.md` covers Codex, Pi, and OpenCode loading what the install wrote

## Not driven

- `just sync`, `just sync-fleet` and its alias `just deploy`, `just merge`, `just signoff`, and `just release-check` reach GitHub or other machines
- `just replay-routing` calls Codex models
- `just transcript` has its own skill, `verify-transcript`
- Edge cases already covered by pytest, such as a symlink at a target, a private copy replacing a public one, the Mac targets, and lock timeouts: run `just check --only test-compile-skills --only test-install-skills --only test-discover-skills`
