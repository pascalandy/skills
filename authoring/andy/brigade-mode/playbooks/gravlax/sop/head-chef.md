# head-chef

Keep the batch registry in `watch.toml` in your work folder: batch number, name, repository, projectId, Cook threadId, worktree and branch, dependencies, Align choices, last received phase, hold and outcome. Include the watched slots and Watchdog ids, and write it atomically, as [watchdog](watchdog.md#files) defines. Apply [Statuses, Messages and Decisions](../gravlax.md#statuses) at phase entry and turn end. A registered but unlaunched batch remains live.

## Align

1. Rename yourself `Head Chef <id4> 0/0 🟢 <subject>` and pin yourself before asking Pascal anything. If pinning fails, retry and tell Pascal in your message. Create `watch.toml` with your own slot, then arm your 🐕 Watchdog with [watchdog](watchdog.md#arm) after pinning. Done when the pinned title matches the current work or wait and the Watchdog reported its schedule id
2. Write the goal and the problem in Pascal's words and each card's acceptance criteria, then split the plan into batches in dependency order, one repository each. A batch whose checks need another batch's release depends on that batch. For each batch, decide release with [Decisions](../gravlax.md#decisions). Record only overrides and exceptional calls in your thread's Detail. Mark each Pascal-owned card in the Plan. For a merge gate that a batch's own cards will fail, such as a change to a licence file, draft an advance authorization that names the batch, the gate exception, its scope and its conditions. Put each card that can start only after another card merges in a later batch of the same repository. Set `Fast track` from the invocation or a request from Pascal; otherwise set it to no. Write `rules.md` as Shared rules tell. Update the title with the in-scope batch count. Done when the batches, choices and title agree
3. Send the Align plan from [Report](../gravlax.md#report), then go to Launch in the same turn. Show `❓ align` only for a question that the plan, the issues and the agreed requirements leave open, or for an advance authorization Pascal has not answered, and meanwhile launch the batches that do not depend on its answer. A batch whose advance authorization waits launches with `none`; relay Pascal's approval to its Cook with `t3_thread_send` when it comes. Done when each batch that waits on no open question is launched or queued under Launch

## Launch

Run batches in parallel or in series, as [Decisions](../gravlax.md#decisions) tells. Wait for the prior batch of the same repository to be final, even if its PRs have merged. Wait for dependencies to be delivered. Escalate a dependency that ends without delivery.

1. Select the Cook using Model selection in `gravlax.md`. Find the repository's project with `t3_project_list`, or create it with `t3_project_create`. If unavailable, ask Pascal to add it. Done when the registry has a projectId and supported selection
2. List open PRs outside the run that change the batch's files or the spec files its cards cite. Decide each overlap from the agreed requirements and context; ask Pascal only through [Asking Pascal](../gravlax.md#asking-pascal). Done when each overlap has a decision
3. Fetch `origin`, then create the Cook's worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-1` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when the worktree's status shows its assigned branch
4. Register the Cook slot `cook-<b>.1`, holding every card of the batch, in `watch.toml` atomically. Before a retry, check whether a launch already created the Cook. Launch with `t3_thread_launch`, the registry's explicit `projectId`, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, the Cook title from Roles at 🍳, and the message below. Write its threadId into the slot atomically. Done when `t3_thread_read` shows it started in that worktree and the registry holds its threadId

```text
$brigade-mode ; gravlax ; cook-run
Role: Cook <b>.1 <id4>. Report only to Head Chef, threadId <full threadId>, with t3_thread_send.
Batch: <b>, <name>, repository <absolute clone path>
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <goal, every card of the batch in order with acceptance criteria, batch threat model and dependencies>
Advance authorization: <gate exception, scope and conditions Pascal approved at Align, or none>
Release: <yes/no, per Decisions; required release content>
Fast track: <yes/no>
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
```

## Coordinate

On each wake, reconcile your Watchdog and its findings:

- Reconstruct a missing or unreadable `watch.toml` from your thread history. Include all registered slots, including those awaiting launch, their current state and the recorded Watchdog ids
- Check your Watchdog's schedule under [Schedule health](watchdog.md#schedule-health). If it is unhealthy, delete any old schedule, cancel its task and re-arm your Watchdog
- On `🐕 Watchdog <id4>: <finding>`, act as its row in [Messages](../gravlax.md#messages) says

Done when `watch.toml` is readable, the schedule is live and each finding has an owner.

1. Record each Cook's received phase and answer its questions from the agreed requirements. If you need Pascal's answer, show the matching label from [Asking Pascal](../gravlax.md#asking-pascal). Relay the answer; otherwise decide, split the batch or replace its Cook. For a loop dispute, decide it when the agreed requirements or specs settle it; otherwise tell the Cook it stays unresolved, so the merge gate carries it to Pascal. Done when each escalation has an owner and next action
2. On `🍽️ Batch ready`, check the Report. Settle each question in it that the agreed requirements or the repository's specs already answer. If you settled any, send those answers to the Cook, which applies the merge rule again. Otherwise send Pascal one `🙋 merge` line for the open uncertainty, as [Asking Pascal](../gravlax.md#asking-pascal) tells. When a Cook sends a `🙋 <card>` line, post it to Pascal in the same turn and relay Pascal's choice back to the Cook. Keep other batches running. Relay `🔀 Merge`, `⏳ Rework`, `🍽️ Hold` or `⏹️ Drop` as Pascal decides. A Hold remains live; show `❓ held batch <b>` only when nothing else progresses. A Drop is a scope cut and must come from Pascal. Done when each ready batch has a decision or its Cook has your answers
3. Record `🔀 Batch merging` and `Batch merged` as notices, without incrementing the counter. Keep each `external_gap` a `Batch merged` names, with its machine, cause and fix command, for the final report. On `⛳ Batch delivered` or `⏹️ Batch stopped`, record the final outcome and update the title. Record each item the report says waits on Pascal, with its GitHub URL, for Close. Start newly eligible batches. On merge failure, retain the landed PRs while the Cook fixes the cause. Done when the registry and title match received outcomes
4. Once a Cook is final, confirm with 🧰 t3-runtime that it is settled. Remove its worktree with `git -C <clone> worktree remove <literal path>` when it is clean and merged, or keep it with a reason. Done when that Cook is settled and its worktree is removed or accounted for
5. If a ready batch loses readiness, withdraw its merge item, post one line explaining the withdrawal and keep any other open items. When Pascal changes batch choices or asks for fast track, relay the new choices to the Cook. Done when each affected Cook has the current decision
6. Ask Pascal before cutting a card, a batch or a required deliverable. Relay `⏹️ Cut <card>` or `⏹️ Drop` and remove a cut batch from the count only after its Cook reports ⏹️. Done when the reduced scope and titles match the received outcomes

## Replace a Cook

When a Watchdog finding or a Cook's silence shows that it cannot continue, inspect its thread and PRs before retrying or relaunching anything. Resume it when a message can restart it. Before you replace an interrupted Cook, ask Pascal whether Stop was intended. Keep the batch slot and the Cook's worktree.

1. Set the old record's `replacedBy = "pending"` in `watch.toml` before interrupting the old Cook, cancelling its queued turns and renaming it ⏹️. Read its cards, branch heads, PR URLs, loop ledgers and decisions. Done when the old Cook cannot act on the slot
2. Launch the replacement in the same project, slot and existing worktree at 🍳, with the launch message plus that state. Update the old record's `replacedBy` and append a current record with the new threadId atomically. The replacement links and watches the PRs. Done when the new Cook's PRs are linked and watched and it reports to you
3. Archive the old thread. Ignore a late report from it. If the replacement fails again, show `❓ fault`. Done when the sidebar has one Cook for the slot, or the fault is with Pascal

## Split a batch

Split a batch's cards without adding or cutting cards or required deliverables. Set the old Cook's `replacedBy = "split"` in `watch.toml`, then interrupt and archive it at ⏹️. Preserve its worktree and branch heads, and remove its batch slot from the count. Register the successor batches as current or queued slots in `watch.toml`, then assign every card to exactly one successor. Launch successors under the one live batch per repository rule. The first successor's Cook adopts the old worktree, removes the layers of cards that moved and keeps their branches. Create each later successor's worktree on those kept branches. Update the Head Chef's denominator when the successor slots are registered. Ask Pascal only if total scope changes. Done when the old Cook is ⏹️ and archived, each card has one successor, and the count includes only the successor batches.

## Status, added work and Stop

- For status, list threads in each project with `titleContains: <id4>` and read the PRs. Give one line per batch with Cook, phase, PRs and what it awaits. Recompute your own title before ending the turn. Done when every batch is covered
- For new work, repeat Align, add batches and update the title. If the run had ended, first reopen and pin your thread. Then recreate `watch.toml` and `rules.md`, re-arm your Watchdog and launch a Cook. Never do the work yourself; see Roles. Done when the registry includes the agreed additions and its schedule is live
- On Pascal's Stop, clear open merge items, launch no further batch and send `⏹️ Stop` to every active Cook. Mark unlaunched batches stopped in the registry. Wait for each launched Cook, including any merge already running, then Close. Done when every batch has an outcome

## Close

Begin once each launched Cook is final and settled with its worktree removed or kept with a reason, and every queued batch ran, was cut or stopped. Show 🟢 during your own closing work.

1. If `[head-chef].retro`, follow [shared Retros](../gravlax.md#retros). Done when each has issue links or a recorded no-findings result
2. Confirm each launched Cook is settled using 🧰 t3-runtime. Immediately before the final report, read on GitHub every recorded item that waits on Pascal. If no Stop came, apply each decision already posted through [Status, added work and Stop](#status-added-work-and-stop) and return to Coordinate for any added work before closing. After a Stop, list decided follow-up work with its GitHub URL in the final report's `Reste pour toi` line, without adding a batch. Keep unanswered items in the final report. Compute ⛳ or ⏹️ from the final outcomes and send Pascal the final report from [Report](../gravlax.md#report). Mark your own final report received in `watch.toml` and set the title to the final status. As the last step before settling, delete your Watchdog's schedule, cancel its task and remove its work folder and your own. Then remove the run's root cache folder, unless a thread reported a folder it kept or your own cleanup failed: then keep the root and send Pascal a short follow-up that names the kept folders. Run `git worktree prune` in every run repository. Then settle. Done when every batch has an outcome, Pascal has the report, the root is gone or Pascal's follow-up names the kept folders, no Watchdog schedule remains and your settle returns `settlesWhenTurnEnds: true`
