---
description: "Run batches under a Head Chef with no Chef: one Cook per batch runs Pascal's solo recipe, one PR per card in one stack, with a review loop on each PR and one on the whole stack, then merges, releases and closes its batch."
---

# CU1. Batches under one Head Chef

## Vocabulary

- **SOP**: a role's procedure in `sop/`
- **Batch**: one Cook's work in one repository, grouped by plan, e.g. an epic or milestone. One Cook implements all of it
- **Card**: unit of work within a batch
- **Chain**: reviewer or side delegate reports to its Cook, Cook to Head Chef, Head Chef to Pascal
- **Loop 1**: 🧰 review-loop on one PR, via manic-1 and manic-2 angles
- **Loop 2**: 🧰 review-loop on what will merge together, whole stack or single PR, via manic-3 and manic-5 angles
- **Fast track**: `$brigade ; gravlax ; manic-4`, or Pascal's request during a run. Cook implements only, skipping docs and both loops
- **Shipped behavior**: what a user or caller of the cards' work can observe. A comment, wording, format, docs or test-only change leaves it unchanged, even if a reviewer proposed it

## Roles

| Role | Runs as | Title | Statuses | Responsibility |
|---|---|---|---|---|
| Head Chef | Pascal's pinned thread | `Head Chef <id4> <done>/<batches> <status> <subject>` | 🟢 ⏳ ❓ ⛳ ⏹️ | Bridges needs and requirements, splits batches, creates each Cook's worktree, launches and guides Cooks, resumes coordination on escalation, removes each settled Cook's worktree. Never edits code or opens a PR, even after Close |
| Cook | Thread bound to its own worktree | `🧑‍🍳 Cook <b>.1 <id4> <status> <batch>` | 🍳 ⏸️ 🍽️ 🔀 🧹 ⛳ ⏹️ | Runs Pascal's solo recipe on every card of its batch, one PR per card in one stack, owns watches, docs and both loops, then merges, releases and closes its batch |
| Watchdog | Head Chef's delegate | `🐕 Watchdog · Head Chef <id4>` | none | Ticks in its own thread, wakes failed threads and stalled Cooks, alerts Head Chef when repair is needed |
| Reviewer | Cook's delegate, one review-loop round | `👀 loop-<n> · Cook <b>.1 <id4>` | none | Reviews one round of loop `<n>` under its brief |
| Side delegate | Cook's delegate | `🔧 <task> · Cook <b>.1 <id4>` | none | Runs side work the Cook delegates, e.g. repository's Verify |

`<id4>` = last four characters of first Head Chef's threadId; a Head Chef that takes over the run keeps it. `<b>` numbers batches in launch order. Cook title keeps the `.1` of earlier routes for replay; a replacement keeps it. `<n>` is `1` or `2`. `<task>` names the side work in one word, e.g. `verify`. `<done>` counts delivered batches. Status is the emoji alone. ❓ adds the item label. Words in the Statuses table are a glossary; never put them in a title. Put status before subject, without `·` separators. Progress goes in `📍` lines, never in a title.

A title shows computed status. It does not prove a report arrived or an external action finished. Parent's `watch.toml` records received child phases, holds and report receipts. Check T3 for a launched thread's run state and settlement. Check GitHub for PR heads, checks and merges.

After renaming, read title from T3. If stale, retry the rename before ending the turn. Report a persistent failure to the parent. Head Chef reports its own failure to Pascal.

## Statuses

Pascal watches the pinned Head Chef. ❓ means Pascal has an action; all other statuses belong to the brigade. If T3 shows pinned Head Chef failed and its Watchdog stopped, that failed row also needs Pascal's attention.

Every thread computes its status from its own facts and last phases received from its children when it enters a phase and before ending a turn. A registered slot not yet launched is live. First applicable line below wins. Statuses use the set of child phases; counters count every slot, repeated phases included. Status model in `references/model.py` does not cover this route yet: https://github.com/pascalandy/skills/issues/1172.

