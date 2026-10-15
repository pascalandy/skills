# cook-implement

Follow Implement, the review pairs, Docs and Ready in process order. Run Fix, Stop or Retros when their trigger arrives.

## Implement

1. Implement every assigned card under the shared rules, commit as you go and open the PRs. Apply shared Model selection for delegated side work. Obtain the Chef's approval before touching another Cook's file group. Done when every card is implemented with green checks, or reported blocked with its reason
2. Link each PR with `link_pull_request` as you open it and own its `watch_pull_request`, unless oem's no-checks rule applies. Route CI failures and external reviews through `cook-review`. File worthwhile out-of-scope gaps with 🧰 label-for-issues after checking duplicates; record the rest. Done when every PR is linked and watched or has its no-checks decision recorded
3. Run 🧰 2nd-pass and push. Proceed to the first review pair; in fast track, do Release content, then Ready. Done when the checkout is clean and pushed

## Fix

1. Fix accepted findings in their owning layers. Run 🧰 2nd-pass, restack with 🧰 gh-stack and push. Done when each accepted finding is fixed or reported blocked to the Chef
2. Rerun affected checks; if Docs already ran, refresh any newly stale docs. Return to `cook-review` for the passes the changes invalidate. If the Chef reopened a rejection, requested a restack on `main` or returned a failed merge, follow the same loop, then Ready. Fast track retains its skips. Done when readiness covers the new stack

## Docs

1. Run 🧰 andy-mode ; docs on the final diff. If docs change, commit them and open a PR at the top of the stack; otherwise record the no-docs decision for manic-3. Done when every affected doc matches the behavior or the report explains the no-docs decision
2. Do Release content, then proceed to manic-3 plus manic-5. Done when docs and required release content are in the review scope

## Release content

For `Release: yes`, add the repository's required release content, such as `CHANGELOG.md`, as the final stack layer before Ready. With parallel Cooks, the Chef names the last Cook to own it. Done when the assigned release content is pushed or `Release: no` applies.

## Ready

1. Confirm a clean, pushed checkout and review completion, or the fast-track skips. Send `🚦 Stack ready` to the Chef with the shared Report. Done when the Chef has the readiness report
2. Freeze the worktree: no commit, checkout, restack or push until the Chef says `merged` or returns it to you. Forward watch wakes to the Chef during this freeze, distinguishing findings from wakes reporting only passing checks. A returned worktree goes through Fix and a fresh 🚦 before merging. Done when the Chef has acknowledged the handoff or returned ownership

## Stop

1. Cancel running delegates with `task_cancel` and wait for cancellation to complete; unwatch every PR with `unwatch_pull_request`. Remove each cancelled barrage's detached worktree and work folder once it has stopped. Done when no delegate can still access them and no watch remains
2. Stop on a clean, pushed checkout; report your branches and heads to the Chef, then settle with 🧰 t3-runtime. Done when the Chef has the preserved work and you are settled

## Retros

Run the retros the Chef requests, report issue links or the no-findings result, remove any remaining watches and settle with 🧰 t3-runtime. Done when the Chef has the results and you are settled.
