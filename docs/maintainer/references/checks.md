---
name: Checks
description: How just check, signoff, commit hooks, and the manual CI workflow fit together, and how to change them
tags:
  - area/ea
  - kind/doc
  - topic/ci
  - status/stable
date_created: 2026-09-26
date_updated: 2026-09-29
---

`just check` is the verdict, and it runs on your machine. `just signoff` posts a passing result to GitHub as a green `signoff` commit status, and `main` merges a PR only when its head commit carries one. Commit hooks run a fast subset before each commit. GitHub Actions runs `just check` only when started by hand

## Sign off a PR

Push the branch, then run `just signoff`. It runs `just check`, and only when every check passes, `gh signoff` posts a green `signoff` commit status on HEAD. The status belongs to that one commit, so each push needs a new signoff. Each machine needs the extension once: `gh extension install basecamp/gh-signoff`

`gh signoff` refuses and posts nothing when the working tree has uncommitted or untracked files, or when HEAD is not pushed. Fix the cause and continue:

| Situation | Do |
|---|---|
| Refused: HEAD not pushed | `git push`, or `git push -u origin HEAD` for a new branch, then `gh signoff`; the passing check already covers this HEAD |
| Refused: uncommitted or untracked files | Commit or remove them, then `just signoff` |
| A check failed | Fix it, commit, push, then `just signoff` |
| Pushed more commits | `just signoff` again |
| Stacked PRs | Check out each layer and run `just signoff`; a restack changes every layer's HEAD, so sign off each again |
| Did this commit get signed off? | `gh signoff status` |
| Merge blocked on `signoff` | Sign off the PR head, then merge; never merge with `gh pr merge --admin` to skip the gate |
| Want a run on a clean GitHub runner | `gh workflow run ci.yml --ref <branch>`, then `gh run watch` |

Commit hooks never sign off: git has no hook after a push, and GitHub accepts a status only for a commit it already has

## The signoff rule

`gh signoff install` created the `signoff` ruleset on `main`. It requires the `signoff` status to merge a PR and blocks force pushes and deletion of `main`. Repository admins bypass it, so direct pushes to `main` keep working. `gh signoff check` reports whether the rule is on; `gh signoff uninstall` removes it, and `gh signoff install` restores it

## Manual CI workflow

`.github/workflows/ci.yml` runs only when started by hand, and its result is not the `signoff` status. `gh workflow run ci.yml --ref <branch>` runs `just check` on a GitHub runner. Started on a `vX.Y.Z` tag, it also validates and publishes that release, a fallback for the local publish step in [[release]]

## Add or change a check

Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools. To add a check, add a row to `CHECKS` in `scripts/check.py`. Script tests follow [[script-conventions]]

`just check` prints nothing when every check passes and replays a failing check's output on stderr. `just check --list` names every check, and `just check --only NAME` reruns one. `just check --list --verbose` adds each check's commands on stderr; run a command directly to pass extra flags, such as `-k` to pytest

## Commit hooks

`lefthook.yml` lists each hook and the staged files that trigger it

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Related

- [[script-conventions]]
- [[release]]
