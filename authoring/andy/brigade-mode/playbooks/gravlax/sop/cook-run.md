# cook-run

Follow Implement, Docs, loop 2 under Loops and Proof in process order, then [cook-closing](cook-closing.md). Run Fix, Changed scope or Stop when their trigger arrives. Report to Head Chef with `t3_thread_send`. Apply [Statuses, Messages and Decisions](../gravlax.md#statuses) at phase entry and turn end.

## Solo recipe

Each step runs the solo skill it names. Brigade rules below override those skills:

- Ask Head Chef with `t3_thread_send`; show ⏸️ until it answers. Never use a question tool, e.g. AskUserQuestion
- Merge rule in [Decisions](../gravlax.md#decisions) replaces 🧰 full-send's merge gate; [cook-closing](cook-closing.md) replaces its Merge step. From full-send, use only Proof and its babysit step; loops replace its codex-loop step, [Report](../gravlax.md#report) replaces its report
- Between rounds, follow [Fix](#fix) instead of review-loop's local-only restriction
- [Shared rules](../gravlax.md#shared-rules) set one PR per card, layer ownership and repository's `AGENTS.md` first

## Implement

1. Show 🍳. For each card, in Plan's order:
   - Bug card: run 🧰 diagnose before reading source code. Send its one question for Pascal to Head Chef; show ⏸️ until answer comes
   - With 🧰 label-for-issues, set card to `1-wip-by-agent`. When an Epic's first card starts, set its Epic to `1-wip-by-agent` too. Read labels back
   - Implement card with 🧰 poteto-mode on a new layer with 🧰 gh-stack. Name each layer above your worktree's branch `<branch>-<concern>`, `<branch>` = branch Head Chef created for you. Run checks for other machines as [Decisions](../gravlax.md#decisions) tells. Apply shared Model selection for delegated side work. Copy side delegate's title from Roles word for word
   - Run 🧰 2nd-pass, commit, push, open card's PR with 🧰 file-pr. Link it with `link_pull_request` and own its `watch_pull_request`, unless oem's no-checks rule applies. Renew an ended watch or reconcile PR state when registration fails
   - Run loop 1 on that PR as [Loops](#loops) says, until it ends. Only then start next card

   Done when every card has its PR, evidence for each acceptance criterion, green checks and an ended loop 1, or is reported blocked with its reason
2. File worthwhile out-of-scope gaps with 🧰 label-for-issues after checking duplicates; record the rest. Proceed to Docs; in fast track, skip each loop 1, do Release content, then Proof. Done when checkout is clean and pushed

## Loops

Both loops use 🧰 review-loop's budget, early stop, ledger and dispute rule. [Approval](../gravlax.md#approval) governs review coverage and reruns. Loop 1 starts on each PR in Implement and Docs; loop 2 starts after Docs on what will merge together. Immutable subjects below replace review-loop's checkout-based code subject.

1. Select `[loop-1]` or `[loop-2]` with shared Model selection. This selection is review-loop's reviewer and replaces its loader skill. Done when target is supported
2. Set subject:
   - Loop 1: base SHA at layer below, or trunk for first card, and head SHA of this PR. Lower layers are context
   - Loop 2: base SHA at trunk merge base, head SHA at stack top

   Done when both literal SHAs and covering checks are recorded
3. Delegate each round with `delegate_task`, `isolation: "worktree"`, `mode: "async"`, `role: "review"`, title `👀 loop-<n> · Cook <b>.1 <id4>` and `clientRequestId: <id4>-<b>.1-loop-<n>-<k>`, where `<k>` counts this Cook's delegations from 1, never reset. Reuse the key only to retry that call. Keep each taskId and follow its `next`. Brief uses review-loop's round 1 contract and severity definitions, with this subject and these additions. Done when round has a taskId

```text
Repo: your T3-prepared checkout of <repository>. Base: <sha>. Head: <sha>. Checks: <results>
Subject: git diff <base SHA> <head SHA>. Read surrounding files with git show <head SHA>:<path>.
Checkout: use only the checkout T3 prepared. It starts at the Cook's last local commit, <literal SHA>; detach it at Head to run code. Keep the Cook's worktree untouched.
Plan: <goal, every card's acceptance criteria and batch threat model>
Evidence: <evidence you claim for the acceptance criteria in the subject>
Docs: <doc layers, top docs PR or no-docs decision; loop 2 only>
Loop 1 ledgers: <each PR's loop 1 ledger; loop 2 only>
Angles: read <absolute playbook path>/sop/manic-1.md and sop/manic-2.md for loop 1, or sop/manic-3.md and sop/manic-5.md for loop 2, and review through each.
Probes: follow the package-copy rule in Rules.
Rules: <rules.md path, plus additions>. Read and follow it.
Work folder: <absolute path>
```

4. Answer each round's findings as review-loop says, via [Fix](#fix). "The user" in review-loop is Head Chef: send a dispute with both sides and apply its decision under [Decisions](../gravlax.md#decisions). Done when every finding has a ledger outcome
5. Record each loop's rounds, reviewer, ledger and end in Detail. Any end other than APPROVE: continue to Proof and merge gate with Head Chef's decision or remaining doubt. Done when loop's end is recorded

Each isolated round reads its recorded SHAs → both loops can run at once. Apply fixes after their active rounds return. Failed or interrupted round is not approval: read its thread with `t3_thread_read` using its `childThreadId`, cancel it, confirm it stopped, start a fresh round with the ledger. Isolation failure goes to Head Chef for repair.

## Docs

1. Run 🧰 andy-mode ; docs on final diff. Place each doc change as [Decisions](../gravlax.md#decisions) tells; use [Approval](../gravlax.md#approval) for review coverage. If no doc changes, record no-docs decision for loop 2. Done when every affected doc matches behavior or report explains no-docs decision
2. Do Release content. Run loop 1 on each PR this step opened, e.g. a top docs PR or release-content layer, then run loop 2. Done when docs and required release content are pushed, every PR has an ended loop 1 and loop 2 has ended

## Release content

For `Release: yes`, add repository's required release content, e.g. `CHANGELOG.md`, as final stack layer. Done when assigned release content is pushed or `Release: no` applies.

## Proof

1. Prove every acceptance criterion on current heads with 🧰 full-send Proof. Paste each criterion's evidence untruncated into its PR and read it back, keeping its signature. On each final head, post required owner statuses with repository's bare recipe, e.g. `just signoff`. Take an unresolved requirement, including a failing layer the Plan forbids changing, to Decisions. Done when each criterion's evidence is in its PR and each owner status is posted or its unresolved requirement is with Head Chef
2. Babysit every PR with 🧰 babysit-pr, triaging wakes under [Watch findings](#watch-findings). Then follow [cook-closing](cook-closing.md). Done when bots have finished, findings have recorded outcomes, and required checks pass or an unconfirmed check has gone to Head Chef under Decisions

## Watch findings

Treat CI failure or conflict as a finding to fix. Judge external review as 🧰 babysit-pr says. Queue watch findings while a loop round runs, triage them after it; otherwise triage at once. Fix accepted findings via [Fix](#fix). Done when every watch wake has a recorded decision.

## Fix

1. Show 🍳. If `🍽️ Batch ready` was sent, send `Readiness withdrawn`. Apply accepted findings using shared layer ownership. Finding on a PR description: edit that PR without a commit. Run 🧰 2nd-pass, commit fixes in their layers, then restack and push with 🧰 gh-stack. Done when each accepted finding is pushed or its PR edit is verified, or reported blocked to Head Chef
2. Rerun affected checks once per set of accepted findings: push every fix of the set first, then run checks on stack's top head, which holds every layer. Keep any check the repository requires on each head or at an intermediate step. Run independent checks in parallel worktrees unless repository forbids it. When a fix changes code or another input the repository's Verify runs or reads, e.g. a prompt, output, exit code, assertion, fixture or the command, rerun that Verify at new heads, even when you expect same end states. Rerun it too when you cannot tell. Copy side delegate's title from Roles word for word. A fix outside those inputs, e.g. docs or comments, keeps existing evidence: name in Detail the tested heads and the changes the evidence does not cover. If Docs already ran, refresh any newly stale docs. Done when checks cover the new stack
3. Apply [Approval](../gravlax.md#approval) to new heads, including after a failed merge or `⏳ Rework`: when it sends a change back, start at once loop 1 on each changed PR and, once loop 2 has started, its next round. Fast track keeps its recorded skip. Then return to Proof. Done when each loop has the coverage or recorded end the merge gate needs

## Changed scope and reporting

- On `⏹️ Cut <card>`, drop the card and report reduced scope. If no cards remain, follow [cook-closing Closing](cook-closing.md#closing), which ends at ⏹️. Done when no cut card remains in the stack
- On fast track during a run, let an active loop round finish or cancel it, then do Release content and Proof after implementing remaining work. Done when no skipped loop or docs step still runs

## Stop

1. Finish a merge or release already running and record its result. Done when no merge or release runs
2. Show 🧹. Cancel running delegates with `task_cancel`, wait for cancellation to complete; unwatch every PR with `unwatch_pull_request`. Once each cancelled delegate has stopped, clean up its worktree, any T3 branch and temp folders as [Work folders](../gravlax.md#work-folders) says. Done when no delegate can still access them and no watch remains
3. Stop on a clean, pushed checkout; record your branches and heads in your Detail. Follow [cook-closing Closing](cook-closing.md#closing). Done when Head Chef received the preserved work and you are settled
