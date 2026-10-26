---
name: "gh-stack"
description: "Manages stacked PRs and splits multi-part work into reviewable branches with gh-stack. Use for stack creation, viewing, edits, push, submit, sync, rebase, merge, or checkout; when asked to split or isolate work for review; whenever a user mentions a stack, branch layers, dependent PRs, or gh stack; or when a stack is checked out."
kind: "dev"
---

# gh-stack

A stack is a chain of branches, or layers, on a trunk. Each layer has one PR based on the layer
below, so a reviewer reads one layer at a time. `gh stack`, a GitHub CLI extension, builds stacks
that GitHub groups natively. `gh stack <command> --help` is authoritative for flags, and the
[official guide](https://github.github.com/gh-stack/) for the rest. This skill holds what they
leave out: the shape a project needs, how to run `gh stack` without a terminal, and what GitHub
refuses in a native stack.

## Pick the shape

An active playbook decides which work to stack; this section decides how. Read how the project
merges in its `AGENTS.md`, then take the first case that matches:

- **The parts touch the same lines, or cannot land apart:** one PR, no stack
- **The project merges by pushing a head to its trunk, such as `git push origin <branch>:main`:**
  a [plain stack](#plain-stack), since GitHub refuses to retarget a PR in a native stack, so the
  push would leave it open. When the project's land steps run `gh stack unstack` first, use a
  [native stack](#native-stack), which [Land](#land) unstacks before the push
- **Otherwise:** a [native stack](#native-stack)

Plan the layers before writing code: one concern per layer, foundations at the bottom, each change
in the lowest layer that needs it. A layer you cannot describe in one sentence is two layers. Name
branches `<topic>/<concern>` unless the project has a convention. A stack is linear, so unrelated
work gets its own PR or stack.

Branch the bottom layer from the remote trunk, since the local trunk can lag, for example when
another worktree holds it: `git fetch <remote>`, then `git switch -c <bottom> <remote>/<trunk>`.

Opening PRs needs `gh auth status --active --hostname github.com` to pass; local layers do not.
When it fails, push the layers with git, open no PR, and say the PRs wait for a signed-in `gh`.

A stack is consistent when `git merge-base --is-ancestor <lower> <upper>` succeeds for each pair of
adjacent layers. Run each `git rebase --update-refs` from `<top>`, the top layer checked out: git
moves the branch it rebases, but skips without an error every other branch checked out in a
worktree when the rebase starts, the one you started from included. Check that the stack is
consistent before you push, and report a layer that another worktree holds instead of pushing it
stale.

## Native stack

Check `gh stack --version` first; when it fails, run `gh extension install github/gh-stack`. Once
per clone, run `git config rerere.enabled true`, which `init` otherwise asks about under a
terminal. With several remotes, set `git config remote.pushDefault <name>`.

Under a terminal, `gh stack` opens prompts or a full-screen view that block an agent forever.
Always run these forms:

| Run | Instead of |
|---|---|
| `gh stack view --json` | `gh stack view` |
| `gh stack init --base <trunk> <branch>...`, `gh stack add <branch>` | `init` or `add` without a branch |
| `gh stack submit --auto --open` | `gh stack submit` |
| `gh stack sync > /dev/null` | `gh stack sync`, which prompts on a divergence |
| `gh stack merge <PR or stack-number> --yes` | `gh stack merge` alone |
| `gh stack checkout <target>`, `up`, `down`, `top`, `bottom` | `checkout` alone, `switch`, `modify` |

1. **Start.** Branch the bottom layer as [Pick the shape](#pick-the-shape) says, then run
   `gh stack init --base <trunk> <bottom>`, which adopts it. Commit, then run `gh stack add <next>`
   for each layer above, which branches from the current layer, and commit there. Done when
   `gh stack view --json` names `<trunk>` as `trunk` and lists the layers bottom to top. Stop here
   when the user asked for local layers only
2. **Open the PRs.** Run `gh stack submit --auto --open`; `--auto` writes the titles, and
   `gh pr edit <number>` changes one. `submit` and `sync` can exit 0 after a push or GitHub
   failed. Done when, after `git fetch <remote>`, `git rev-parse <layer> <remote>/<layer>` prints
   one commit twice for each layer, `gh pr view <number> --json baseRefName,isDraft` shows each PR
   ready and based on the layer below, and, from two PRs up,
   `gh api 'repos/{owner}/{repo}/stacks?pull_request=<bottom PR>' --jq '.[] | {number, prs: [.pull_requests[].number]}'`
   lists every PR bottom to top; no output means GitHub holds no stack
3. **Change a layer.** Check out the layer that owns the change, found with `gh stack view --json`
   or `git log --all -- <path>`, and commit there. Then run `gh stack rebase --upstack`, or
   `gh stack rebase --upstack --no-trunk` when another worktree holds the trunk, as
   `git worktree list` shows, and `gh stack push`, or follow [Force pushes](#force-pushes). Done
   when the stack is consistent from that layer up and step 2's check passes
4. **Sync with the trunk.** When another worktree holds the trunk, leave it alone, since `sync` and
   `rebase` without `--no-trunk` can fast-forward it there: run `git fetch <remote>`, then, from
   `<top>`, `git rebase --update-refs <remote>/<trunk> <top>`, check that the stack is consistent,
   and run `gh stack push`. Otherwise run `gh stack sync > /dev/null`. Done when stderr has no
   `Sync aborted`, `git merge-base --is-ancestor <remote>/<trunk> <bottom>` succeeds, and step 2's
   check passes

To stack open PRs, or a new PR on an open PR in no stack, run
`gh stack link --open --base <bottom PR's base> <PR or branch>...`, bottom to top; without
`--base`, `link` retargets the bottom PR to the default branch.
`gh stack link --open <stack-number> <branch>` appends a layer to an existing stack. `link` tracks
nothing locally, so run `gh stack checkout <stack-number>` before a local `gh stack` command.

GitHub refuses, in a native stack:

- `gh pr merge` on any PR: land with `gh stack merge`
- a draft in `gh stack merge`: pass `--open` to `submit` or `link`
- `gh pr edit --base` on any PR: run `gh stack unstack <stack-number>` first, which keeps the PRs
  and branches, retarget, then relink with
  `gh stack link --open --base <trunk> <PRs bottom to top>` when the stack should stay. Once a PR
  of the stack merged, `unstack` leaves the stack in place, and step 2's `gh api` check still
  prints it

## Plain stack

Use git and `gh pr` only, no `gh stack` command, so GitHub never groups the PRs.

1. Branch each layer from the one below, commit, and push it. Open its PR with
   `gh pr create --fill --base <layer below>`, or `--base <trunk>` for the bottom one. Done when
   `gh pr view <number> --json baseRefName` names the layer below for each PR
2. To change a layer, commit on it, then, from `<top>`, run `git rebase --update-refs <layer> <top>`,
   which replays the layers above and moves their branches. When you amended or rebased the layer
   instead, run `git rebase --update-refs --onto <layer> <its old tip> <top>`. To take in the
   trunk, run `git fetch <remote>` and `git rebase --update-refs <remote>/<trunk> <top>`. To fold
   fixes committed on `<top>` with `git commit --fixup=<commit>` into their layers, run
   `top_before=$(git rev-parse HEAD)` after the last fixup, then
   `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash --update-refs "$(git merge-base <remote>/<trunk> <bottom>)"`,
   and check that `git diff --exit-code "$top_before" HEAD` exits 0: a conflict resolved wrong can
   drop a line while the stack stays consistent. Push each moved branch with
   `git push --force-with-lease <remote> <branch>...`, or follow [Force pushes](#force-pushes).
   Done when the stack is consistent

## Force pushes

`gh stack submit`, `sync`, `push`, and `rebase` rewrite or force-push layers, with
`--force-with-lease`. When a rule says to ask before any force push and a layer is already on the
remote, add commits instead: commit on the owning layer and run `git push <remote> <layer>`. Then,
for each layer above, bottom to top, run `git switch <upper>`,
`git merge --no-ff --no-edit <layer below>`, and `git push <remote> <upper>`. To take in the trunk,
merge `<remote>/<trunk>` into the bottom layer the same way, instead of `sync` or a rebase.

## Land

Land the PRs you were asked to land, from the bottom. Done when `gh pr view <number> --json state`
prints `MERGED` for each of them and, for each PR merged outside the default branch, you reported
every issue its closing keywords name that is still open, as the last item below says.

When the bottom PR's base is a branch whose own PR merged outside the stack, retarget the bottom
PR to the trunk first, in a native stack as the refusals above say.

- **The project merges through GitHub:** in a native stack, `gh stack merge <PR> --yes` with the
  project's method flag, such as `--squash`, lands that PR and every unmerged PR below it, all or
  nothing unless a merge queue takes them; a stack number lands the whole stack. Pass the method
  each time, since the last one used is reused otherwise. A plain stack lands with the project's
  merge command, one PR at a time. After each merge, run `gh pr edit <next> --base <trunk>`, then,
  from `<top>`, `git rebase --update-refs --onto <remote>/<trunk> <merged layer's old tip> <top>`,
  and push the moved branches
- **The project merges by pushing a head to its trunk:** in a native stack, first run
  `gh stack unstack <stack-number>`. Then retarget every PR to the trunk, bottom to top, with
  `gh pr edit <number> --base <trunk>`, push every layer you rebased, and apply the project's method
  once to the top layer. A PR turns `MERGED` when its head on GitHub reaches its base. When the
  stack remains after the unstack, apply the method, then, for each PR still open, bottom to top,
  run `git push <remote> <layer>:refs/heads/<layer below>`, a fast-forward that marks it merged
  into the layer below. GitHub ignores the closing keywords of a PR whose base is not the default
  branch, so list the issues each such PR body names with a closing keyword, as `#N` in the PR's
  repository or `owner/repo#N`, check each with `gh issue view <N> -R <owner/repo> --json state`,
  and report every one still open with its PR

## Recovery

- **Exit 3, a rebase conflict:** after `gh stack rebase`, resolve the files, run `git add`, then
  `gh stack rebase --continue`, or `--abort` to restore every layer. After `gh stack sync`, the
  stack is already restored: run `gh stack rebase` to replay the conflict
- **Exit 9:** stacked PRs are off for the repository; use a plain stack
- **`Sync aborted`, the local and GitHub stacks diverged:** keep GitHub's with
  `gh stack unstack --local` and `gh stack checkout <stack-number>`, or rebuild from the local
  branches as the next item says
- **Rebuild from local branches, or reorder or drop a layer:** rewrite the branches with git, run
  `gh stack unstack`, which also drops local tracking, then
  `gh stack init --base <trunk> <branches bottom to top>`, which adopts them, and
  `gh stack submit --auto --open`
- **Another exit code:** read stderr, then the
  [CLI reference](https://github.github.com/gh-stack/reference/cli/)
