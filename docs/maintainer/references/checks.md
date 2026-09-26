---
name: Checks
description: How just check, CI, and commit hooks fit together, and how to change them
tags:
  - area/ea
  - kind/doc
  - topic/ci
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-26
---

`just check` runs on every PR, push to `main`, and release tag. Commit hooks run a subset locally before each commit

## Add or change a check

Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools. To add a check, add a row to `CHECKS` in `scripts/check.py`. A check for a private package names it in `requires`; machines without the package, including CI, skip that check. Script tests follow [[script-conventions]]

`just check --list` names every check, and `just check --only NAME` reruns one. `just check --list --verbose` prints each check's commands; run a command directly to pass extra flags, such as `-k` to pytest

## Commit hooks

`lefthook.yml` lists each hook and the staged files that trigger it

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Related

- [[script-conventions]]
- [[release]]
