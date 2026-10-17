---
description: "Run batches under a Head Chef: Cooks implement, document, watch and delegate reviews; each Chef validates, merges and closes its batch."
---

# CU1. Batches under one Head Chef

## Vocabulary

- **SOP**: a role's procedure in `sop/`
- **Batch**: one Chef's work in one repository, grouped by the plan, such as an epic or milestone
- **Card**: a unit of work within a batch
- **Chain**: a barrage reports to its Cook, a Cook to its Chef, a Chef to the Head Chef, and the Head Chef to Pascal
- **Fast track**: `$brigade ; carpaccio ; manic-4`, or Pascal's request during a run. The Cook implements only, skipping docs and barrages

## Roles

| Role | Runs as | Title | Statuses | Responsibility |
|---|---|---|---|---|
| Head Chef | Pascal's pinned thread | `Head Chef <id4> <done>/<batches> <status> <subject>` | 🟢 ⏳ ❓ ⛳ ⏹️ | Bridges needs and requirements, splits batches, launches and guides Chefs, resumes coordination on escalation. Never edits a repository or opens a PR, even after Close |
| Chef | Thread in the batch's repository project | `🚥 Chef <b> <id4> [<served>/<cooks>] <status> <batch>` | ⏳ 🔀 🧹 🍽️ ⏸️ ⛳ ⏹️ | Creates worktrees, launches Cooks, prevents conflicts, validates, merges, releases and closes. Never edits code |
| Cook | Thread bound to its own worktree | `🧑‍🍳 Cook <b>.<c> <id4> <status> <batch>` | 🍳 🧹 🍽️ ⏸️ ⏹️ | Owns implementation, PRs, watches, docs, barrage delegation and triage, then reports readiness. Leaves merging to the Chef |
| Watchdog | Head Chef's or Chef's delegate | `🐕 Watchdog · Head Chef <id4>` or `🐕 Watchdog · Chef <b> <id4>` | none | Ticks in its own thread, wakes failed or stalled threads and alerts its parent when repair is needed |
| Barrage | Cook's delegate | `👀 <sop> · Cook <b>.<c> <id4>` | none | Reviews under the contract in its brief |
| Side delegate | Cook's delegate | `🔧 <task> · Cook <b>.<c> <id4>` | none | Runs side work the Cook delegates, such as the repository's Verify |

`<id4>` is the last four characters of the Head Chef's threadId. `<b>` numbers batches in launch order; `<c>` numbers a batch's Cooks. `<task>` names the side work in one word, such as `verify`. `<done>` counts delivered batches. The Chef adds its counter once it has grouped the Cooks. The status is the emoji alone. ❓ adds the item label. The words in the Statuses table are a glossary; never put them in a title. Put the status before the subject, without `·` separators. Progress goes in `📍` lines, never in a title.

A title displays computed status. It does not prove that a report arrived or an external action finished. The parent's `watch.toml` records received child phases, holds and report receipts. Check T3 for a launched thread's run state and settlement. Check GitHub for PR heads, checks and merges.

After renaming, read the title from T3. If the title is stale, retry the rename before ending the turn. Report a persistent failure to the parent. The Head Chef reports its own failure to Pascal.

## Statuses

Pascal watches the pinned Head Chef. ❓ means Pascal has an action; all other statuses belong to the brigade. If T3 shows the pinned Head Chef failed and its Watchdog stopped, that failed row also needs Pascal's attention.

Every thread computes its status from its own facts and the last phases received from its children when it enters a phase and before ending a turn. A registered slot that has not launched is live. The first applicable line below wins. Statuses use the set of child phases; counters count every slot, including repeated phases. [The status model](../../references/model.py) checks these functions, counters and parent-child combinations.

| Status | Meaning | Final for |
|---|---|---|
| 🟢 working | Head Chef does its own work, including answering a Chef and closing the run | none |
| ⏳ monitoring | Head Chef follows unfinished batches; Chef launches, answers, validates or follows Cooks | none |
| 🍳 cooking | Cook implements, runs barrages, writes docs or fixes its stack | none |
| ❓ `<item>` | Head Chef waits on Pascal for an item in Asking Pascal | none |
| 🔀 merging | Chef merges stacks and releases | none |
| 🧹 closing | Chef or Cook runs retros and cleanup | none |
| 🍽️ served | Cook handed up its stack, or finished after its stack merged; Chef has a ready batch at x/x | Cook, after closing |
| ⏸️ paused | Chef waits on Head Chef, or Cook waits on Chef | none |
| ⛳ delivered | All in-scope slots and own deliverables are done | Head Chef, Chef |
| ⏹️ stopped | Work closed without delivery after Stop, a cut or replacement | Head Chef, Chef, Cook |

