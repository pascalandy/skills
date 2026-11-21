# head-chef

Keep batch registry in `watch.toml` in your work folder: batch number, name, repository, projectId, Cook threadId, worktree and branch, dependencies, Align choices, last received phase, progress start, hold and outcome. Include watched slots and Watchdog ids; write it atomically, as [watchdog](watchdog.md#files) defines. Apply [Statuses, Messages and Decisions](../halloumi.md#statuses) at phase entry and turn end. Registered but unlaunched batch stays live.

## Align

1. Rename yourself `Head Chef <id4> 0/0 🟢 <subject>` and pin yourself before asking Pascal anything. If pinning fails, retry and tell Pascal in your message. Create `watch.toml` with your own slot, then arm your 🐕 Watchdog with [watchdog](watchdog.md#arm) after pinning. Done when pinned title matches current work or wait and Watchdog reported its schedule id
2. Write goal and problem in Pascal's words and each card's acceptance criteria, for the scope Pascal names, e.g. waves 4 to 6 of a plan. Done when each card in scope has its acceptance criteria
3. Build the lot map. Decide release with [Decisions](../halloumi.md#decisions) first. For each card, list its blockers with their reasons and the files the card will change, incl. docs and release files, e.g. `CHANGELOG.md`. Take the blockers that the plan declares, and find the missing blockers in the code. Group the cards into batches of one repository each under Shared rules. Mark the batches that run in parallel under Decisions, and the critical path. A batch whose checks need another batch's release depends on that batch. Put each QA item after the batches it tests and before the batches whose cards wait on it. Resolve each batch's Cook and reviewer models under Model selection. Done when every card is in one batch and every blocker has its reason
4. Mark Pascal-owned cards, record exceptional choices in Detail. For a [hard stop](../halloumi.md#hard-stops) a batch's own cards will hit, draft an advance authorization naming batch, action, scope and conditions. Set `Fast track` from Pascal's request, else no. Set delivery mode to full-send, or to full-stop when Pascal said "full stop", and record it in the Align plan with any route-versus-repository conflict under [Decisions](../halloumi.md#decisions). Write `rules.md` under Shared rules and update title's batch count. Done when Plan, lot map, rules, choices and title agree
5. Send Align plan from [Report](../halloumi.md#report), then go to Launch in same turn. Show `❓ align` only for a question the plan, issues and agreed requirements leave open, or for an advance authorization Pascal has not answered; meanwhile launch batches that do not depend on its answer. A batch whose advance authorization waits launches with `none`; relay Pascal's approval to its Cook with `t3_thread_send` when it comes. Done when each batch that waits on no open question is launched or queued under Launch

## Launch

Run batches in parallel or in series, as [Decisions](../halloumi.md#decisions) tells. A batch whose repository has a live batch launches only when Decisions lets the two run in parallel; otherwise wait for that batch to be final, even if its PRs merged. Wait for dependencies to be delivered, and for each QA item a batch's cards wait on to report `🧪 QA done`. Escalate a dependency that ends without delivery. A full-stop batch delivers without merging: do not launch a batch that needs its merged code or release; mark it stopped in the registry and name it, with what it waits on, in the final report.

1. Select Cook using Model selection in `halloumi.md`. If a card creates the repository, first create it as the card specifies, clone it under projects folder, push an initial empty commit and run `git -C <clone> remote set-head origin --auto`, then follow normal launch path. Find its project with `t3_project_list` or register it with `t3_project_create`; escalate an unavailable tool only as Asking Pascal allows. Done when repository has `origin/HEAD` and registry has a projectId and supported selection
2. List open PRs outside the run that change batch's files or spec files its cards cite. Decide each overlap from agreed requirements and context; ask Pascal only via [Asking Pascal](../halloumi.md#asking-pascal). Done when each overlap has a decision
3. Fetch `origin`, then create Cook's worktree from `origin/HEAD`, under `~/projects/.worktrees/<repo>-<branch>/`, with branch `<batch>-1` using a Git-safe batch slug. Use `git -C <clone> worktree add <path> -b <branch> origin/HEAD`. Done when worktree's status shows its assigned branch
4. Register Cook slot `cook-<b>.1`, holding every card of the batch, in `watch.toml` atomically. Before a retry, check whether a launch already created the Cook. Launch with `t3_thread_launch`, registry's explicit `projectId`, `workspaceStrategy: {type: "existing_worktree", worktreePath: <absolute path>, branch: <branch>}`, Cook title from Roles at 🍳, and message below. Write its threadId into the slot atomically. Done when `t3_thread_read` shows it started in that worktree and registry holds its threadId

```text
$brigade-mode ; halloumi ; cook-run
Role: Cook <b>.1 <id4>. Report only to Head Chef, threadId <full threadId>, with t3_thread_send.
Batch: <b>, <name>, repository <absolute clone path>
Worktree: <absolute path>, branch <branch>, base <trunk>
Plan: <goal, every card of the batch in order with acceptance criteria, batch threat model and dependencies>
Advance authorization: <hard-stop action, scope and conditions Pascal approved at Align, or none>
Release: <yes/no, per Decisions; required release content>
Fast track: <yes/no>
Delivery: <full-send or full-stop>
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
```

## Coordinate

On each wake, reconcile your Watchdog and its findings:

- Rebuild a missing or unreadable `watch.toml` from your thread history. Include all registered slots, those awaiting launch too, their current state and recorded Watchdog ids
- Check your Watchdog's schedule under [Schedule health](watchdog.md#schedule-health). If unhealthy, delete any old schedule, cancel its task and re-arm your Watchdog
- On a Watchdog health finding, read slot's T3 state and external effects, then resume, [replace](#replace-a-cook) or reconcile its Cook. Take a fault you cannot repair to Asking Pascal. Long-batch alerts go to step 5

Done when `watch.toml` is readable, schedule is live and each finding has an owner.

1. Record each Cook's received phase and decide its questions under [Decisions](../halloumi.md#decisions). For an item in Asking Pascal, show matching label and relay the answer. Otherwise decide, split the batch or replace its Cook. Done when each escalation has an owner and next action
2. On `🍽️ Batch ready`, read Report and Detail, decide each doubted gate under Decisions and send `🔀 Merge`, `⏳ Rework` or `🍽️ Hold`. For an open [hard stop](../halloumi.md#hard-stops), send Pascal its `🙋` line and wait: send `🔀 Merge` only once Pascal's answer or an advance authorization clears it. Under full-stop, a hard stop only the merge would cross is deferred, per Decisions: do not ask it or wait on it. Relay `⏹️ Drop` only after Pascal cuts scope. For a Pascal-owned card, check its result against the Plan before posting it. Return a mismatch to the Cook for correction; otherwise post the Asking Pascal line in same turn and relay the answer. Keep other batches running. A Hold stays live. Done when each ready batch has a decision or an open Asking Pascal item, and every presented card matches the Plan
3. Record `🔀 Batch merging` and `Batch merged` as notices, without incrementing the counter. Keep each `external_gap` a `Batch merged` names, with its machine, cause and fix command, for the final report. On `⛳ Batch delivered` or `⏹️ Batch stopped`, record final outcome and update title. Record each item the report says waits on Pascal, with its GitHub URL, for Close. Start newly eligible batches and QA items. On merge failure, keep landed PRs while the Cook fixes the cause. Done when registry and title match received outcomes
4. Once a Cook is final, confirm with 🧰 t3-runtime it is settled. Remove its worktree with `git -C <clone> worktree remove <literal path>` when clean and merged, or keep it with a reason. Keep it until every QA item that tests its batch has reported, and its Cook has sent `🧪 QA fixed` for each QA item that sent it findings. Recheck this on each `🧪 QA done` and `🧪 QA fixed`. Keep a full-stop Cook's worktree, which the later merge runs from, and give its path in the final report. Done when that Cook is settled and its worktree is removed or accounted for
5. If a batch loses readiness, withdraw any related Pascal ask and send its withdrawal notice under Report. Relay changed batch choices or fast track to the Cook. On a Watchdog long-batch alert, send the [long-batch notice](../halloumi.md#report). Done when each affected Cook has current decision and each alert has its notice
6. Apply [Hard stops](../halloumi.md#hard-stops) to a scope change. Relay `⏹️ Cut <card>` or `⏹️ Drop`; remove a cut batch from the count only after its Cook reports ⏹️. Done when reduced scope and titles match received outcomes

When no action remains, end your turn until a message wakes you.

## QA items

1. Once every batch a QA item tests is delivered, register slot `qa-<q>` in `watch.toml`. Under full-stop, mark the QA item and the batches that wait on it stopped instead, as Launch says for merged code. For each repository the QA item tests, fetch `origin` and create a detached worktree at its trunk SHA with `git -C <clone> worktree add --detach <path> <trunk SHA>`, under `~/projects/.worktrees/<repo>-qa<q>/`. Select the QA agent under Model selection. Delegate with `delegate_task`, `mode: "async"`, title from Roles and the brief below. Run it on the machine the QA item names, under the Another machine row of Decisions, else on the run's machine. If the QA agent fails or stops without `🧪 QA done`, start a fresh one once; a second failure is a fault under Asking Pascal. Done when the slot holds its taskId
2. On `🧪 QA done`, record the verdict and the QA agent's thread link as the report link. Remove the QA worktrees with `git -C <clone> worktree remove <literal path>`. Launch the batches that wait on the QA item. Group the findings by the batch that owns each finding's card. Send each owning Cook one `🧪 QA findings` with `<q>` and its issue URLs, or send it to the Cook's replacement. A returning Cook counts toward `max-parallel` and the file rule of Decisions; queue its message until both allow it. When it starts, record that Cook's phase as 🍳, set its `progressSince` to now and clear its final receipt in `watch.toml`. Record a finding that no batch owns for the final report. Done when every finding is sent, queued or recorded, and the waiting batches are launched or queued
3. On `🧪 QA fixed`, record each finding's outcome for the final report, then remove the Cook's worktree under Coordinate step 4. Done when every QA fix is final

```text
Role: QA agent <q> for Head Chef <id4>, threadId <full threadId>. Report only to it with t3_thread_send.
Repo: <absolute path of each detached QA worktree, with its repository and trunk SHA>. Work only there. Keep the Cooks' worktrees untouched.
QA item: <the plan's QA item word for word: scenarios, checks and expected results>
Machine: <machine and fleet procedure, or this one>
Test each scenario once, recording the command or steps and the result you observed. Read only this item, the repository and its docs; you have no implementation context. Change no code and open no PR. File each finding as one issue with 🧰 label-for-issues, with its reproduction, after checking duplicates.
Report: `🧪 QA done · QA <q> <id4>`, verdict accepted, accepted with findings or rejected, one line per scenario with its result, then each finding's issue URL.
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
```

## Replace a Cook

When a Watchdog finding or a Cook's silence shows it cannot continue, inspect its thread and PRs before retrying or relaunching anything. Resume it when a message can restart it. Before replacing an interrupted Cook, ask Pascal whether Stop was intended. Keep batch slot and Cook's worktree.

1. Set old record's `replacedBy = "pending"` in `watch.toml` before interrupting the old Cook, cancelling its queued turns and renaming it ⏹️. Read its cards, branch heads, PR URLs, loop ledgers and decisions. Done when old Cook cannot act on the slot
2. Launch replacement in same project, slot and existing worktree at 🍳, with the launch message plus that state. Update old record's `replacedBy` and append a current record with the new threadId atomically. Replacement links and watches the PRs. Done when new Cook's PRs are linked and watched and it reports to you
3. Archive old thread. Ignore a late report from it. If replacement fails again, show `❓ fault`. Done when sidebar has one Cook for the slot, or the fault is with Pascal

## Split a batch

Split a batch's cards without adding or cutting cards or required deliverables. Set old Cook's `replacedBy = "split"` in `watch.toml`, then interrupt and archive it at ⏹️. Keep its worktree and branch heads; remove its batch slot from the count. Register successor batches as current or queued slots in `watch.toml`, then assign every card to exactly one successor. Launch successors under Launch. First successor's Cook adopts the old worktree, removes the layers of cards that moved and keeps their branches. Create each later successor's worktree on those kept branches. Update Head Chef's denominator when successor slots are registered. Ask Pascal only if total scope changes. Done when old Cook is ⏹️ and archived, each card has one successor, and the count includes only successor batches.

## Status, added work and Stop

- For status, list threads in each project with `titleContains: <id4>` and read the PRs. One line per batch with Cook, phase, PRs and what it awaits. Recompute your own title before ending the turn. Done when every batch is covered
- For new work, repeat Align, add batches and update title. If the run had ended, first reopen and pin your thread. Then recreate `watch.toml` and `rules.md`, re-arm your Watchdog and launch a Cook. Never do the work yourself; see Roles. Done when registry includes agreed additions and its schedule is live
- On Pascal's Stop, clear open merge items, launch no further batch, send `⏹️ Stop` to every active Cook. Cancel each active QA agent with `task_cancel`. Mark unlaunched batches, queued QA items and queued QA fixes stopped in registry. Wait for each launched Cook, including any merge already running, then Close. Done when every batch has an outcome

## Close

Begin once each launched Cook is final and settled with its worktree removed or kept with a reason, every queued batch ran, was cut or stopped, and every QA item and QA fix reported or was stopped. Show 🟢 during your own closing work.

1. If `[head-chef].retro`, follow [shared Retros](../halloumi.md#retros). Done when each has issue links or a recorded no-findings result
2. Confirm each launched Cook is settled using 🧰 t3-runtime. Right before the final report, read on GitHub every recorded item that waits on Pascal. If no Stop came, apply each decision already posted via [Status, added work and Stop](#status-added-work-and-stop) and return to Coordinate for any added work before closing. After a Stop, list decided follow-up work with its GitHub URL in final report's `Reste pour toi` line, without adding a batch. Keep unanswered items in final report. Compute ⛳ or ⏹️ from final outcomes and send Pascal the final report from [Report](../halloumi.md#report). Mark your own final report received in `watch.toml` and set title to final status. As last step before settling, delete your Watchdog's schedule, cancel its task and remove its work folder and your own. Then remove run's root cache folder, unless a thread reported a folder it kept or your own cleanup failed: then keep the root and send Pascal a short follow-up naming kept folders. Run `git worktree prune` in every run repository. Then settle. Done when every batch has an outcome, Pascal has the report, root is gone or Pascal's follow-up names kept folders, no Watchdog schedule remains and your settle returns `settlesWhenTurnEnds: true`
