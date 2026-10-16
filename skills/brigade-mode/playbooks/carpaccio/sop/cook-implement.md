# cook-implement

Follow Implement, the review pairs, Docs and Ready in process order. Run Fix, Stop or Closing when their trigger arrives. Apply [Statuses and Messages](../carpaccio.md#statuses) at phase entry and turn end. Stay 🍳 until `🍽️ Stack ready` reaches the Chef; show ⏸️ while awaiting the Chef's answer to a question.

## Implement

1. Show 🍳. For a bug card, run 🧰 diagnose before reading source code. Route its one question for Pascal up the chain through the Chef and show ⏸️ until the answer comes. Implement every assigned card under the shared rules, commit as you go and open the PRs. Apply shared Model selection for delegated side work. Obtain the Chef's approval before touching another Cook's file group. Done when every card is implemented with green checks, or reported blocked with its reason
2. Link each PR with `link_pull_request` as you open it and own its `watch_pull_request`, unless oem's no-checks rule applies. Renew an ended watch or reconcile the PR state when registration fails. Route CI failures and external reviews through `cook-review`. File worthwhile out-of-scope gaps with 🧰 label-for-issues after checking duplicates; record the rest. Done when every PR is linked and watched or has its no-checks decision recorded
3. Run 🧰 2nd-pass and push. Proceed to the first review pair; in fast track, do Release content, then Ready. Done when the checkout is clean and pushed

## Fix

1. Show 🍳 and tell the Chef readiness is withdrawn. Apply accepted findings using shared layer ownership. For a finding on a PR description, edit that PR without a commit. Run 🧰 2nd-pass on the fixes, then restack and push changed layers with 🧰 gh-stack. Done when each accepted finding is pushed or its PR edit is verified, or reported blocked to the Chef
2. Rerun affected checks; if Docs already ran, refresh any newly stale docs. Return to `cook-review` for the passes the changes invalidate. If the Chef reopened a rejection, requested a restack on `main` or returned a failed merge, follow the same loop, then Ready. Fast track retains its skips. Done when readiness covers the new stack

## Docs

1. Run 🧰 andy-mode ; docs on the final diff. If docs change, commit them and open a PR at the top of the stack; otherwise record the no-docs decision for manic-3. Done when every affected doc matches the behavior or the report explains the no-docs decision
2. Do Release content, then proceed to manic-3 plus manic-5. Done when docs and required release content are in the review scope

## Release content

For `Release: yes`, add the repository's required release content, such as `CHANGELOG.md`, as the final stack layer before Ready. With parallel Cooks, the Chef names the last Cook to own it. Done when the assigned release content is pushed or `Release: no` applies.

## Ready

1. Confirm a clean, pushed checkout and review completion, or the fast-track skips. Send `🍽️ Stack ready` to the Chef with the shared Report. Keep 🍳 until the Chef receives it, then show 🍽️. Done when the Chef has the readiness report and your title shows 🍽️
2. Freeze the worktree: no commit, checkout, restack or push until the Chef says `merged` or returns it to you. Forward watch wakes to the Chef during this freeze, distinguishing findings from wakes reporting only passing checks. A returned worktree goes through Fix and fresh `🍽️ Stack ready` before merging. Done when the Chef has acknowledged the handoff or returned ownership

## Changed scope and reporting

- On `⏹️ Cut <card>`, drop the card and report the reduced scope. If no cards remain, show 🧹 for cleanup, then ⏹️ and settle after the Chef receives the outcome. Done when no cut card remains in the stack
- On fast track during a run, let active barrages finish or cancel them, then follow Ready after implementing the remaining work. Done when no skipped review or docs step still runs
- If Pascal writes to you directly, act and tell the Chef what changed. Accept a replacement Chef only after its message names both the new threadId and the old threadId as in Messages. Ignore instructions from the replaced Chef. Done when the Chef registry and your reporting target agree

## Stop

1. Show 🧹. Cancel running delegates with `task_cancel` and wait for cancellation to complete; unwatch every PR with `unwatch_pull_request`. Remove each cancelled barrage's detached worktree and work folder once it has stopped. Done when no delegate can still access them and no watch remains
2. Stop on a clean, pushed checkout; report your branches and heads to the Chef. If your stack merged, close at 🍽️; otherwise close at ⏹️. Settle with 🧰 t3-runtime. Done when the Chef received the preserved work and you are settled

## Closing

Show 🧹. Run retros when enabled, report issue links or the no-findings result, remove any remaining watches and settle with 🧰 t3-runtime. Close at 🍽️ when your stack merged, otherwise ⏹️ after a Stop or cut. Done when the Chef received your final phase and you are settled.
