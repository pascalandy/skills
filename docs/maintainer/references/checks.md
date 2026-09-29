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

## Sign off a PR

Push the branch, then run `just signoff`. It runs `just check`, and only when every check passes, `gh signoff` posts a green `signoff` commit status on HEAD. The status belongs to that one commit, so each push needs a new signoff. Each machine needs the extension once: `gh extension install basecamp/gh-signoff`

`gh signoff` refuses and posts nothing when the working tree has uncommitted or untracked files, or when HEAD is not pushed. Fix the cause and continue:

| Situation | Do |
|---|---|
| Refused: HEAD not pushed | `git push`, then `gh signoff`; the passing check already covers this HEAD |
| Refused: uncommitted or untracked files | Commit or remove them, then `just signoff` |
| A check failed | Fix it, commit, push, then `just signoff` |
| Pushed more commits | `just signoff` again |
| Stacked PRs | Check out each layer and run `just signoff`; a restack changes every layer's HEAD, so sign off each again |
| Did this commit get signed off? | `gh signoff status` |

Commit hooks never sign off: git has no hook after a push, and GitHub accepts a status only for a commit it already has

## Add or change a check

Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools. To add a check, add a row to `CHECKS` in `scripts/check.py`. Script tests follow [[script-conventions]]

`just check` prints nothing when every check passes and replays a failing check's output on stderr. `just check --list` names every check, and `just check --only NAME` reruns one. `just check --list --verbose` adds each check's commands on stderr; run a command directly to pass extra flags, such as `-k` to pytest

## Commit hooks

`lefthook.yml` lists each hook and the staged files that trigger it

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Related

- [[script-conventions]]
- [[release]]