Cook: show 🍳 while building, ⏸️ while waiting on the Chef, 🍽️ when the stack is ready, 🧹 during retros or cleanup, and ⏹️ when its batch stops or all its cards are cut. Once its merged stack and retro are done, 🍽️ is final, even after a Stop.

Chef, in priority order:

1. ⏸️ while waiting on the Head Chef for an answer other than merge approval
2. ⏳ while any Cook builds or asks
3. Once the batch stops, or all its in-scope stacks merge and its release is done, 🧹 until every Cook is final and settled and the Chef has closed; then ⛳ for a merged and released batch, otherwise ⏹️
4. 🔀 after the merge rule in Decisions authorizes the frozen heads or the Head Chef relays Pascal's approval, through release
5. 🍽️ when every Cook in its count has served and checks passed on the frozen heads
6. ⏳ while validating or working alone on a batch without PRs

For a batch without PRs, finishing the Chef's own work satisfies its checks, merge and merged facts. A release is done when completed, not required or cut by Pascal.

Head Chef, in priority order:

1. ❓ while Pascal owes an answer to an item in Asking Pascal. A held batch adds an item once no other batch or Head Chef work can progress
2. 🟢 while doing its own work or answering a Chef
3. ⏳ while any in-scope batch is unfinished, launched or not
4. ⛳ when at least one batch was delivered and no Stop came; otherwise ⏹️. A batch Pascal cuts leaves the count

The Head Chef counts delivered batches over batches in scope. The Chef counts served Cooks over Cooks in scope. A Cook whose cards were all cut leaves the Chef's count; a cut batch leaves the Head Chef's count. A stopped thread keeps the count it had. A replaced thread leaves the tree when archived, and its replacement takes the slot. Only `⛳ Batch delivered` increments the Head Chef's numerator. The `Batch merged` notice does not.

## Messages

Use the status emoji caused by a handoff. Delivery counts when the parent receives the message, not when the child sends it. Until receipt is confirmed, the sender keeps its live status, retries and reconciles; the parent never advances on an unreceived outcome.

| Message | From → to | Effect |
|---|---|---|
| 🍽️ Stack ready | Cook → Chef | Cook freezes its stack; Chef validates |
| 🍽️ Batch ready | Chef → Head Chef | Chef waits at x/x for a merge decision |
| 🔀 Merge | Head Chef → Chef | Approves the frozen stack heads |
| 🔀 Batch merging | Chef → Head Chef | Notifies a merge that the merge rule allows |
| Batch merged, with deploy results | Chef → Head Chef | Records merge progress, without counting delivery |
| ⛳ Batch delivered or ⏹️ Batch stopped | Chef → Head Chef | Counts final batch outcome |
| ⏹️ Stop | Pascal → Head Chef → Chef → Cook | Closes remaining work after an active merge finishes |
| ⛳ or ⏹️ `<done>/<batches>` lots livrés | Head Chef → Pascal | Reports final run outcome |
| ⏳ Rework, 🍽️ Hold, ⏹️ Drop | Head Chef → Chef | Relays Pascal's answer to a merge ask |
| `🙋 <card> : <URL>` | Cook → Chef → Head Chef → Pascal | Shows a Pascal-owned card as soon as it is ready; each level relays it unchanged |
| ⏹️ Cut `<card>` | Head Chef → Chef → Cook | Removes scope Pascal cut |
| `Chef <b> <id4> is now threadId <id>, replacing <old threadId>` | New Chef → Cook | Transfers reporting to a replacement |
| `🐕 Watchdog <id4>: wake <n>/<max-wakes>` | Watchdog → watched thread | Queues a resume turn after failure or stall |
| `🐕 Watchdog <id4>: <finding>` | Watchdog → parent | Reports an interruption, exhausted wakes or a two-tick finding. The parent reads the slot's T3 state and external effects, then resumes, replaces or reconciles the child. Before it replaces an interrupted child, it asks up the chain whether Pascal intended Stop. It escalates a fault it cannot repair |

