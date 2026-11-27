---
name: "rust"
description: "Use when writing, fixing, or reviewing Rust code, setting up a new Cargo crate or workspace, adding lints or a check recipe to an existing Rust project, or when a Clippy lint, a failing test, or a borrow-checker error tempts a shortcut."
kind: "dev"
---

# Rust

An agent skims prose but cannot argue with a failing build. This skill puts the rules in lints, a check recipe, and a diff guard, and keeps one rule in prose: when a guardrail blocks you, stop and ask before you add an exception.

Rules that belong to one project, such as its error type, its async runtime, or its module layout, live in that project's `AGENTS.md`. Read it first, and follow it where it differs from this skill.

## Prerequisites

Confirm each tool before the step that needs it. Give the user the install command of a missing one instead of working around it.

| Tool | Install | Confirm |
|---|---|---|
| Rust with Clippy and rustfmt | [rustup](https://rustup.rs), then `rustup component add clippy rustfmt` | `cargo clippy --version` |
| `uv`, which runs the guard script | [install uv](https://docs.astral.sh/uv/getting-started/installation/) | `uv --version` |
| `just` | `cargo install --locked just` | `just --version` |
| `cargo-deny` | `cargo install --locked cargo-deny` | `cargo deny --version` |
| `cargo-shear` | `cargo install --locked cargo-shear` | `cargo shear --version` |
| `lefthook`, optional | [install lefthook](https://lefthook.dev/installation/) | `lefthook version` |

`<skill>/scripts/rust_guard.py` is this skill's copy of the guard; it runs `init` and `audit`. `init` writes a project copy at `scripts/rust_guard.py`, which runs `diff`; before `init`, run `diff` from the skill's copy. Run `uv run <skill>/scripts/rust_guard.py --help` for every flag.

## Pick the branch

| Situation | Branch |
|---|---|
| No guardrails yet: a new crate, or a project the user wants set up | [A. Set up](#a-set-up) |
| An existing project with its own lints, recipes, or debt | [B. Audit](#b-audit) |
| Writing or fixing code | [C. Work](#c-work) |
| Reviewing a change or a pull request | [D. Review](#d-review) |

### A. Set up

1. For a new crate, run `cargo new <name>`, which uses the latest edition. Set `rust-version` in `Cargo.toml` to the oldest Rust the crate supports, and either `license` or, for a crate never published, `publish = false`: `cargo deny` rejects a crate with neither
2. From the crate or workspace root, run `uv run <skill>/scripts/rust_guard.py init --dry-run`, then without `--dry-run`. It writes the lint profile, `clippy.toml`, `deny.toml`, the `check` recipe, `lefthook.yml`, a copy of the guard under `scripts/`, and the exception rule in `AGENTS.md`. A file the project already has keeps its content, except the guard copy and the `AGENTS.md` section, which `init` refreshes. A rerun changes nothing
3. Run `just check`. Fix what it reports in the code, never in the guardrails. Its last step, `rust_guard.py diff`, lists the setup itself, since the setup edits guarded files: show the user that list, and commit the setup once they approve it
4. Run `lefthook install`, since the pre-commit hook is what stops an exception before it is committed. For a crate nested in a larger repository, first add the commands `init`'s note names to the root `lefthook.yml`. Done when `just check` passes on the committed setup

### B. Audit

1. Run `uv run <skill>/scripts/rust_guard.py audit --violations`. It lists, per manifest, the profile lints the project lacks and whether a workspace member inherits `[workspace.lints]`, then the guardrail files present, the gate steps the `check` recipe lacks, whether lefthook runs the staged guard, whether `clippy.toml` lets tests use `unwrap`, `expect`, and `panic!` (`tests_may_panic`), and the Clippy findings for every profile lint
2. Propose the change to the user, since it edits `[lints]` and the `justfile`. Turn on now every lint at zero findings. For the others, say what leaving them out costs: `rust_guard.py diff` flags new `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!`, and `dbg!` while existing ones stay, but nothing guards the cast and swallowed-error lints until they are on
3. After approval, apply the lints, add the missing gate steps to the `check` recipe, the `exceptions` command of the skill's `lefthook.yml` to the project's, and, when `tests_may_panic` is false, the three `allow-*-in-tests` keys of the skill's `clippy.toml` to the project's, then follow [A. Set up](#a-set-up) from step 2. Done when `just check` passes on the committed change

### C. Work

1. Read the contract: the project's `AGENTS.md`, its `[lints]`, and `just --list`
2. Write the change. Keep tests in the same change as the code they cover
3. Run `just check` before every commit. When a lint, a test, or the guard blocks you, find the shortcut in [references/shortcuts.md](references/shortcuts.md) and fix the design it points to
4. When the fix still needs an exception, follow [Exceptions](#exceptions)
5. Done when `just check` passes and your reply quotes its result

### D. Review

1. Run `uv run scripts/rust_guard.py diff --base origin/main --report` from the project, with the pull request's base branch. It lists each exception it detects in the branch and counts new `.clone()` and `Arc<Mutex<_>>`
2. Check each exception against an approval in the conversation or the PR description
3. Read the change against the review column of [references/shortcuts.md](references/shortcuts.md), which covers what no lint catches
4. When tests changed with the code, run `cargo mutants --in-diff` as [references/toolchain.md](references/toolchain.md) describes. Read each missed mutant: when it changes behavior a caller would notice, add the test case that catches it

## Exceptions

These need explicit approval in the conversation before they stay: `unsafe`, `#[allow]`, `#[expect]`, `#[ignore]`, `#[should_panic]`, a new dependency, a deleted or weakened test or assertion, a `TODO` without an issue link, and any edit to `[lints]`, `clippy.toml`, `deny.toml`, `justfile`, `lefthook.yml`, `rust-toolchain.toml`, CI, or `scripts/rust_guard.py`. `rust_guard.py diff` compares the working tree with the last commit, so `just check` and the pre-commit hook stop on each one it detects until it is committed. A weakened assertion or a changed expected value shows only in review.

1. Stop and tell the user what blocks you, the exception you need, and why the design cannot avoid it
2. After approval, write the reason where the exception lives, such as `#[expect(clippy::cast_possible_truncation, reason = "length is capped at u16::MAX")]`. Use `#[expect]`, never `#[allow]`: it fails the build once it stops matching, so a stale exception cannot linger
3. Commit the change. When the pre-commit hook still stops it, commit with `LEFTHOOK_EXCLUDE=exceptions git commit`
4. Paste the list from `uv run scripts/rust_guard.py diff --base origin/main --report`, with the pull request's base branch, into the PR description

`unsafe_code` is `forbid`, which no attribute can lift. Code that truly needs `unsafe` gets the user's approval to set it to `deny` in `Cargo.toml`. Each `unsafe` item then carries `#[expect(unsafe_code, reason = "…")]`, and each `unsafe` block a `// SAFETY:` comment.

## References

- [references/lint-profile.md](references/lint-profile.md): why each lint is in the profile, the library additions, workspaces, and how to check a lint name. Read when choosing, explaining, or changing lints
- [references/shortcuts.md](references/shortcuts.md): each shortcut an agent takes, the fix to make instead, and what catches it. Read when a check blocks you, and in every review
- [references/use-cases.md](references/use-cases.md): example prompts for each branch and how to phrase an approval. Read when the user asks how to use this skill or what it can do
- [references/toolchain.md](references/toolchain.md): what each tool in the gate does and why it was chosen, plus `cargo-mutants` and the optional tools. Read when a tool fails or before adding one
