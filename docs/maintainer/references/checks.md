---
name: Checks
description: How just check, CI, and commit hooks fit together, and how to change them
tags:
  - area/ea
  - kind/doc
  - topic/ci
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-28
---

`just check` runs on every PR, push to `main`, and release tag. Commit hooks run a subset locally before each commit

## Add or change a check

Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools. To add a check, add a row to `CHECKS` in `scripts/check.py`. Script tests follow [[script-conventions]]

`just check` prints nothing when every check passes and replays a failing check's output on stderr. `just check --list` names every check, and `just check --only NAME` reruns one. `just check --list --verbose` adds each check's commands on stderr; run a command directly to pass extra flags, such as `-k` to pytest

## Commit hooks

`lefthook.yml` lists each hook and the staged files that trigger it

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Related

- [[script-conventions]]
- [[release]]
