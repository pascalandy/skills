---
name: "gh-stack"
description: "Manages stacked PRs and splits multi-part work into reviewable branches with gh-stack. Use for stack creation, viewing, edits, push, submit, sync, rebase, merge, or checkout; when asked to split or isolate work for review; whenever a user mentions a stack, branch layers, dependent PRs, or gh stack; or when a stack is checked out."
kind: "dev"
metadata:
  author: "github"
  version: "0.1.0"
---

# gh-stack

`gh stack` is a [GitHub CLI](https://cli.github.com/) extension for stacked branches and pull
requests. A stack is an ordered chain of branches rooted on a trunk, where each branch, a layer,
has one PR based on the layer below it, so a reviewer sees only that layer's diff.

`gh stack` prints a stack trunk-first, left to right:

```
(main) <- auth <- api <- frontend
```

Left is the **bottom**, right is the **top**. `auth` is based on `main` and merges first;
`frontend` merges last. `up` moves toward the top, away from trunk; `down` moves toward it.

## Prerequisites

Run each check before the first `gh stack` command. Done when every check passes, or you took the
path its failure names.

| Check | When it fails |
|---|---|
| `gh auth status --active --hostname github.com` | [Without gh stack](#without-gh-stack) |
| `gh stack --version` | `gh extension install github/gh-stack`, then check again |
| `git remote` prints a remote | [Without a remote](#without-a-remote) |
| `git remote` prints one remote, or `git config remote.pushDefault` is set | `git config remote.pushDefault <name>`, or pass `--remote <name>` to `push`, `submit`, `sync`, `rebase`, and `link` |

Use that selected remote for every fetch, branch base, and push below. `<remote>` names it;
the examples use `origin`.

Once per clone, `git config rerere.enabled true` makes a rebase reuse conflict resolutions.

## Pick the path

- **The layers would touch the same lines, or the change cannot land in parts:** open one PR, no
  stack
- **Multi-part work with no stack yet:** [Start a stack](#start-a-stack)
- **A change belongs to a layer of an existing stack:** [Change a layer](#change-a-layer)
- **The trunk moved:** [Sync](#sync)
- **The stack is approved:** [Land](#land)

## Non-interactive use

`gh stack` branches on whether **stdout is a TTY**. Piped, most commands error cleanly or print
static text; under a PTY the same commands open a prompt or a full-screen TUI and block forever.
Agent harnesses differ, so always pass the flags below instead of relying on that detection.

| Always run | Never run bare | Why |
|---|---|---|
| `gh stack view --json` | `gh stack view` | opens a TUI under a PTY |
| `gh stack submit --auto` | `gh stack submit` | prompts for a title per new PR |
| `gh stack merge <target> --yes` | `gh pr merge` | GitHub refuses it for any PR in a stack |
| `gh stack init <branch>...` | `gh stack init` | prompts for branch names |
| `gh stack add <branch>` | `gh stack add` | prompts for a name, and fails even when piped |
| `gh stack checkout <target>` | `gh stack checkout` | opens a selection menu |
| `gh stack up` / `down` / `top` / `bottom` | `gh stack switch` | `switch` is menu-only |
| — | `gh stack modify` | TUI-only, no non-interactive path |

`view --short` is safe in both modes, but it is formatted for humans. Use `--json` to parse.

## Start a stack

Create the stack before writing any file, so each concern lands in its own layer. Read
`references/stack-design.md` to choose the layers.

1. Branch the bottom layer from the remote trunk. The local trunk can lag it, for example when
   another worktree has it checked out. Run `git fetch <remote>`, `git switch -c <bottom>
   <remote>/<trunk>`, then `gh stack init <bottom>`, which adopts the branch. Done when
   `git merge-base --is-ancestor <remote>/<trunk> <bottom>` succeeds
2. Commit the bottom layer's concern. For each next layer, run `gh stack add <branch>`, which
   branches from the current layer, and commit its concern there. Done when each layer holds one
   concern and `gh stack view --json` lists them bottom to top
3. Open the PRs with `gh stack submit --auto --open`: it pushes every layer and opens one PR per
   layer, ready for review. Open a lower layer's PR early, for CI, the same way: `gh stack merge`
   lands only PRs in a stack on GitHub, which `submit` creates, and refuses drafts. `--auto` writes the
   titles and bodies; set them with `gh pr edit <number>`. Done when `gh stack view --json` shows a
   `pr` on every layer

```bash
git fetch origin && git switch -c auth origin/main && gh stack init auth
git add ... && git commit -m "Add auth middleware"
gh stack add api
git add ... && git commit -m "Add API routes"
gh stack submit --auto --open
gh stack view --json
```

## Change a layer

1. Check out the layer that owns the change: run `gh stack view --json`, and
   `git log --all -- <path>` when ownership is unclear. Done when you are on the owning layer,
   which is often not the top
2. Commit the change there
3. Bring the change into every layer above. `gh stack rebase --upstack` can rewrite the changed
   layer itself as well as those above, so choose by whether any of them is on the remote:
   - **None is on the remote, or the session allows force pushes:** run
     `gh stack rebase --upstack`, then `gh stack push`, which force-pushes the rewritten layers
     with `--force-with-lease`. A rebase restamps each commit's committer from git config, so
     check `git log --format='%h %ce'` before pushing when the repository requires an email
   - **One is on the remote, and a rule says to ask before any force push:** run
     `git push <remote> <layer>`. Then, for each layer above, bottom to top, run
     `git switch <upper>`, `git merge --no-ff --no-edit <layer below>`, and
     `git push <remote> <upper>`. Every push is a fast-forward

   Done when `git merge-base --is-ancestor <lower> <upper>` succeeds for each pair of adjacent
   layers from the changed one up, and the remote holds every layer you changed

```bash
gh stack down                   # or: gh stack checkout api
git add ... && git commit -m "Add get-user endpoint"
gh stack rebase --upstack       # replay every layer above onto the change
gh stack push
gh stack top                    # return to where you were
```

## Sync

`gh stack sync` fetches, rebases the stack onto the remote trunk, pushes, and refreshes PR state.
`gh stack sync --prune` also deletes local branches of merged PRs; pruning never happens without
`--prune` when non-interactive. `sync` can exit 0 even when a push failed, so check the result
yourself. Done when, after `git fetch <remote>`, `git merge-base --is-ancestor <remote>/<trunk>
<bottom>` succeeds and `git rev-parse <layer> <remote>/<layer>` prints the same commit twice for
every layer.

- **Local and remote stacks diverged:** `sync` prints both chains, makes no changes, and exits 0
  with `Sync aborted`. Read `references/troubleshooting.md`
- **Another worktree holds the trunk:** `gh stack rebase` warns `Could not update local <trunk>`,
  rebases the stack onto `<remote>/<trunk>`, and leaves that worktree untouched. The warning needs
  no action
- **A rule says to ask before any force push:** `sync` rewrites pushed layers. Run
  `git fetch <remote>` and `git merge --no-edit <remote>/<trunk>` on the bottom layer instead, then
  carry it up as in [Change a layer](#change-a-layer), step 3

## Land

On a layer of a stack tracked locally, so `gh stack view --json` succeeds, `gh stack merge --yes`
merges the whole stack without a number. After `gh stack link`, which tracks nothing locally, pass
the top PR's number. A bare number is read as a stack number first, then as a PR number: a PR
number merges that PR and every unmerged PR below it.

```bash
gh stack merge --yes --squash    # the current stack; or --merge, --rebase, --merge-method
gh stack merge 42 --yes          # PR #42 and every unmerged PR below it
```

- **All-or-nothing:** if any PR in the set cannot merge, none do
- **Squash:** with GitHub's default squash setting, a PR with one commit lands under that commit's
  subject, not the PR title. Before `--squash`, amend the commit or retitle the PR so they match
- **Method:** without a method flag, the last-used method is reused. A merge queue on the base
  branch queues the stack instead, picks the method, and ignores any method flag with a warning;
  queued PRs may land in separate groups

Done when `gh pr view <number> --json state` prints `MERGED` for every PR in the stack.

## Without gh stack

When `gh` is missing or not signed in, build the stack by hand: one branch per layer, each
branched from the layer below, and each PR opened with the layer below as its base, through
whatever forge tool the session has. Replace `gh stack rebase` with
`git rebase --onto <layer below> <its old tip> <branch>` for each layer above a change, which
replays only that branch's own commits. Replace `gh stack push` with
`git push --force-with-lease <remote> <branch>...`, naming the layer you changed and every layer you
rebased; when a rule says to ask before any force push, merge upward as in
[Change a layer](#change-a-layer), step 3. Done when each layer's PR targets the layer below.

## Without a remote

`gh stack rebase` needs a remote: without one, it fails with `no remotes configured` and leaves
the layers above unchanged. Restack with `git rebase --update-refs <changed layer> <top>`, which
replays the layers above and moves each of their branches. It skips a layer checked out in another
worktree: check that layer out here first, or restack from its worktree. Done when
`git merge-base --is-ancestor <lower> <upper>` succeeds for each pair of adjacent layers from the
changed one up.

## Reading state

`gh stack view --json` writes JSON to **stdout**. Status messages go to **stderr**; branch on exit
codes instead of parsing them.

```
trunk           string
currentBranch   string
branches[]      name, base, isCurrent, isMerged, isQueued, needsRebase
branches[].pr   number, url, state ("OPEN" | "MERGED" | "QUEUED"); absent when no PR exists
```

No field holds a branch's tip; read it with `git rev-parse <name>`. `base` is the saved SHA of the
parent branch that this branch was last known to contain. It may be older than the parent's
current tip. `needsRebase` is true when the current parent tip is no longer an ancestor of the
branch.

## Exit codes

| Code | Meaning | Recovery |
|---|---|---|
| 0 | Success | — |
| 1 | Generic error | Read stderr |
| 2 | Not in a stack | `gh stack init`, or `gh stack checkout <target>`; for open PRs never linked, `gh stack link <pr>...` bottom to top |
| 3 | Rebase conflict | Follow the Exit 3 recovery below |
| 4 | GitHub API failure | Run `gh auth status`: signed in, retry; signed out, follow [Without gh stack](#without-gh-stack) |
| 5 | Invalid arguments | Fix the invocation; see `<command> --help` |
| 6 | Disambiguation required | Branch is in several stacks; check out a non-shared branch |
| 7 | Rebase already in progress | `gh stack rebase --continue` or `--abort` |
| 8 | Stack file locked | Another `gh stack` process is writing; retry after ~5s |
| 9 | Stacked PRs unavailable | Not enabled on the repository; tell the user |
| 10 | Modify recovery required | `gh stack modify --abort` |

**Exit 3 recovery:**

- After `gh stack rebase`: resolve the files, run `git add`, then
  `gh stack rebase --continue`; use `gh stack rebase --abort` to restore the stack.
- After `gh stack sync`: the stack has already been restored. Run `gh stack rebase` to recreate the
  conflict, then resolve and continue as above.

## Constraints

- Stacks are strictly linear: one parent, at most one child. Use separate stacks for parallel work.
- There is no non-interactive reorder or removal. Errors may suggest `gh stack modify`, but it is
  TUI-only; restructure with `unstack`, then `init`, instead.
- `checkout <pr>` cannot be forced when a different local stack already covers those branches. Run
  `gh stack unstack --local` first, which keeps the stack on GitHub, then retry.

## More detail

`gh stack <command> --help` is authoritative for flags and arguments. `gh stack help <command>`
prints the top-level help instead.

Open the reference whose trigger matches the task; no need to preload all three.

- `references/stack-design.md`: read before creating a stack, when deciding how many layers to
  use, what belongs in each one, or whether work belongs in a new stack.
- `references/commands.md`: read when a command fails unexpectedly or you need its preconditions,
  side effects, atomicity, or ordering guarantees.
- `references/troubleshooting.md`: read on a rebase conflict, after a squash-merge, on local and
  remote divergence, when restructuring a stack, or when driving stacks from another tool.