| Status | Meaning | Final for |
|---|---|---|
| 🟢 working | Head Chef does its own work, incl. answering a Cook and closing the run | none |
| ⏳ monitoring | Head Chef follows unfinished batches | none |
| 🍳 cooking | Cook implements, runs its loops, writes docs, proves, babysits or fixes its stack | none |
| ❓ `<item>` | Head Chef waits on Pascal for an item in Asking Pascal | none |
| 🔀 merging | Cook merges its stack and releases | none |
| 🧹 closing | Cook runs retros and cleanup | none |
| 🍽️ served | Cook sent `🍽️ Batch ready`, waits for merge decision | none |
| ⏸️ paused | Cook waits on the Head Chef | none |
| ⛳ delivered | All in-scope slots and own deliverables are done | Head Chef, Cook |
| ⏹️ stopped | Work closed without delivery after Stop, a cut or replacement | Head Chef, Cook |

Cook, in priority order:

1. ⏸️ while waiting on Head Chef for an answer other than a merge decision
2. Once batch stops, or its stack merged and its release is done, 🧹 until retros and cleanup are done; then ⛳ for a merged and released batch, else ⏹️
3. 🔀 after merge rule in Decisions authorizes frozen heads or Head Chef sends `🔀 Merge`, through release
4. 🍽️ after `🍽️ Batch ready`, while waiting for merge decision
5. 🍳 otherwise

Batch without PRs: finishing Cook's own work satisfies its checks, merge and merged facts. A release is done when completed, not required or cut by Pascal.

Head Chef, in priority order:

1. ❓ while Pascal owes an answer to an item in Asking Pascal. A held batch adds an item once no other batch or Head Chef work can progress
2. 🟢 while doing its own work or answering a Cook
3. ⏳ while any in-scope batch is unfinished, launched or not
4. ⛳ when at least one batch was delivered and no Stop came; else ⏹️. A batch Pascal cuts leaves the count

Head Chef counts delivered batches over batches in scope. A cut batch, or one whose cards were all cut, leaves Head Chef's count. A stopped thread keeps the count it had. A replaced thread leaves the tree when archived; its replacement takes the slot. Only `⛳ Batch delivered` increments Head Chef's numerator. `Batch merged` notice does not.

## Messages

Use the status emoji a handoff causes. Delivery counts when parent receives the message, not when child sends it. Until receipt is confirmed, sender keeps its live status, retries and reconciles; parent never advances on an unreceived outcome.

Send an answer or relay with `t3_thread_send` `mode: "auto"` and a `clientRequestId` you reuse for each retry. `delivery: "steered"` means the message entered the running turn, not that receiver acted on it. Treat `queued` as not yet received: call `t3_queue` with receiver's `threadId` and `action: "list"`; once receiver's turn is steerable, call it again with `action: "promote_to_steer"`, that message's queued run as `queuedRunId` and active run as `targetRunId`. Receipt counts when receiver's reply acts on it. Watchdog wakes keep `mode: "queue"`.

