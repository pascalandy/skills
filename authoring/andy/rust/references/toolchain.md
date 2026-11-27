# Toolchain

The gate is the `check` recipe in [../assets/justfile](../assets/justfile). Each step answers one question.

| Step | Answers | Why this tool |
|---|---|---|
| `cargo fmt --all --check` | Is the code formatted? | The standard formatter |
| `cargo clippy --workspace --all-targets --all-features --locked -- -D warnings` | Does the code pass the lint profile, tests included? | `--workspace` covers every member even when the root is a package; `--all-targets` covers tests and examples; `--locked` fails on a stale `Cargo.lock` instead of rewriting it |
| `cargo test --workspace --all-features --locked` | Do the tests and doctests pass? | Runs doctests too |
| `cargo deny --all-features check` | Any known vulnerability, banned crate, rejected license, or unknown source? | Covers the RustSec advisories, so `cargo-audit` adds nothing |
| `cargo shear` | Any dependency the code never uses? | Parses the code instead of matching regexes, so it misfires less than `cargo-machete`; `cargo shear --fix` removes what it finds |
| `uv run scripts/rust_guard.py diff` | Does the change add an exception? | Catches what lints cannot: removed tests, new dependencies, edited guardrails |

`--locked` needs a `Cargo.lock`. `init` creates one; commit it, for libraries too.

## Test strength

`cargo mutants` changes the code, such as replacing a function body with a default value, and reports each change no test caught. Run it on the diff only, since a whole-crate run takes long:

```bash
git diff "$(git merge-base origin/main HEAD)" > /tmp/change.diff
cargo mutants --in-diff /tmp/change.diff
```

Install with `cargo install --locked cargo-mutants`; `cargo mutants --version` confirms it. A missed mutant is a change no test noticed. Read it: when it changes behavior a caller would notice, add the case that catches it; some mutants change nothing observable.

## Optional tools

| Tool | Use when | Note |
|---|---|---|
| `cargo nextest run` | The test suite is slow | Faster runner, but it skips doctests: keep `cargo test --doc` in the recipe |
| `cargo semver-checks` | A published library changes its public API | Reports changes that break semantic versioning |
| `cargo +nightly miri test` | The crate has `unsafe` code | Detects undefined behavior at run time |

## When a step fails

- `cargo deny check` reports `unlicensed` for the crate itself: set `license` in `Cargo.toml`, or `publish = false` for a crate that is never published
- `cargo deny check` rejects a dependency's license: adding it to the `allow` list edits `deny.toml`, which is an exception
- `cargo deny check` flags an advisory: update the crate with `cargo update -p <crate>`. Ignoring an advisory edits `deny.toml`, which is an exception
- `cargo shear` flags a crate that a macro or build script uses: ask before adding it to `[package.metadata.cargo-shear] ignored`, since that edits `Cargo.toml`
- `cargo clippy` or `cargo test` fails only under `--all-features`, because two features exclude each other: the gate assumes features combine. Tell the user before changing the recipe; a recipe that checks each valid feature set instead differs from the skill's, so `init` refuses it and `audit` lists the missing steps