## Decisions

Apply this table without asking. Only the items in Asking Pascal go to Pascal. An explicit instruction from Pascal overrides a row; the Head Chef writes it in the Plan of the Chef. Record overrides, exceptional calls and merge authorization in your thread's Detail message. The SOPs link here for these choices.

| Choice | Rule | Decides |
|---|---|---|
| Parallel or serial | If the groups touch disjoint files and have no dependency, run them in parallel. If you have a doubt, run them in series. Stay within `max-parallel` and `max-cooks`. Never run two batches of one repository at the same time | Head Chef for batches, Chef for Cooks |
| Merge | Apply Pareto 90-10 to the work left: focus on the few gaps that could change the outcome, not low-impact polish. Return an open `Act on` finding to Fix. If the requirements and required checks are met and you can explain why the remaining risk does not change the result, state your confidence, evidence and low-impact remainder in the Report, then merge with `🔀 Batch merging`. If a material uncertainty remains after you try to resolve it, send `🍽️ Batch ready` with your recommendation; the Head Chef asks Pascal one `🙋 merge` question | Chef |
| Release | If the `AGENTS.md` or release doc of the repository requires a release after a merge, release. Otherwise, do not release | Head Chef, at Align |
| Docs | Put the doc change of a card in the layer of that card. Open a top docs PR only for docs that no card owns | Cook |
| Another machine, such as macOS | Run the check with 🧰 fleet, from the machine of the run. For a macOS check, use the mini if fleet's `repos.toml` marks the repository `mini = true` and the mini has the tools. Otherwise, run the macOS check on the mbp. Name the machine in the report. Do not skip it because it is on another machine. If a required check remains unconfirmed at Ready, name the check, its exact command and the blocker; the Chef asks Pascal before merging. For an optional check, the Chef explains why its absence cannot change the result | Cook; Chef reads the output |
| Pascal-owned card ready, such as a mockup | Align marks these cards in the Plan. When such a card is ready, send `🙋 <card> : <URL>` up the chain at once. Keep the other work running | Cook sends; Head Chef posts |
| Work after Close | Reopen the run. Align the addition, write `rules.md` again, re-arm the Watchdog and launch a Chef | Head Chef |
| Anything else with a safe default, such as a cost trade-off | If you have the context, decide and log it. Otherwise, send it one level up with your default | The lowest role that has the context |

### Asking Pascal

Only these items produce ❓. For one item, label the title `align`, `merge <b>`, `scope`, `reserved action`, `fact`, `fault <what>`, `held batch <b>` or `card <card>`. For two or more items, label it `<n> for you`.

1. Align: requirements and batches, or work added during the run. Never ask Pascal a choice that a Decisions row covers
2. Merge with a material uncertainty that the Chef cannot resolve under Decisions
3. Scope cut of a card, batch or required deliverable
4. Reserved action: deleting data, leaving the agreed repositories or force-pushing a branch the run did not create
5. Fact only Pascal knows, such as diagnose's one question when Align did not answer it
6. Fault the brigade cannot repair, including a stack returned `max-returns` times for the same cause
7. Held batch once nothing else in the run can progress
8. Pascal-owned card ready, per Decisions

Each item is one line in Canadian French, starting with `🙋`, such as `🙋 merge #122–#129 sans test macOS requis ? Confiance incertaine ; je recommande d'attendre` or `🙋 choisir les looks M07-T1 : <URL>`. A merge line names the material uncertainty and the Chef's recommendation. Use no option menu, long status block, protocol name or cache path. Put the open items as the last lines of each ❓ turn. Post them again when they change. Pascal's reply decides the item it names. If exactly one merge item is open, `oui` or `merge` approves it. If several items are open and the reply names none, ask which item in one line. Keep an unanswered merge batch at 🍽️.

Approval binds to the frozen heads and the stack's own diff. A restack that changes only its base keeps approval and the Cook 🍽️ when checks pass on the new heads. A change to its own diff needs a new merge decision. Stop voids an unused approval. Before you retry a launch, merge, deploy or release, look in T3, GitHub or the deploy output to see if that action already occurred.

## SOPs