| Message | From → to | Effect |
|---|---|---|
| 🍽️ Batch ready | Cook → Head Chef | A real doubt or hard stop remains; Cook freezes its stack, waits for a decision |
| 🔀 Merge | Head Chef → Cook | Authorizes frozen heads under Decisions |
| 🔀 Batch merging | Cook → Head Chef | Notifies a merge the merge rule allows |
| Batch merged, with deploy results | Cook → Head Chef | Records merge progress, without counting delivery |
| Readiness withdrawn | Cook → Head Chef | Records a return to Fix, withdraws a pending merge decision |
| ⛳ Batch delivered or ⏹️ Batch stopped | Cook → Head Chef | Counts final batch outcome |
| ⏹️ Stop | Pascal → Head Chef → Cook | Closes remaining work after an active merge finishes |
| ⛳ or ⏹️ `<done>/<batches>` lots livrés | Head Chef → Pascal | Reports final run outcome |
| ⏳ Rework, 🍽️ Hold, ⏹️ Drop | Head Chef → Cook | Records Head Chef's decision or relays Pascal's answer; only Pascal can Drop |
| `🙋 <card> : <URL>` | Cook → Head Chef → Pascal | Presents a Pascal-owned card after Head Chef checks it against the Plan |
| ⏹️ Cut `<card>` | Head Chef → Cook | Removes scope Pascal cut |
| `🐕 Watchdog <id4>: wake <n>/<max-wakes>` | Watchdog → watched thread | Queues a resume turn after failure or stall |
| `🐕 Watchdog <id4>: <finding>` | Watchdog → Head Chef | Reports a health or long-batch finding; [Coordinate](sop/head-chef.md#coordinate) owns the response |

Cook → Head Chef uses only this table, `📍` step lines, questions and a report another rule asks for, e.g. a kept folder. Record other progress in Detail.

## Decisions

When a rule's words do not fit your case, apply its purpose, decide and record the decision in your Detail. Applies to every rule of this route. Never stop to ask which rule wins. An explicit instruction from Pascal overrides a rule; Head Chef writes it in the Cook's Plan.

Cook merges alone when every merge gate's purpose is met and no [hard stop](#hard-stops) is open. Send a real doubt to Head Chef, incl. a loop ended at budget or on a dispute, or a required check that stays unconfirmed. Head Chef decides from the evidence and records its reasons and remaining risk in Detail. Its `🔀 Merge` settles the doubted gate for the frozen heads; loop's recorded end stays as it was. Only a hard stop goes to Pascal. Other questions follow Asking Pascal.

| Choice | Rule | Decides |
|---|---|---|
| Parallel or serial | If batches touch disjoint files and have no dependency, run them in parallel. If in doubt, run them in series. Stay within `max-parallel`. Never run two batches of one repository at once. A batch has one Cook, which implements its cards in Plan's order. A card that can start only after another card merges goes to a later batch of same repository | Head Chef |
| Merge | Apply [Merge gates](#merge-gates) to frozen heads, then follow [cook-closing](sop/cook-closing.md#merge-gate-and-merge) | Cook; Head Chef settles doubts |
| Release | If repository's `AGENTS.md` or release doc requires a release after a merge, release. Otherwise do not release | Head Chef, at Align |
| Docs | Put a card's doc change in that card's layer. Open a top docs PR only for docs no card owns | Cook |
| Another machine, e.g. macOS | Run the check with 🧰 fleet, from the run's machine. For a macOS check, use the mini if fleet's `repos.toml` marks the repository `mini = true` and the mini has the tools. Otherwise use the mbp. Name the machine in the report. Public repository: use fleet's `check_remote.py` receipt for the tested head and exact `--command`. Private repository: record in your Detail host, worktree, folder and tested SHA, plus borrowed checkout's `git worktree list --porcelain` and `git for-each-ref` before adding yours. Create a detached worktree at `HEAD`, fetch with `git fetch --no-tags --no-prune <repository URL> <tested SHA>` inside it, then check out that SHA there; only its `FETCH_HEAD` is written. Before your final report, remove that worktree without `--force`, then your folder under Work folders. Check both paths are gone and borrowed checkout's refs match your record. If either procedure fails, stop, keep what remains and report remaining paths to Head Chef with the reason. Leave borrowed checkouts. Optional check: explain why its absence cannot change the result | Cook |
| Pascal-owned card ready, e.g. a mockup | Align marks these cards in the Plan. When one is ready, Cook sends `🙋 <card> : <URL>` at once and keeps other work running. Head Chef checks the card against the Plan, then posts the line in same turn or returns the card with each mismatch | Cook sends; Head Chef checks and posts |
| Work after Close | Reopen the run. Align the addition, rewrite `rules.md`, re-arm the Watchdog, launch a Cook | Head Chef |
| Anything else with a safe default, e.g. a cost trade-off | If you have the context, decide and log it. Otherwise send it one level up with your default | Lowest role that has the context |

### Merge gates

Each gate passes when its purpose holds on frozen heads; its mechanics show how.

| Gate | Purpose | Mechanics |
|---|---|---|
| Checks | The code that merges is the code that was tested | Required checks pass on every frozen head. `no checks reported` proves no pass. A check on another machine follows the Another machine row; never skip it because it runs elsewhere |
| Proof | Each acceptance criterion has evidence a reader can check | [Proof](sop/cook-run.md#proof) puts it untruncated in the PR |
| Review | A reviewer other than the author read every change to shipped behavior | Both loops have APPROVE under [Approval](#approval), no open `blocker` or `should`. Budget end or unresolved dispute is not approval. Fast track passes this gate on its recorded skip |
| Undo | Everything the batch does can be undone: by a revert, by an edit history, or by a restore the Cook ran once | Reverting its PRs undoes its code. A GitHub edit a card requires, e.g. an issue, label or milestone change, keeps its own edit history. Real data the batch or a job it schedules removes or rewrites has the restore proof Shared rules require; with none, it is a hard stop |
| Reach | The merge changes nothing the public sees, or Pascal authorized what it changes | Deploy to Pascal's machines is not public. Deploy to a public site or live service is a hard stop. A required release follows the Release row |
| Judgment | The remaining risk cannot change the result | Apply Pareto 90-10 to work left. Challenge your verdict with 🧰 andy-mode ; sparring. Report confidence, evidence and low-impact remainder |

### Approval

An approval holds until shipped behavior changes. A behavior change goes back through both loops, in parallel: loop 1 on each changed PR, loop 2 on what will merge together. This covers each loop's APPROVE and each `🔀 Merge`. [Loops](sop/cook-run.md#loops) gives each reviewer an immutable base SHA and head SHA.

A restack or a change moved between layers keeps approval when top tree is unchanged on the same base. Compare `git rev-parse <approved-top>^{tree} <new-top>^{tree}` and both base SHAs. Record matching base and tree IDs in Detail; approval then covers the new frozen heads. Each new head still needs its required checks. Otherwise compare shipped behavior under the rule above before another merge decision. Stop voids unused approval.

### Hard stops

Ask Pascal before proceeding with:

1. Real data with no proven restore
2. A change to secrets, auth or billing
3. A deploy that reaches the public
4. Scope: cutting a card, batch or required deliverable, or leaving the agreed repositories, incl. force-pushing a branch the run did not create

Pascal's answer clears a hard stop. So does an advance authorization from Align, while the frozen stack's own diff stays within its approved scope and conditions; record that comparison in Detail. A scope change, cut or Stop voids it.

### Asking Pascal

Only these items produce ❓. One item: label the title `align`, `hard stop <what>`, `fact`, `fault <what>`, `held batch <b>` or `card <card>`. Two or more items: label it `<n> for you`.

1. Align: a question the plan, issues and agreed requirements leave open, at Align or for work added during the run. Never ask Pascal a choice a Decisions row covers
2. A hard stop above. At Align, ask in advance for each one the batch's own cards will hit
3. Fact only Pascal knows, e.g. diagnose's one question when Align did not answer it
4. Fault the brigade cannot repair, incl. a replacement Cook that fails again or a merge that fails twice for the same cause
5. Held batch once nothing else in the run can progress
6. Pascal-owned card ready, per Decisions

Each item is one Canadian French line starting with `🙋`. Use plain words, a recommendation and a link needed to answer. Say why the work needs the answer and what a no would cost: `🙋 Publier le site maintenant : <URL> ? C'est la dernière étape promise ; sinon la nouvelle page reste invisible`. No option menu, long status block, protocol name or cache path. Put open items last in each ❓ turn, above Detail; repost them when they change.

Pascal's reply decides the item it names. A reply naming none applies only to items open when sent. One item: `oui` accepts its recommendation. Several items: `oui` accepts all stated recommendations only when none is a hard stop. Otherwise ask in one line which item Pascal means. Announce accepted recommendations in the next message. Keep a batch with an unanswered hard stop at 🍽️.

## SOPs

Read only the SOP for your current role and step, plus each section it links to.

| SOP | Read when |
|---|---|
| [head-chef](sop/head-chef.md) | Coordinating the run, launching or replacing a Cook, or removing its worktree |
| [cook-run](sop/cook-run.md) | Implementing, running a loop, documenting, proving, babysitting, fixing, a cut or Stop |
| [cook-closing](sop/cook-closing.md) | Applying the merge gate, merging, releasing or closing the batch |
| [watchdog](sop/watchdog.md) | Delegated tick, wake, alert and forbidden-combination checks |
| [manic-1](sop/manic-1.md) | Loop 1 reviewer: adversarial angle |
| [manic-2](sop/manic-2.md) | Loop 1 reviewer: blast-radius angle |
| [manic-3](sop/manic-3.md) | Loop 2 reviewer: docs angle |
| [manic-5](sop/manic-5.md) | Loop 2 reviewer: pristine angle |

## Settings

Read [config.toml](config.toml) for settings and their readers; edit the source copy when changing them.

## Process

Copy the table and check off your role's steps:

| # | Step | Owner and SOP |
|---|---|---|
| 0 | Align and arm Watchdog | Head Chef and Pascal, `head-chef` |
| 1 | For each card in Plan's order: diagnose first for a bug card, implement it on a new stack layer, open its PR, run loop 1 on that PR until it ends; only then start next card | Cook, `cook-run` Implement and Loops |
| 2 | Docs and required release content; loop 1 on each PR this step opens | Cook, `cook-run` Docs |
| 3 | Loop 2 on whole stack or single PR | Cook, `cook-run` Loops |
| 4 | Prove every acceptance criterion; babysit until bots finish and required checks pass or an unconfirmed check is with Head Chef | Cook, `cook-run` Proof |
| 5 | Merge gate, merge and release | Cook, `cook-closing`; Head Chef for `🍽️ Batch ready` |
| 6 | Closing, remove Cook's worktree, then the Watchdog at run end | Cook and Head Chef, `cook-closing` and `head-chef` |

Batch that opens no PR: its Cook does the work, skips the PR part of step 1 and steps 2 to 5, and reports that choice. Fast track skips docs and both loops: Cook implements every card, adds required release content, then goes to step 4.

## Shared rules

- Head Chef plans one stack per batch, putting independent cards in that stack or separate batches. Cook uses 🧰 gh-stack for one PR per card. Assign each PR to `pr-assignee`; 🧰 file-pr writes each description
- Cook is sole writer in its worktree and owns every restack and the merge
- Before a reviewer probe patches an installed dependency, the reviewer asks Cook for a package copy. Cook copies it into a separate private scratch directory per reviewer, without hardlinks or symlinks to installed files. Run the probe against that copy; keep installed packages and shared package caches unchanged
- While a delegate reads your worktree directly, e.g. a Verify run needing uncommitted changes, keep its files, index and commit unchanged until completion or confirmed cancellation. Reviewers use the isolated checkout in Loops
- Put each fix in the layer whose change added the faulty text, even when a later layer also changed its line; for text from trunk, use the layer whose change made it wrong
- Cook follows repository's `AGENTS.md` procedure first; solo skills [cook-run](sop/cook-run.md#solo-recipe) names, starting with 🧰 poteto-mode, fill what it leaves open. Treat issue proposals as drafts: verify each command, flag and message against the tool's source or a throwaway run before copying it. Report each false line and its fix to Head Chef
- Head Chef writes `~/.cache/brigade-<id4>/rules.md` once: the judgment rule that opens [Decisions](#decisions), these Shared rules, [Work folders](#work-folders) and Pascal's standing instructions, leaving out any rule a role's loaded skills already give, e.g. oem's signature line. Every launch message, loop brief and side-delegate brief carries `Rules: <rules.md path>`, plus the additions it inherited and its own. A delegate that tests how an agent acts without the run's context gets a separate `rules.md` with both data-safety rules and only its checkout, work-folder, deletion, repository, concurrency and GitHub limits
- A comment posted via Pascal's account does not wake the Cook's watch; Head Chef also sends it to the Cook with `t3_thread_send`
- When Pascal writes to a Cook directly, act, record the change in Detail and include it in next allowed message to Head Chef
- Keep going without Pascal within agreed repositories and their PRs and issues. The run may push, open or update PRs and issues, and force-push its own branches with `--force-with-lease`. Merge deploys under the merge rule in Decisions and retro issues in Pascal's repositories are allowed
- Before a live proof removes, rewrites or refreshes real data, or before merging a job that will, Cook takes a backup or snapshot, runs the restore path once and checks restored data. Include needed token and API budget. A scheduled job writes and verifies a backup of each item before deleting it, outside every path any scheduled job prunes. Record restore result and backup location in Detail
- Never print the text or diff of a file that can hold a secret, e.g. a shell startup file, keyring template, `.env` or credentials file, context lines included. Record only its path, status and line count; check a move with a count or a hash
- Before retrying a launch, merge, deploy or release, check in T3, GitHub or deploy output whether it already happened
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md

### Retros

For each enabled role, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Each retro files the highest-value issues, up to `retro-max-issues` per thread. Quote in the issue the lines of any log or report it relies on, with command and exit code when there is one; for a screenshot, describe what it shows. Never cite a path under `~/.cache/brigade-<id4>/`, which Close removes. Read the issue back before your final report, while the folder it quotes still exists. Done when each has issue links or a recorded no-findings result.

## Work folders

Use `~/.cache/brigade-<id4>/<thread>/` for temp files and caches, with `TMPDIR` set to its `tmp/` subfolder. `<thread>` is `head-chef`, `cook-<b>.1`, `watchdog-head-chef` or `<task>-<b>.1-<k>`, where a reviewer's `<task>` is `loop-<n>`. Create both folders before work. Keep a Cook's work folder, briefs included, through `🍽️ Batch ready` and any Fix. Remove it before its final report, after any enabled retros: in Closing, Stop or a cut that leaves no card. Remove a reviewer's or side delegate's work folder before its final report, removing its worktree first without `--force`. Before removal, record any branch T3's worktree isolation created for that delegate. After removing the worktree, delete only that run-created local `t3/` branch without escalating, with `git -C <clone> update-ref -d refs/heads/<branch> <literal nonzero isolation commit from the delegation brief>` only when the brief supplies that SHA; keep and report the branch if SHA is missing or guard fails. After the repository's Verify procedure, incl. its cleanup and quote steps in that procedure's order, and before it removes its worktree or work folder, a side delegate copies the evidence the Cook will quote, e.g. a Verify run folder with its command, tested head and exit code, plus ready-to-paste output of the repository's quote step when it has one, into `<Cook work folder>/evidence/<task>/` and reads the copy back there. Only after any required repository cleanup succeeds and the evidence copy passes readback, remove any separate temp run folders the delegate or its tools created for this run outside its work folder, e.g. a Verify run folder. Keep Cook's evidence copy and shared tool caches unchanged; keep and report any folder the repository forbids deleting. If repository's cleanup, quote, copy, readback or removal fails, stop cleanup, keep all remaining folders and report each remaining path with the failure. Cook reads that evidence there, pastes it untruncated into the PR and reads the PR back before Closing removes its own folder; if paste or readback fails, it keeps the folder and reports it. A path under the cache is not evidence. Delete as 🧰 oem says; remove a worktree with `git -C <clone> worktree remove <literal path>`. A thread removes its own folder and the folders of children it launched once they have stopped, except a folder a child reported keeping; Head Chef also removes the run's root. A folder already gone counts as removed. When a removal fails, keep that folder and its parents, and report its path to your parent, which relays it unchanged up to Head Chef. Recreate folders when resumed.

## Model selection

Head Chef selects `[cook]`; Cook selects `[loop-1]` or `[loop-2]` from `config.toml` for each reviewer. Head Chef selects `[watchdog]` for its own Watchdog.

1. Read your selection with `t3_thread_configure`, without `modelSelection`. For a Cook, choose `head-chef-on-claude` or `head-chef-on-codex` from Head Chef's provider. When Pascal asks for a Codex, Sol or DSF (DeepSeek Flash) Cook, in the invocation, at Align or during the run, choose `on-request-codex` or `on-request-dsf` instead, for the batches Pascal names or every batch, and record it with Align choices; a request during the run applies to Cooks not yet launched. For a reviewer, choose `cook-on-claude`, `cook-on-codex` or `cook-on-pi` from Cook's provider. `inherit` keeps your instance, model and reasoning level. Otherwise resolve `instance` to a live provider instance in `orchestrator_capabilities`. Done when provider and model exist
2. Map `reasoning-level` to Codex `reasoningEffort`, claudeAgent `effort` or Pi `thinking`. Map `service-tier` `standard`/`fast` to Codex `serviceTier` `default`/`priority` or claudeAgent `fastMode` `false`/`true`. Send an option only when the model's catalog entry lists it. Table values override top-level defaults. For Cook side work on Claude, use `[cook].delegate-on-claude` via `delegate_task`, unless repository's procedure selects a model for that work, e.g. its Verify delegate; then follow repository's model selection. A Watchdog uses `watch-on-claude` or `watch-on-codex` from its parent's provider, staying on that provider, not following the reviewer rule. Done when catalog supports each option, every reviewer uses the other provider and every Watchdog uses its parent's provider
3. Threads inherit runtime and interaction modes at launch; delegates inherit them from the Cook. Keep `runtime-mode = "inherit"` all run, no mode change. Launches use `modelSelection`; delegations use `target`, renaming `instanceId` to `providerInstanceId`. Escalate an unavailable setting via the chain. Done when selection is supported

## Report

Before sending `🍽️ Batch ready`, `🔀 Batch merging` or a final outcome, each Cook posts a message in its own thread starting with `Detail · <role and id>`, e.g. `Detail · Cook 1.1 7f3a`. Name the frozen heads it covers. Give each acceptance criterion of its cards with its evidence. Record each loop's rounds, reviewer and end, its ledger of fixed, declined and disputed findings with reasons, each merge gate's result, skipped steps, gaps not filed, and exceptional decisions. Post a new `Detail` after a changed head. Head Chef reads that thread and cites its threadId, but does not copy the Detail. Detail survives work-folder cleanup.

A Report message uses only its field set below. Max 8 lines and 1200 characters, plus its `🙋` lines.

A Cook lists its PRs and heads in `🍽️ Batch ready` or `🔀 Batch merging`, and again after a restack. Later messages give the range only if needed to identify a partial outcome.

Head Chef's Close removes the cache folders → a message to Pascal cites only PR, issue and artifact URLs, except a follow-up naming a folder kept after a failed cleanup.

In a message or Detail, write every clock time in America/Montreal time. GitHub and T3 return UTC; convert first.

`🍽️ Batch ready` or `🔀 Batch merging`, Cook → Head Chef:

```text
🍽️ Batch ready · Cook <b>.1 <id4>
PR: #<n> <sha> · #<n> <sha>, checks <state>
Gates: <the doubted gate or open hard stop and your recommendation, or all pass>
Loops: loop 1 APPROVE on <n>/<PRs> PRs, loop 2 <end>; <fixed> fixed, <declined> declined
Not confirmed: <what and the command that would confirm it, or none>
Confidence: <level, evidence and remaining risk>
Detail: <Cook threadId>
For Pascal: <🙋 lines, or none>
```

For `🔀 Batch merging`, replace first line's message. For `⛳ Batch delivered` or `⏹️ Batch stopped`, send outcome, deploy result, Detail threadId and `For Pascal: <items with GitHub URLs, or none>`. Give PR range only for a partial outcome.

Head Chef → Pascal, in Canadian French. At Align, send Align plan below, then any open `🙋` lines. Repeat the `Lot` block per batch in launch order, one line per acceptance criterion; omit an empty line. Align plan has no line limit. For a later ask, send only the `🙋` lines.

```text
Je veux <goal>, pour régler <problem>
Lot <b> · <repository> · après <batches, or aucun> · release <oui/non> · cook <Cook model>
- <card> : <acceptance criterion> → <evidence that will prove it>
Pour toi : <Pascal-owned cards>
🙋 feu vert d'avance lot <b> : <action> pour <why needed> ; sinon <cost of no> · <scope and conditions>
```

Head Chef messages Pascal only for an action in Asking Pascal, a requested status or these notices: Align plan, a merge outcome, withdrawal of a Pascal ask, a long-batch alert, final report and kept folders after cleanup. It never relays that there is nothing to do. A merge or withdrawal notice has at most 3 lines: outcome, PR range and next step.

On a long-batch alert, read cards' PRs and step timings. Send one line: `Lot <b> : <cards with a PR>/<cards> cartes ont une PR, <hours> h, surtout <longest step>`. Compare with previous line. If no new card got a PR, append a recommendation to split, narrow scope or Stop; apply Asking Pascal before cutting scope. Record the line's count in your Detail.

Head Chef records overrides, exceptional calls and authorizations in its Detail. Include it in next allowed message as one `<details>` block after open `🙋` lines, with summary `Detail · Head Chef <id4>`. Write settled asks in prose inside it. Message's line limit excludes Detail. For the final report, use this template:

```text
<⛳ or ⏹️> <done>/<batches> lots livrés : <one-line outcome>
PR fusionnées : <#<n>–#<n>, or aucune>
Reste pour toi : <🙋 lines, decided follow-up work with GitHub URLs after a Stop, then each external_gap machine with its cause and fix command, or rien>
```

`📍` progress, Cook → Head Chef, no reply, at end of each process step: `📍 <card> <step>/6 · <PR URL> · checks <state>`, where `<step>` is the step's number in the [Process table](#process), never in the repository's own checklist. Step 1 sends one line per card. Steps 2 to 6 cover the whole stack: send one line with `stack` as `<card>` and top PR's URL.
