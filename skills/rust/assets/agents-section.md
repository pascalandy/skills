## Rust guardrails

Run `just check` before saying a change is done, and report its result. A change is done only when it passes.

Never add any of these without explicit approval in the conversation:

- `unsafe`, `#[allow]`, `#[expect]`, `#[ignore]`, or `#[should_panic]`
- A dependency
- A change to `[lints]`, `clippy.toml`, `deny.toml`, `justfile`, `lefthook.yml`, `rust-toolchain.toml`, CI, or `scripts/rust_guard.py`
- A deleted test or assertion, or a weakened one

`just check` and the pre-commit hook stop on each of them. Stop too, and explain what blocks you and why. After approval:

1. Write the reason in the attribute, such as `#[expect(clippy::cast_possible_truncation, reason = "length is capped at u16::MAX")]`
2. Commit the change. When the pre-commit hook still stops it, commit with `LEFTHOOK_EXCLUDE=exceptions git commit`. Once committed, the exception no longer fails `just check`
3. Paste the list from `uv run scripts/rust_guard.py diff --base origin/main --report`, with the default branch in place of `main`, into the PR description

A comment explains why the code is as it is, never what it does. A `TODO` links to an issue.
