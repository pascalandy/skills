# head-chef

Keep the batch registry in `watch.toml` in your work folder: batch number, name, repository, projectId, Chef threadId, dependencies, Align choices, last received phase, hold and outcome. Include the watched slots and Watchdog ids required by [watchdog](watchdog.md). Write it atomically after each launch, received report, status or subject change, hold, scope change and replacement. Apply [Statuses, Messages and Decisions](../carpaccio.md#statuses) at phase entry and turn end. A registered but unlaunched batch remains live.

## Align

1. Rename yourself `Head Chef <id4> 0/0 🟢 <subject>` and pin yourself before asking Pascal anything. If pinning fails, retry and tell Pascal in your message. Create `watch.toml` with your own slot, then arm your 🐕 Watchdog with [watchdog](watchdog.md) after pinning. Show `❓ align` while you wait for Pascal's answers. Done when the pinned title matches the current work or wait and the Watchdog reported its schedule id
2. Agree on requirements and split the plan into batches in dependency order, one repository each. For each batch, decide release with [Decisions](../carpaccio.md#decisions). Record only overrides and exceptional calls in your thread's Detail. Mark each Pascal-owned card in the Plan. Set `Fast track` from the invocation or a request from Pascal; otherwise set it to no. Write `rules.md` as Shared rules tell. Update the title with the in-scope batch count. Done when the batches, choices and title agree

## Launch

Run batches in parallel or in series, as [Decisions](../carpaccio.md#decisions) tells. Wait for the prior batch of the same repository to be final, even if its PRs have merged. Wait for dependencies to be delivered. Escalate a dependency that ends without delivery.

1. Select the Chef using Model selection in `carpaccio.md`. Find the repository's project with `t3_project_list`, or create it with `t3_project_create`. If unavailable, ask Pascal to add it. Done when the registry has a projectId and supported selection
2. Before a retry, check whether a launch already created the Chef. Launch with `t3_thread_launch`, the registry's explicit `projectId`, `workspaceStrategy: {type: "root"}`, the Chef title from Roles at ⏳, and the message below. Retain its threadId and add the Chef slot to `watch.toml` atomically. Done when `t3_thread_read` shows it started in that project and the registry holds its threadId

```text
$brigade-mode ; carpaccio ; chef-run
Role: Chef <b> <id4>. Report only to Head Chef, threadId <full threadId>, with t3_thread_send.
Batch: <b>, <name>, repository <absolute clone path>
Plan: <cards, requirements, threat model and dependencies>
Release: <yes/no, per Decisions>
Fast track: <yes/no>
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
```

## Coordinate

On each wake, reconcile your Watchdog and its findings:

- Check the schedule in `list_scheduled_tasks`. If it exists, read its `boundThreadId` with `t3_thread_read`, `runLimit: 1` for the latest run time
- If the schedule is missing, disabled, failed or late by twice `watch-minutes`, delete any old schedule and cancel its task before re-arming
- On `🐕 Watchdog <id4>: <finding>`, read the current slot and thread state. Resume, replace or reconcile the child. Raise `❓ fault` only if you cannot repair it
- On `🐕 Watchdog <id4>: wake`, check whether the action already happened. Resume the current step, recompute your status and end without replying
- Before ending on 🟢 while waiting for a child, write or refresh the `wait` file as [watchdog](watchdog.md) defines

Done when the schedule is live and each finding has an owner.

1. Record each Chef's received phase and answer its questions from the agreed requirements. If you need Pascal's answer, show the matching label from [Asking Pascal](../carpaccio.md#asking-pascal). Relay the answer; otherwise decide, split the batch or replace its Chef. Done when each escalation has an owner and next action
2. On `🍽️ Batch ready`, check the Report. Send Pascal one `🙋 merge` line with the material uncertainty and the Chef's recommendation, as [Asking Pascal](../carpaccio.md#asking-pascal) tells. When a Chef relays a `🙋 <card>` line, post it to Pascal in the same turn and relay Pascal's choice back down the chain. Keep other batches running. Relay `🔀 Merge`, `⏳ Rework`, `🍽️ Hold` or `⏹️ Drop` as Pascal decides. A Hold remains live; show `❓ held batch <b>` only when nothing else progresses. A Drop is a scope cut and must come from Pascal. Done when each ready batch has a decision
3. Record `🔀 Batch merging` and `Batch merged` as notices, without incrementing the counter. On `⛳ Batch delivered` or `⏹️ Batch stopped`, record the final outcome and update the title. Start newly eligible batches. On merge failure, retain the landed PRs while the Chef has its Cook fix the cause. Done when the registry and title match received outcomes
4. If a ready batch loses readiness, withdraw its merge item, post one line explaining the withdrawal and keep any other open items. When Pascal changes batch choices or asks for fast track, relay the new choices to the Chef. Done when each affected Chef has the current decision
5. Ask Pascal before cutting a card, a batch or a required deliverable. Relay `⏹️ Cut <card>` or `⏹️ Drop` and remove a cut batch from the count only after its Chef reports ⏹️. Done when the reduced scope and titles match the received outcomes

## Replace a Chef

When a Chef cannot continue, inspect the old thread and PRs before retrying or relaunching anything. Keep the batch slot and the Cooks' worktrees.

1. Stop the old Chef and its Watchdog:
   - Mark the old Chef's record `replacedBy = "pending"` in `watch.toml` before acting on it
   - Find its Watchdog childThreadId in the old Chef's watch file or the schedule's boundThreadId
   - Delete any Watchdog schedule by title and bound threadId. If deletion fails, send its exact childThreadId `delete your schedule` and wait
   - Stop the Watchdog childThreadId with `t3_thread_interrupt` because its task belongs to the old Chef. List its queued runs with `t3_queue_list`, then cancel them with `t3_queue_cancel`
   - Before launching a replacement, verify that no Watchdog schedule, active run or queued turn remains. If the Watchdog cannot be stopped, escalate `❓ fault`
   - Interrupt the old Chef. Cancel its queued turns and rename it ⏹️
   - Read the old Chef's cards, branch heads, PR URLs, review rounds and decisions

   Done when neither the old Chef nor its Watchdog can act on the slot

2. Launch the replacement Chef:
   - Launch a new Chef in the same project and slot at ⏳ with that state and the replacement procedure in [chef-run](chef-run.md#return-or-replace-a-cook)
   - Update the old record's `replacedBy` and append a current `watch.toml` record with the new threadId atomically

   Done when the new Chef's Watchdog is armed, its PRs are linked and watched, and each Cook reports to the new Chef

3. Archive the old thread. Ignore a late report from it. Done when the sidebar has one Chef for the slot

## Split a batch

Split card groups without adding or cutting cards or required deliverables. Set the old Chef's `replacedBy = "split"` in `watch.toml`, then stop its Watchdog with the schedule deletion, childThreadId interruption and queued-run cancellation in Replace a Chef before interrupting and archiving the old Chef at ⏹️. Preserve its Cooks' worktrees and branch heads, and remove its batch slot from the count. Register the successor batches as current or queued slots in `watch.toml`, then assign every card and Cook to exactly one successor. A Cook whose cards move to another owner closes at ⏹️. Launch successors under the one live batch per repository rule. The first Chef adopts its assigned live Cooks with the replacement message. Cooks assigned to a queued successor close at ⏹️ with their work preserved; that successor relaunches them in the same worktrees. Update the Head Chef's denominator when the successor slots are registered. Ask Pascal only if total scope changes. Done when the old Chef is ⏹️ and archived, each card has one successor, and the count includes only the successor batches.

## Status, added work and Stop

- For status, list threads in each project with `titleContains: <id4>` and read the PRs. Give one line per batch with Chef, phase, PRs and what it awaits. Recompute your own title before ending the turn. Done when every batch is covered
- For new work, repeat Align, add batches and update the title. If the run had ended, first reopen and pin your thread. Then recreate `watch.toml` and `rules.md`, re-arm your Watchdog and launch a Chef. Never do the work yourself; see Roles. Done when the registry includes the agreed additions and its schedule is live
- On Pascal's Stop, clear open merge items, launch no further batch and send `⏹️ Stop` to every active Chef. Mark unlaunched batches stopped in the registry. Wait for each launched Chef, including any merge already running, then Close. Done when every batch has an outcome

## Close

Begin once each launched Chef is final and settled, and every queued batch ran, was cut or stopped. Show 🟢 during your own closing work.

1. If `[head-chef].retro`, follow [shared Retros](../carpaccio.md#retros). Done when each has issue links or a recorded no-findings result
2. Confirm each launched Chef is settled using 🧰 t3-runtime. Compute ⛳ or ⏹️ from the final outcomes and send Pascal the final report from [Report](../carpaccio.md#report). Mark your own final report received in `watch.toml` and set the title to the final status. As the last step before settling, delete your Watchdog's schedule, cancel its task and remove its work folder and your own, then remove the run's root cache folder. Then settle. Done when every batch has an outcome, Pascal has the report, no Watchdog schedule remains and your settle returns `settlesWhenTurnEnds: true`
