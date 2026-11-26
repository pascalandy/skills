## Rust guardrails

Run `just check` before saying a change is done, and report its result. A change is done only when it passes.

Never add any of these without explicit approval in the conversation:

- `unsafe`, `#[allow]`, `#[expect]`, `#[ignore]`, or `#[should_panic]`
- A dependency
- A change to `[lints]`, `clippy.toml`, `deny.toml`, `justfile`, `lefthook.yml`, `rust-toolchain.toml`, CI, or `scripts/rust_guard.py`
- A deleted test or assertion, or a weakened one

When one of them looks needed, stop and explain what blocks you and why. After approval, write the reason in the attribute, such as `#[expect(clippy::cast_possible_truncation, reason = "length is capped at u16::MAX")]`, run `uv run scripts/rust_guard.py diff --report`, and paste its list into the PR description.

A comment explains why the code is as it is, never what it does. A `TODO` links to an issue.
