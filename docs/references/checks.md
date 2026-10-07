---
name: Checks
description: How just check, signoff, merge, commit hooks, and the manual CI workflow fit together, and how to change them
tags:
  - area/ea
  - kind/doc
  - topic/ci
  - status/stable
date_created: 2026-09-26
date_updated: 2026-10-04
---

`just check` is the routine verdict, and it runs on your machine. `just signoff` posts a passing result to GitHub as a green `signoff` commit status, and `main` merges a PR only when its head commit carries one. `just merge` signs off a PR head when needed, squash-merges exactly that commit, then runs `just deploy`. Commit hooks run a fast subset before each commit. GitHub Actions runs `just check --sweep` only when started by hand

## Sign off a PR

Push the branch, then run `just signoff`. It records the pushed HEAD, runs `just check` on that commit in a temporary worktree, and only when every check passes posts a green `signoff` commit status on that commit. Edits or checkouts in your checkout during the checks cannot change what they test. The status belongs to that one commit, so each push needs a new signoff. When the branch on GitHub moves while the checks run, it signs nothing. A run that signs off answers `{"ok":true,"changes":[["signoff","SHA"]]}`. A head that already carries a green signoff needs no new run, so a rerun answers `{"ok":true}`. `just signoff --dry-run` answers what a run would, without checking. Each machine needs the extension once: `gh extension install basecamp/gh-signoff`

`just signoff` refuses and posts nothing when the working tree has uncommitted or untracked files, or when HEAD is not the commit GitHub holds for the branch. It compares HEAD with `origin/<branch>`, whatever the upstream: a branch made from `origin/main` tracks `main`, and `gh stack push` sets no upstream. Fix the cause and continue:

| Situation | Do |
|---|---|
| Refused: HEAD is not on GitHub | Run the `git push` the message names, then `just signoff` |
| Refused: GitHub has newer commits | Run the `git pull` the message names, then `just signoff` |
| Refused: uncommitted or untracked files | Commit and push them, or remove them, then `just signoff` |
| A check failed | Fix it, commit, push, then `just signoff` |
| Refused: the branch on GitHub moved during the checks | `just signoff` again |
| Pushed more commits | `just signoff` again |
| Stacked PRs | Check out each layer and run `just signoff`; a restack changes every layer's HEAD, so sign off each again |
| Did this commit get signed off? | `gh signoff status` |
| Merge blocked on `signoff` | `just merge` signs off the PR head, then merges it; never merge with `gh pr merge --admin` to skip the gate |
| Want a run on a clean GitHub runner | `gh workflow run ci.yml --ref <branch>`, then `gh run watch` |

Commit hooks never sign off: git has no hook after a push, and GitHub accepts a status only for a commit it already has

## Merge a PR

Run `just merge` on the PR branch, pushed, with a clean working tree. It squash-merges exactly the commit the checks ran on:

1. It refuses in seconds when the PR is a draft or targets another branch, when the working tree has changes, when HEAD is not the PR head on GitHub, or when the branch lacks the tip of `main`
2. It reuses a green `signoff` on the head, or runs the `just signoff` steps once
3. It waits up to `--timeout` for GitHub to accept the merge, and stops when the PR head, base, or state changes
4. It checks the tip of `main` again, then runs `gh pr merge --squash --match-head-commit`, so GitHub refuses any other head. GitHub cannot pin the base, so a retarget in that last second is reported right after the merge. The subject is `<PR title> (#N)`
5. It reads the PR back, then fails when the tip of `main` holds a tree the checks did not run on, as when another PR lands in the same seconds
6. When the tip of `main` holds that tree, it runs `just deploy`, an alias of `just sync-fleet`, from the main checkout. The deploy runs the main checkout's code, so that checkout must hold a commit of `main`, with no changes under `scripts/` or the justfile. The deploy brings the fleet to `main` as it is when the deploy runs. A machine the deploy cannot reach waits for the next sync. When the merge landed but the deploy failed or was withheld, the run exits 1, says that the merge landed, and lists it under `changes`

