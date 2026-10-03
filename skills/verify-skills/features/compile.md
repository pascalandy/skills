# Compile

`just compile-skills` turns each package in `authoring/` into `skills/<name>/` and rewrites `docs/references/skill-count.md`. `just remote-skills` rewrites the skill tables in `docs/references/`. A checkout is compiled when both report no difference.

## Sub-features

- `compile-check`: `skills/` and the skill count match `authoring/`
- `remote-check`: the generated skill tables match `skills/`

## How to get to it (user POV)

- `just compile-skills`, then `just remote-skills`, after editing a package in `authoring/`
- `just check`, which runs both checks

## Driving it with just

Preconditions:

- Launch and Doctor passed

- **Check both.** Run the block. It prints `compile-check: exit 0` and `remote-check: exit 0`, and both `.out` files are empty.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  record compile-check just compile-skills --check &&
  record remote-check just remote-skills --check )
```

## Gotchas

- A failure lists each differing skill or table in its `.err` file. The change was not compiled, or the compiler broke; report which and stop
- An install recompiles the checkout's `skills/`. On a compiled checkout that changes nothing, which is why this feature runs first
