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
  push would leave it open
- **`gh auth status --active --hostname github.com` fails:** a plain stack, pushed with git. Open
  no PR, and say the PRs wait for a signed-in `gh`
- **Otherwise:** a [native stack](#native-stack)

Plan the layers before writing code: one concern per layer, foundations at the bottom, each change
in the lowest layer that needs it. A layer you cannot describe in one sentence is two layers. Name
branches `<topic>/<concern>` unless the project has a convention. A stack is linear, so unrelated
work gets its own PR or stack.

Branch the bottom layer from the remote trunk, since the local trunk can lag, for example when
another worktree holds it: `git fetch <remote>`, then `git switch -c <bottom> <remote>/<trunk>`.

A stack is consistent when `git merge-base --is-ancestor <lower> <upper>` succeeds for each pair of
adjacent layers.

## Native stack

Check `gh stack --version` first; when it fails, run `gh extension install github/gh-stack`. With
several remotes, set `git config remote.pushDefault <name>`.

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
   `gh pr edit <number>` changes one. `submit` and `sync` can exit 0 after GitHub refused part of
   the stack. Done when
   `gh api 'repos/{owner}/{repo}/stacks?pull_request=<bottom PR>' --jq '.[] | {number, prs: [.pull_requests[].number]}'`
   lists every PR bottom to top; no output means GitHub holds no stack
3. **Change a layer.** Check out the layer that owns the change, found with `gh stack view --json`
   or `git log --all -- <path>`, and commit there. Then run `gh stack rebase --upstack` and
   `gh stack push`, or follow [Force pushes](#force-pushes). Done when the stack is consistent from
   that layer up and the remote holds every changed layer
4. **Sync with the trunk.** Run `gh stack sync > /dev/null`. Done when stderr has no
   `Sync aborted` and step 2's check passes

To stack open PRs, or a new PR on an open PR in no stack, run
`gh stack link --base <bottom PR's base> <PR or branch>...`, bottom to top; without `--base`,
`link` retargets the bottom PR to the default branch. `gh stack link --open <stack-number> <branch>`
appends a layer, ready for review, to an existing stack.

GitHub refuses, in a native stack:

- `gh pr merge` on any PR: land with `gh stack merge`
- a draft in `gh stack merge`: pass `--open` to `submit` or `link`
- `gh pr edit --base` on any PR: run `gh stack unstack <stack-number>` first, which keeps the PRs
  and branches, retarget, then relink with `gh stack link --base <trunk> <PRs bottom to top>` when
  the stack should stay. GitHub refuses the unstack once a PR of the stack merged

## Plain stack

Use git and `gh pr` only, no `gh stack` command, so GitHub never groups the PRs.

1. Branch each layer from the one below, commit, and push it. Open its PR with
   `gh pr create --base <layer below>`, or `--base <trunk>` for the bottom one
2. To change a layer, commit on it, then run `git rebase --update-refs <layer> <top>`, which
   replays the layers above and moves their branches, except one checked out in another worktree.
   When you amended or rebased the layer instead, run
   `git rebase --update-refs --onto <layer> <its old tip> <top>`. To take in the trunk, run
   `git fetch <remote>` and `git rebase --update-refs <remote>/<trunk> <top>`. Push each moved
   branch with `git push --force-with-lease <remote> <branch>...`, or follow
   [Force pushes](#force-pushes). Done when the stack is consistent

## Force pushes

`gh stack submit`, `sync`, `push`, and `rebase` rewrite or force-push layers, with
`--force-with-lease`. When a rule says to ask before any force push and a layer is already on the
remote, add commits instead: commit on the owning layer and run `git push <remote> <layer>`. Then,
for each layer above, bottom to top, run `git switch <upper>`, `git merge --no-ff --no-edit <layer
below>`, and `git push <remote> <upper>`. To take in the trunk, merge `<remote>/<trunk>` into the
bottom layer the same way, instead of `sync` or a rebase.

## Land

Done when `gh pr view <number> --json state` prints `MERGED` for every PR of the stack.

- **The project merges through GitHub:** in a native stack, `gh stack merge <PR> --yes --squash`
  lands that PR and every unmerged PR below it, all or nothing; a stack number lands the whole
  stack. Pass the method each time, since the last one used is reused otherwise. A plain stack
  lands with the project's merge command, one PR at a time from the bottom: before each next PR,
  run `gh pr edit <next> --base <trunk>` and bring it up to date with the trunk
- **The project merges by pushing a head to its trunk:** in a native stack, first run
  `gh stack unstack <stack-number>`. Then retarget every PR to the trunk, bottom to top, with
  `gh pr edit <number> --base <trunk>`, push every layer you rebased, and apply the project's method
  once to the top layer. A PR turns `MERGED` when its head on GitHub reaches its base. When GitHub
  refuses the unstack, apply the method, then, for each PR still open, bottom to top, run
  `git push <remote> <layer>:refs/heads/<layer below>`, a fast-forward that marks it merged

## Recovery

- **Exit 3, a rebase conflict:** after `gh stack rebase`, resolve the files, run `git add`, then
  `gh stack rebase --continue`, or `--abort` to restore every layer. After `gh stack sync`, the
  stack is already restored: run `gh stack rebase` to replay the conflict
- **Exit 9:** stacked PRs are off for the repository; use a plain stack
- **`Sync aborted`, the local and GitHub stacks diverged:** keep GitHub's with
  `gh stack unstack --local` and `gh stack checkout <stack-number>`, or keep the local one with
  `gh stack unstack` and `gh stack submit --auto --open`
- **Reorder or drop a layer:** rewrite the branches with git, then run `gh stack unstack` and
  `gh stack init --base <trunk> <branches bottom to top>`, which adopts them
- **Another exit code:** read stderr, then the
  [CLI reference](https://github.github.com/gh-stack/reference/cli/)
