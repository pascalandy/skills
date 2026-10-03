# Discovery

`just skills-discover` asks the Codex, Pi, and OpenCode CLIs which skills they load, without a model call, and compares their answers with what the checkout installs. Claude Code has no listing interface, so it always reports `unverified`.

## Sub-features

- `discover-codex`: Codex loads every skill from `~/.codex/skills` on om1, or `~/.agents/skills` on mac
- `discover-pi`: Pi loads every skill from `~/.pi/agent/skills`
- `discover-opencode`: OpenCode loads every skill from `~/.config/opencode/skills`
- `discover-claude`: reported `unverified` by design

## How to get to it (user POV)

- `just skills-discover --profile om1` after an install
- Step 6 of the cutover in `docs/references/install-skills.md`

## Driving it with just

Preconditions:

- Install passed in this run

- **Discover.** Run the block. It prints `discover: exit 0`, and `discover.out` reads `codex verified`, `pi verified`, `claude unverified`, and `opencode verified`, one tab-separated line each.

```bash
( . "${RUN:?}/env" && cd "$CHECKOUT" &&
  record discover just skills-discover --profile "$PROFILE" --private-root "$RUN/private" )
```

## Gotchas

- OpenCode also loads `.claude/skills` and `.agents/skills` from every parent of its working folder. A run folder under the real home lets the real copies win name clashes at random, so Launch puts it in `/var/tmp`
- OpenCode finds its skill folder through `XDG_CONFIG_HOME`. With the real `XDG_*` folders, it reports every skill missing
- Exit 75 means every failing agent timed out. Rerun, with `--timeout 2m` if it repeats
- A reason that starts with `native adapter changed or failed` is a finding about `scripts/discover_skills.py` or an agent CLI update, not about the install
- The first run in a fresh test home is the slowest, since each CLI creates its state there