Read only the SOP for your current role and step, plus each section it links to.

| SOP | Read when |
|---|---|
| [head-chef](sop/head-chef.md) | Coordinating the run |
| [chef-run](sop/chef-run.md) | Launching Cooks, following progress or relaying Stop |
| [chef-closing](sop/chef-closing.md) | Validating a stack, merging or closing the batch |
| [cook-implement](sop/cook-implement.md) | Implementing, fixing, documenting, reporting, stopping or running retros |
| [cook-review](sop/cook-review.md) | Delegating reviews or triaging results and watch wakes |
| [watchdog](sop/watchdog.md) | Delegated per-parent tick, wake, alert and forbidden-combination checks |
| [manic-1](sop/manic-1.md) | Delegated adversarial review |
| [manic-2](sop/manic-2.md) | Delegated blast-radius review |
| [manic-3](sop/manic-3.md) | Delegated docs review |
| [manic-5](sop/manic-5.md) | Delegated pristine review |

## Settings

Read [config.toml](config.toml) for settings and their readers; edit the source copy when changing them.

## Process

Copy the table and check off your role's steps:

| # | Step | Owner and SOP |
|---|---|---|
| 0 | Align and arm Watchdog | Head Chef and Pascal, `head-chef` |
| 1 | Implement, diagnose first for bug cards | Cook, `cook-implement` |
| 2 | manic-1 and manic-2 side by side through interrogate | Cook leads, delegates and triages, `cook-review` |
| 3 | Docs | Cook, `cook-implement` Docs |
| 4 | manic-3 and manic-5 side by side through interrogate | Cook leads, delegates and triages, `cook-review`; manic-3 uses technical-writing |
| 5 | Validation and merge | Chef, `chef-closing`; Head Chef for held batches |
| 6 | Closing and remove Watchdogs | Head Chef, Chef and Cook, `head-chef`, `chef-closing` and `cook-implement` Retros |

For a batch that opens no PR, its Chef does the work alone, skips steps 1 to 5, and reports that choice. Fast track goes from Implement to the Cook's Ready section, then step 5.

## Shared rules