`just merge --dry-run` runs step 1 and answers what a run would do, without deploying. A rerun on a merged PR runs only the deploy. It never deletes the branch

| Situation | Do |
|---|---|
| Refused: the branch lacks the tip of `main` | `git merge origin/main`, `git push`, then `just merge` |
| Refused: the PR targets another branch | A stack lands through its stack: sign off each layer, run `gh stack merge <stack> --yes --squash`, then `just deploy` |
| GitHub did not accept the merge in time, exit 75 | `just merge` again; it reuses the signoff |
| Interrupted | `just merge` again; on a merged PR it only deploys |
| The merge landed, but `just deploy` did not reach every machine | Fix what its answer names, then `just deploy` |
| The merge landed, but `main` holds a tree the checks did not run on | `just check` on an up-to-date `main`, then `just deploy` |
| The merge landed, but the main checkout holds code `main` never had | Put it back on a commit of `main`, with no changes under `scripts/` or the justfile, then `just deploy` there |

## The signoff rule

`gh signoff install` created the `signoff` ruleset on `main`. It requires the `signoff` status to merge a PR and blocks force pushes and deletion of `main`. Repository admins bypass it, so direct pushes to `main` keep working. `gh signoff check` reports whether the rule is on; `gh signoff uninstall` removes it, and `gh signoff install` restores it

## Manual CI workflow

`.github/workflows/ci.yml` runs only when started by hand, and its result is not the `signoff` status. `gh workflow run ci.yml --ref <branch>` runs `just check --sweep` on a GitHub runner. Started on a `vX.Y.Z` tag, it also validates and publishes that release, a fallback for the local publish step in [[release]]

## Add or change a check

Keep `just check` CI-safe: it needs no secrets or private packages and uses the network only to download tools. To add a check, add a row to `CHECKS` in `scripts/check.py`. Script tests follow [[script-conventions]]

A skill check whose commands name a path under `authoring/` belongs to the package holding that path. `just check` selects it when the branch, compared with `origin/main`, or the working tree changes a file in that package, or changes `scripts/check.py`, which pins the tools. A check that reads files outside its package lists them in `reads=`, and a change to them selects it too. The direct repository validators always run. When git cannot compare with `origin/main`, every check runs. `--only NAME` runs a named check regardless of changed paths. `--sweep` runs every check, including unrelated suites, for release or diagnosis. `--verbose` names each skipped check

The root test suite has one `test-<stem>` check for each `scripts/tests/test_<stem>.py` module. Underscores in `<stem>` become hyphens in the check name. The registry fails before running checks if a test module has no route or a route is stale or duplicated. `just check` always includes the two cheap project-rule tests, `test-commands` and `test-skill-invocation`. It selects other root test modules when their file or a declared `reads` dependency changes. Changes to `scripts/check.py`, `scripts/_cli.py`, `scripts/_common.py`, `pytest.ini`, or `scripts/tests/conftest.py` select every root test module. Selected root modules run in one pytest process. When it fails, the rerun command names only the modules pytest reports as failed, or every module of the batch when its output cannot tell, as after a collection error. Use `just check --only test-sync-fleet` to rerun one module

`just check` answers `{"ok":true}` when every check passes. A failure replays the failing check's output on stderr and ends it with `{"ok":false,…}`, as [[script-output]] shows. `just check --list` answers with every check's name, and `just check --only NAME` reruns one. `just check --list --verbose` adds each check's commands on stderr; run a command directly to pass extra flags, such as `-k` to pytest

## Commit hooks

`lefthook.yml` lists each hook and the staged files that trigger it

Without `.gitleaks.toml`, gitleaks uses built-in rules. For an allowlist, start `.gitleaks.toml` with `[extend]` / `useDefault = true`; otherwise every scan passes because built-in rules are disabled

## Related

- [[script-conventions]]
- [[script-output]]
- [[release]]
