# Shortcuts

Each row is a shortcut agents take in Rust, the fix to make instead, and what catches it. "Guard" means `rust_guard.py diff`; "review" means a human or a review pass, since no tool catches it reliably.

## Silencing a check

| Shortcut | Instead | Caught by |
|---|---|---|
| `#[allow(lint)]` on the failing item | Fix the code; if the lint is wrong here, ask, then `#[expect(lint, reason = "…")]` | Lint, guard |
| Editing `[lints]`, `clippy.toml`, or CI to pass | Fix the code. A guardrail changes only with approval | Guard |
| `unsafe` to get past the borrow checker | Restructure ownership; see the next table | Lint, guard |

## Errors

| Shortcut | Instead | Caught by |
|---|---|---|
| `.unwrap()`, `.expect()`, `panic!` in non-test code | Return `Result` and use `?`; add context where the caller needs it | Lint, guard |
| `let _ = result;` or `result.ok();` | Handle the error, or propagate it | Lint |
| `.unwrap_or_default()` on a real failure | Propagate the error. A default is right only when absence is normal | Review |
| `.map_err(\|_\| MyError)` | Keep the source: `MyError::Io(e)`, or `#[from]` with `thiserror` | Lint |
| `anyhow::Error` returned from a library | A typed error the caller can match on | Review |

## Ownership

Read the error code as a question about the design before reaching for a fix.

| Error or shortcut | Ask first | Usual fix |
|---|---|---|
| E0382, then `.clone()` | Who should own this value? | Borrow `&T`, move it once, or share it as `Arc<T>` when several owners are real |
| E0499 or E0502, then `RefCell` | Why do two paths mutate at once? | Split the borrow, shorten its scope, or change the data layout |
| E0597, then `'static` or `Box::leak` | Is the scope boundary in the right place? | Move the owner up, or return an owned value |
| E0277 `Send`, then `Arc<Mutex<_>>` everywhere | Does this state need sharing at all? | One owner task and a channel; `Mutex` only for state that is truly shared |
| A lock guard held across `.await` | What does the guard protect during the await? | Release it before the await, or use `tokio::sync::Mutex` |

`diff` counts new `.clone()` and `Arc<Mutex<_>>` as notes for review.

## Tests

| Shortcut | Instead | Caught by |
|---|---|---|
| `#[ignore]` on a failing test | Fix the code, or ask | Guard |
| Deleting a test or an assertion | Fix the code, or ask | Guard |
| Changing an expected value to match a wrong output | Fix the code. The test states the requirement | Review |
| An implementation that returns what the test expects | Implement the behavior; add a second case that a hard-coded answer fails | `cargo mutants`, review |
| `#[should_panic]` where a `Result` belongs | Return `Result` and assert on the error | Guard |

## Code and comments

| Shortcut | Instead | Caught by |
|---|---|---|
| `x as u32` | `u32::try_from(x)?` | Lint |
| `todo!()` or an empty body that compiles | Finish it, or say what is left | Lint |
| A comment that narrates the next line | Delete it; a comment says why | Review |
| A comment the change made stale | Update or delete it in the same change | Review |
| `// TODO` with no issue | Link the issue: `// TODO(#123): …` | Guard |
| A new dependency for a few lines of code | Write the few lines, or ask | Guard, `cargo deny`, `cargo shear` |