- One PR per verifiable unit, in one stack per Cook and repository with 🧰 gh-stack, even for independent cards. Assign each PR to `pr-assignee`
- The Cook is the sole writer in its worktree and owns every restack. The Chef uses it for merging only after the Cook reports a clean, pushed checkout
- Put each fix in the layer that last changed its line; for a line from the trunk, use the layer whose change made it wrong
- The Cook follows the repository's `AGENTS.md` procedure first; 🧰 poteto-mode fills what it leaves open. Treat issue proposals as drafts: verify each command, flag and message against the tool's source or a throwaway run before copying it. Report each false line and its fix to the Chef
- The Head Chef writes the standing rules that the target projects do not load, including [Work folders](#work-folders), once to `~/.cache/brigade-<id4>/rules.md`. Every launch message and barrage brief carries `Rules: <rules.md path>`, plus the additions it inherited and its own. Omit an empty field
- A comment posted through Pascal's account does not wake the Cook's watch; the Chef also sends it to the Cook with `t3_thread_send`
- A question climbs the chain with the sender's default. Each level answers from its context or escalates. A Chef unable to resolve a batch problem asks the Head Chef to decide, split the work again or relaunch the Chef
- When Pascal writes to a Chef or Cook directly, that thread acts on the message and tells its parent so the status tree stays current
- Keep going without Pascal within the agreed repositories and their PRs and issues. The run may push and open or update PRs and issues, and force-push its own branches with `--force-with-lease`. Merge deploys and retro issues in Pascal's repositories are allowed
- Escalate before deleting data, changing anything outside that scope or force-pushing a branch the run did not create. Deleting a merged branch whose tip matches its recorded PR head preserves the merged work
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md

### Retros

For each enabled role, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Each retro files the issues with the most value, up to `retro-max-issues` per thread. Done when each has issue links or a recorded no-findings result.

## Work folders

Use `~/.cache/brigade-<id4>/<thread>/` for temporary files and caches, with `TMPDIR` set to its `tmp/` subfolder. `<thread>` is `head-chef`, `chef-<b>`, `cook-<b>.<c>`, `watchdog-head-chef`, `watchdog-<b>` or `<sop>-<b>.<c>-<k>`. Create both folders before work. Remove a Cook or barrage work folder before its final report, removing a barrage's detached worktree first. Recreate folders when resumed.

## Model selection

The Head Chef selects `[chef]`, the Chef selects `[cook]`, and the Cook selects each barrage's table from `config.toml`. The Head Chef and each Chef select `[watchdog]` for their own Watchdog.

1. Read your selection with `t3_thread_configuration`. For a thread, choose `chef-on-claude` or `chef-on-codex` from the launching role's provider; for a barrage, choose `cook-on-claude` or `cook-on-codex` from the Cook's provider. `inherit` keeps your instance, model and reasoning level. Otherwise resolve `instance` to a live provider instance in `orchestrator_capabilities`. Done when the provider and model exist
2. Map `reasoning-level` to Codex `reasoningEffort` or claudeAgent `effort`. Map `service-tier` `standard`/`fast` to Codex `serviceTier` `default`/`priority` or claudeAgent `fastMode` `false`/`true`. Send an option only when the catalog entry of the model lists it. Table values override top-level defaults. For Cook side work on Claude, use `[cook].delegate-on-claude` through `delegate_task`. A Watchdog uses `watch-on-claude` or `watch-on-codex` from its parent's provider, staying on that provider rather than following the barrage rule. Done when the catalog supports each option, every barrage uses the other provider and every Watchdog uses its parent's provider
3. Threads inherit runtime and interaction modes at launch; delegates inherit them from the Cook. Keep `runtime-mode = "inherit"` throughout the run, with no mode change. For launches use `modelSelection`; for delegations use `target`, renaming `instanceId` to `providerInstanceId`. Escalate an unavailable setting through the chain. Done when the selection is supported

## Report

Before sending `🍽️ Stack ready`, `🍽️ Batch ready`, `🔀 Batch merging` or a final outcome, each Cook and Chef posts a `Detail` message in its own thread. Name the frozen heads it covers. Record review rounds, accepted, `Consider` and rejected findings with reasons, skipped steps, gaps not filed, and exceptional decisions. Post a new `Detail` after a changed head. The parent reads that thread and cites its threadId, but does not copy the Detail. The Detail survives work-folder cleanup.

A Report message uses only its field set below. It has a maximum of 8 lines and 1200 characters, plus its `🙋` lines.

A Cook lists its PRs and heads in `🍽️ Stack ready`, and again after a restack. The Chef gives the batch's PR range in `🍽️ Batch ready` or `🔀 Batch merging`. Later messages give the range only if needed to identify a partial outcome.

The Head Chef's Close removes the cache folders. Thus a message to Pascal cites only PR, issue and artifact URLs.

In a message or a Detail, write every clock time in America/Montreal time. GitHub and T3 return UTC times. Convert them first.

`🍽️ Stack ready`, Cook → Chef:

```text
🍽️ Stack ready · Cook <b>.<c> <id4>
PR: #<n> <sha> · #<n> <sha>, checks <state>
Reviews: <accepted> accepted, <rejected> rejected
Not confirmed: <what and the command that would confirm it, or none>
Confidence: <level, evidence and remaining risk>
Detail: <Cook threadId>
```

`🍽️ Batch ready` or `🔀 Batch merging`, Chef → Head Chef: replace the Cook template's first line with the Chef role and message. Use the batch's PR range, your confidence based on every Cook's evidence and `Detail: <Chef threadId>`. Add `For Pascal: <🙋 lines, or none>`. For `⛳ Batch delivered` or `⏹️ Batch stopped`, send the outcome, deploy result and Detail threadId. Give the PR range only for a partial outcome.

Head Chef → Pascal, in Canadian French. At Align, show the batch plan and end with the open `🙋` lines. For a later ask, send only those lines. Any other unrequested message to Pascal before the final report is a notice. A notice has at most 3 lines: the outcome, the PR range and the next step. It has no table or `<details>`. For the final report, use this template:

```text
<⛳ or ⏹️> <done>/<batches> lots livrés : <one-line outcome>
PR fusionnées : <#<n>–#<n>, or aucune>
Reste pour toi : <🙋 lines, or rien>
```

`📍` progress, Cook → Chef, at the end of each process step: `📍 <card> <step>/6 · <PR URL> · checks <state>`.
