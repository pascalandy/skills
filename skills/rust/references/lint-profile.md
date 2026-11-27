# Lint profile

The profile lives in [../assets/lints.toml](../assets/lints.toml), and `rust_guard.py init` copies it into `Cargo.toml`. Every lint is at `deny`, because `just check` runs Clippy with `-D warnings`: a `warn` would block the same way while pretending to be softer.

## What each lint blocks

| Lint | The shortcut it blocks |
|---|---|
| `unsafe_code = "forbid"` | `unsafe` added to get past the borrow checker. `forbid` cannot be lifted by an attribute, so lifting it takes a visible `Cargo.toml` edit |
| `unsafe_op_in_unsafe_fn` | An `unsafe fn` body that hides its unsafe operations. Edition 2024 only warns |
| `allow_attributes` | `#[allow]` to silence a lint. `#[expect]` does the same job and fails once it stops matching |
| `allow_attributes_without_reason` | An exception with no `reason = "…"` |
| `undocumented_unsafe_blocks` | An `unsafe` block with no `// SAFETY:` comment |
| `multiple_unsafe_ops_per_block` | One `SAFETY` comment stretched over several operations |
| `unwrap_used`, `expect_used`, `panic` | A panic where the caller deserves a `Result` |
| `todo`, `unimplemented` | A stub that compiles and does nothing |
| `dbg_macro` | Debug output left in the code |
| `let_underscore_must_use` | `let _ = result;`, which discards an error |
| `unused_result_ok` | `result.ok();` as a statement, which discards an error |
| `map_err_ignore` | `.map_err(\|_\| …)`, which drops the cause |
| `cast_possible_truncation`, `cast_sign_loss`, `cast_possible_wrap` | `as` casts that lose data silently. Use `TryFrom` and handle the error |

## Tests

[../assets/clippy.toml](../assets/clippy.toml) allows `unwrap`, `expect`, and `panic!` inside `#[cfg(test)]` code and `#[test]` functions, since a panic is how a test fails. Prefer it to a `#![allow(clippy::unwrap_used)]` at the top of each test file.

Shared helpers under `tests/`, such as `tests/common/mod.rs`, sit outside any test function, so the lints still apply there. Declare them with `#[cfg(test)] mod common;` in each test file that uses them.

## Libraries

A crate other code depends on adds these to its `[lints]`:

```toml
[lints.rust]
missing_docs = "deny"

[lints.clippy]
missing_errors_doc = "deny"
missing_panics_doc = "deny"
print_stdout = "deny"
print_stderr = "deny"
```

## Workspaces

`init` puts the profile under `[workspace.lints]` and adds `[lints] workspace = true` to each member. A member without that line inherits nothing, silently; `audit` reports it as `"inherits": false`.

## Left out on purpose

- The whole `clippy::pedantic` group: under `-D warnings` it blocks hundreds of style lints. Pick single pedantic lints when a project wants them
- `redundant_clone`: still in `clippy::nursery`, so it can misfire. Review catches repeated `.clone()`, and `diff` counts them
- `indexing_slicing` and `as_conversions`: too noisy as a default. Turn them on in code that parses untrusted input

## Check a lint name

Run `cargo clippy --explain <lint>`. An unknown name answers `unknown lint`. Run `rustc -W help` for compiler lints.
