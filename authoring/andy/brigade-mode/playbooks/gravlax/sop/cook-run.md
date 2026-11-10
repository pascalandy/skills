# cook-run

Follow Implement, Docs, loop 2 under Loops and Proof in process order, then [cook-closing](cook-closing.md). Run Fix, Changed scope or Stop when their trigger arrives. Report to the Head Chef with `t3_thread_send`. Apply [Statuses, Messages and Decisions](../gravlax.md#statuses) at phase entry and turn end.

## Solo recipe

Each step runs the solo skill it names. These brigade rules override those skills:

- Ask the Head Chef with `t3_thread_send` and show ⏸️ until it answers. Never use a question tool such as AskUserQuestion
- The merge rule in [Decisions](../gravlax.md#decisions) replaces 🧰 full-send's merge gate, and [cook-closing](cook-closing.md) replaces its Merge step. From full-send, use only Proof and its babysit step; the loops replace its codex-loop step and [Report](../gravlax.md#report) replaces its report
- Between rounds, follow [Fix](#fix) instead of review-loop's local-only restriction
- [Shared rules](../gravlax.md#shared-rules) set one PR per card, layer ownership and the repository's `AGENTS.md` first

## Implement

1. Show 🍳. For each card, in the Plan's order:
   - For a bug card, run 🧰 diagnose before reading source code. Send its one question for Pascal to the Head Chef and show ⏸️ until the answer comes
   - With 🧰 label-for-issues, set the card to `1-wip-by-agent`. When an Epic's first card starts, set its Epic to `1-wip-by-agent` too. Read the labels back
   - Implement the card with 🧰 poteto-mode on a new layer with 🧰 gh-stack. Name each layer above your worktree's branch `<branch>-<concern>`, where `<branch>` is the branch the Head Chef created for you. Run the checks for other machines as [Decisions](../gravlax.md#decisions) tells. Apply shared Model selection for delegated side work. Copy the side delegate's title from Roles word for word
   - Run 🧰 2nd-pass, commit, push and open the card's PR with 🧰 file-pr. Link it with `link_pull_request` and own its `watch_pull_request`, unless oem's no-checks rule applies. Renew an ended watch or reconcile the PR state when registration fails
   - Run loop 1 on that PR as [Loops](#loops) says, until it ends. Only then start the next card

   Done when every card has its PR, the evidence for each acceptance criterion, green checks and an ended loop 1, or is reported blocked with its reason
2. File worthwhile out-of-scope gaps with 🧰 label-for-issues after checking duplicates; record the rest. Proceed to Docs; in fast track, skip each loop 1, do Release content, then Proof. Done when the checkout is clean and pushed

## Loops

Both loops use 🧰 review-loop's budget, early stop, ledger and dispute rule. [Approval](../gravlax.md#approval) governs review coverage and reruns. Loop 1 starts on each PR in Implement and Docs; loop 2 starts after Docs on what will merge together. The immutable subjects below replace review-loop's checkout-based code subject.

1. Select `[loop-1]` or `[loop-2]` with shared Model selection. This selection is review-loop's reviewer and replaces its loader skill. Done when the target is supported
2. Set the subject:
   - Loop 1: base SHA at the layer below, or trunk for the first card, and head SHA of this PR. Lower layers are context
   - Loop 2: base SHA at the trunk merge base and head SHA at the stack top

   Done when both literal SHAs and covering checks are recorded
3. Delegate each round with `delegate_task`, `isolation: "worktree"`, `mode: "async"`, `role: "review"`, the title `👀 loop-<n> · Cook <b>.1 <id4>` and `clientRequestId: <id4>-<b>.1-loop-<n>-<k>`, where `<k>` counts this Cook's delegations from 1 without resetting. Reuse the key only to retry that call. Retain each taskId and follow its `next`. The brief uses review-loop's round 1 contract and severity definitions, with this subject and these additions. Done when the round has a taskId

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

4. Answer each round's findings as review-loop says, through [Fix](#fix). "The user" in review-loop is the Head Chef: send a dispute with both sides and apply its decision under [Decisions](../gravlax.md#decisions). Done when every finding has a ledger outcome
5. Record each loop's rounds, reviewer, ledger and end in Detail. For any end other than APPROVE, continue to Proof and the merge gate with the Head Chef's decision or the remaining doubt. Done when the loop's end is recorded

Each isolated round reads its recorded SHAs, so both loops can run at once. Apply fixes after their active rounds return. A failed or interrupted round is not approval: read its thread with `t3_thread_read` using its `childThreadId`, cancel it, confirm it stopped and start a fresh round with the ledger. An isolation failure goes to the Head Chef for repair.

## Docs

1. Run 🧰 andy-mode ; docs on the final diff. Place each doc change as [Decisions](../gravlax.md#decisions) tells and use [Approval](../gravlax.md#approval) for review coverage. If no doc changes, record the no-docs decision for loop 2. Done when every affected doc matches the behavior or the report explains the no-docs decision
2. Do Release content. Run loop 1 on each PR this step opened, such as a top docs PR or the release-content layer, then run loop 2. Done when docs and required release content are pushed, every PR has an ended loop 1 and loop 2 has ended

## Release content

For `Release: yes`, add the repository's required release content, such as `CHANGELOG.md`, as the final stack layer. Done when the assigned release content is pushed or `Release: no` applies.

## Proof

1. Prove every acceptance criterion on the current heads with 🧰 full-send Proof. Paste each criterion's evidence untruncated into its PR and read it back, preserving its signature. On each final head, post required owner statuses with the repository's bare recipe, such as `just signoff`. Take an unresolved requirement, including a failing layer the Plan forbids changing, to Decisions. Done when each criterion's evidence is in its PR and each owner status is posted or its unresolved requirement is with the Head Chef
2. Babysit every PR with 🧰 babysit-pr, triaging wakes under [Watch findings](#watch-findings). Then follow [cook-closing](cook-closing.md). Done when bots have finished, findings have recorded outcomes, and required checks pass or an unconfirmed check has gone to the Head Chef under Decisions

## Watch findings

Treat a CI failure or conflict as a finding to fix. Judge an external review as 🧰 babysit-pr says. Queue watch findings while a loop round runs, then triage them after it; otherwise triage them at once. Fix accepted findings through [Fix](#fix). Done when every watch wake has a recorded decision.

## Fix

1. Show 🍳. If `🍽️ Batch ready` was sent, send `Readiness withdrawn`. Apply accepted findings using shared layer ownership. For a finding on a PR description, edit that PR without a commit. Run 🧰 2nd-pass, commit fixes in their layers, then restack and push with 🧰 gh-stack. Done when each accepted finding is pushed or its PR edit is verified, or reported blocked to the Head Chef
2. Rerun affected checks once per set of accepted findings: push every fix of the set first, then run the checks on the top head of the stack, which holds every layer. Keep any check the repository requires on each head or at an intermediate step. Run independent checks in parallel worktrees unless the repository forbids it. When a fix changes code or another input that the repository's Verify runs or reads, such as a prompt, an output, an exit code, an assertion, a fixture or the command, rerun that Verify at the new heads, even when you expect the same end states. Rerun it as well when you cannot tell. Copy the side delegate's title from Roles word for word. A fix outside those inputs, such as docs or comments, keeps the existing evidence: name in the Detail the tested heads and the changes the evidence does not cover. If Docs already ran, refresh any newly stale docs. Done when the checks cover the new stack
3. Apply [Approval](../gravlax.md#approval) to the new heads, including after a failed merge or `⏳ Rework`: when it sends a change back, start at once loop 1 on each changed PR and, once loop 2 has started, its next round. Fast track keeps its recorded skip. Then return to Proof. Done when each loop has the coverage or recorded end the merge gate needs

## Changed scope and reporting

- On `⏹️ Cut <card>`, drop the card and report the reduced scope. If no cards remain, follow [cook-closing Closing](cook-closing.md#closing), which ends at ⏹️. Done when no cut card remains in the stack
- On fast track during a run, let an active loop round finish or cancel it, then do Release content and Proof after implementing the remaining work. Done when no skipped loop or docs step still runs

## Stop

1. Finish a merge or release already running and record its result. Done when no merge or release runs
2. Show 🧹. Cancel running delegates with `task_cancel` and wait for cancellation to complete; unwatch every PR with `unwatch_pull_request`. Once each cancelled delegate has stopped, clean up its worktree, any T3 branch and temporary folders as [Work folders](../gravlax.md#work-folders) says. Done when no delegate can still access them and no watch remains
3. Stop on a clean, pushed checkout and record your branches and heads in your Detail. Follow [cook-closing Closing](cook-closing.md#closing). Done when the Head Chef received the preserved work and you are settled
