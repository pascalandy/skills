# Compile

`just compile-skills` turns each package in `authoring/` into `skills/<name>/` and rewrites `docs/references/skill-count.md`. `just remote-skills` rewrites the skill tables in `docs/references/`. A checkout is compiled when both report no difference.

## Sub-features

- `compile-check`: `skills/` and the skill count match `authoring/`
- `remote-check`: the generated skill tables match `skills/`
- `compile-write`: both recipes rebuild deleted output, and the rebuilt output passes both checks

## How to get to it (user POV)

- `just compile-skills`, then `just remote-skills`, after editing a package in `authoring/`
- `just check`, which runs both checks

## Driving it with just

- **Check both.** Run the block. It prints `compile-check: exit 0` and `remote-check: exit 0`, and both `.out` files are empty.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  record compile-check just compile-skills --check &&
  record remote-check just remote-skills --check )
```

- **Rebuild deleted output.** Run the block. It copies the checkout to `$RUN/checkout`, deletes `skills/` and the generated tables there, and rebuilds them. It prints `compile-write: exit 0`, `remote-write: exit 0`, and `compile-after: exit 0`. `compile-write.out` holds one `add` line per skill plus one for `docs/references/skill-count.md`, and `remote-write.out` one `add` line per table. `compile-after.out` is empty.

```bash
( . "${RUN:?}/env" &&
  rsync -a --exclude .git --exclude _skills_private "$CHECKOUT/" "$RUN/checkout/" &&
  cd "$RUN/checkout" && git init -q &&
  rm -r skills docs/references/skill-count.md docs/references/remote-skills*.md &&
  record compile-write just compile-skills &&
  record remote-write just remote-skills &&
  record compile-after sh -c 'just compile-skills --check && just remote-skills --check' )
```

## Gotchas

- A failure in the first block lists each differing skill or table in its `.err` file. The change was not compiled, or the compiler broke; report which and stop
- The copy keeps uncommitted changes and gets a fresh `git init`, because the compiler lists files through git. The rebuild leaves the checkout under test unchanged
- An install recompiles the checkout's `skills/`. On a compiled checkout that changes nothing, which is why this feature runs first
