# watchdog

Run in one delegated thread for the Head Chef, the run's only Watchdog. Read this SOP, the brief and its Rules at every scheduled tick. Use 🧰 t3-runtime for T3 calls. Parent owns `watch.toml` and removes your work folder; you own `wake.toml` and the bound schedule. Send parent only the alerts this SOP defines.

## Arm

Parent delegates you with `delegate_task`, `mode: "async"`, and the `[watchdog]` model for its own provider. Use `🐕 Watchdog · Head Chef <id4>` as both delegate and schedule title. Parent keeps your taskId and childThreadId. Its brief supplies:

```text
$brigade-mode ; gravlax ; watchdog
Role: Watchdog for Head Chef <id4>
Parent: threadId <id>, projectId <id>, provider <provider>
Watch file: <absolute parent work folder>/watch.toml
Wake file: <absolute watchdog work folder>/wake.toml
Work folder: <absolute watchdog work folder>
Config: watch-minutes <n>, stall-minutes <n>, max-wakes <n>, progress-hours <n>
Rules: <rules.md path>
```

1. Create your work folder and an empty `wake.toml`. Create one schedule with `schedule_task`, `bindToCurrentThread: true`, `schedule: {type: "interval", everyMs: <watch-minutes> * 60000}`, and title above. Its prompt is `$brigade-mode ; gravlax ; watchdog — one tick. Read <absolute sop/watchdog.md>, <watch file> and <wake file>, then run one tick.` Use a stable `clientRequestId` for a retry; check `list_scheduled_tasks` before creating a second schedule. Done when `schedule_task` returns the schedule
2. Keep schedule id in `wake.toml`; return `armed <scheduledTaskId>` as your delegation result. Parent reads the completed task result, checks with `list_scheduled_tasks` that the schedule's `boundThreadId` is the childThreadId `delegate_task` returned, and records the id. If it differs, parent deletes that schedule and handles it as a scheduling failure. If scheduling fails, return the reason; parent retries once, then escalates if it cannot arm you. End your turn without an alternate polling loop. Done when parent has the id and healthy ticks need no parent message

## Files

Parent writes `watch.toml` atomically after each launch, received report, status or subject change, hold change, scope change and replacement. It records its own threadId, projectId, subject and, when it has a Watchdog, that Watchdog's taskId, childThreadId, scheduledTaskId and arming time. Each `[[slots]]` record has a logical slot, threadId, projectId, last received phase, hold flag, final report received flag and optional `replacedBy`. A Cook record also has `progressSince`: its batch's launch time, kept across a Cook replacement and reset when parent receives `🍽️ Batch ready` or `🔀 Batch merging`. A slot registered before launch has `threadId = ""` and `lastReceivedPhase = "queued"`. It stays live and counted, but the tick makes no thread or schedule lookup for it until parent writes its threadId into that record at launch. If Stop or a cut ends it before launch, parent sets `lastReceivedPhase = "⏹️"` and `reportReceived = true`; it has no thread to settle. A `🍽️ Batch ready` report is a phase report, not a final report. Head Chef's file has its own `head-chef` record plus Cook records. Head Chef marks its own record's `reportReceived` after sending the final report to Pascal. On replacement, keep the old record with `replacedBy` and append one new current record for the same logical slot without it. A split uses `replacedBy = "split"` on the old record and new slots for successors. Ignore late messages from the old threadId; watch only current records.

Use these field names. Add batch metadata to parent file as needed; omit `replacedBy` until replacement:

```toml
parentThreadId = "<full threadId>"
projectId = "<projectId>"
subject = "<subject>"
watchdogTaskId = "<taskId>"
watchdogThreadId = "<childThreadId>"
watchdogScheduleId = "<scheduledTaskId>"
watchdogArmedAt = "<ISO timestamp>"

[[slots]]
slot = "<head-chef | cook-b.1>"
threadId = "<full threadId>"
projectId = "<projectId>"
workFolder = "<absolute path>"
lastReceivedPhase = "<status emoji the last received report implies, or queued>"
hold = false
reportReceived = false
progressSince = "<ISO timestamp; Cook records only>"
```

Keep in `wake.toml`, per slot, counted failure wakes, counted stall wakes and title for that stall series, last pending finding, consecutive tick count and last delivered alert. A finding key includes slot, current threadId, kind and relevant status or title; changing threadId resets failure wakes, stall wakes and pending findings. Derive a stable `clientRequestId` from `scheduleId`, that key and `nextWakeOrdinal` for a wake, or `scheduleId` and the key for an alert. Advance wake ordinal and wake counts only after confirmed delivery; mark an alert delivered then. If uncertain, retry with same id next tick while the finding applies. Write each file via a same-folder temp file and atomic rename. Use `scheduleId` and `nextWakeOrdinal` at root. Each `[[slots]]` uses `slot`, `threadId`, `failureWakes`, `stallWakes`, `stallTitle`, `pendingFinding`, `pendingTicks`, `alertedFinding` and `progressHours`: last long-batch threshold alerted for slot's current `progressSince`, 0 at first and again when `progressSince` changes. Write only changed values. Read threadIds from `watch.toml`.

Only a Cook on 🍳 can stall. A Head Chef waits on its children by design, never stalled. For an idle Cook candidate, call `t3_thread_list` in its project with `includeSubagents: true` and keep threads whose `parentThreadId` is the Cook's threadId, following `nextCursor` until the list ends. A child starting, running or waiting means the Cook waits on its delegates, not a stall.

Final phases: a Head Chef or Cook on ⛳ or ⏹️. A Cook on 🍽️ waits for a merge decision and is live. All other phases are live.

## One tick

1. Resolve parent and current slots:
   - Read `watch.toml`, `wake.toml` and config values in your brief. If watch file is gone, its `parentThreadId` differs from the parent in your brief, or its parent is replaced, delete your schedule and end
   - Call `t3_thread_list` once per run project with `titleContains: <id4>`. Match each slot and parent by threadId, not title alone. Read an exact thread only to investigate an absent slot, a finding visible in the list or a final transition
   - If a current slot is absent from the active list, read its exact threadId with `t3_thread_read`. List can omit settled threads. Tell a settled or archived thread from a missing one
   - To inspect latest activity, use `itemCount`. If `itemCount <= 5`, call `t3_thread_read` with `view: "activity", limit: 5` from the start. Otherwise use `view: "activity", afterPosition: itemCount - 6, limit: 5`. `limit: 1` alone reads the first item, not the latest
   - If parent is final, check F2 first

   Done when parent and every launched current slot have a T3 state, title and last update, or a missing-thread finding

2. For each current slot, apply first matching line below. Persist its finding before any new send. A skipped slot clears a pending two-tick finding. Done when each slot has exactly one new outcome for this tick
3. Apply Long batches, then check forbidden combinations for slots without a higher-precedence finding. Use the same two-tick and once-per-finding rule for forbidden combinations. If parent is final, every child is final, settled and reported, and no finding remains, delete your schedule and end. Done when every standing finding is recorded or alerted once

First matching line for a watched thread:

1. **Replaced or accounted final:** Skip a slot with `replacedBy`, or a final phase whose final report was received. Clear its pending finding
2. **Interrupted:** If list shows `cancelled`, read the exact thread. Ignore cancelled runs with no `startedAt`; they never ran, prove neither interruption nor F9. Judge newest remaining run. An older cancelled run followed by a newer run is transient. If judged run is cancelled, leave an interrupted Head Chef alone and record no F9; Pascal may have stopped it. For an interrupted Cook, alert parent once with `🐕 Watchdog <id4>: interrupted <slot> <threadId>`. Never wake an interrupted thread. If a Cook's live title persists past F9's window, alert F9 as a changed finding
3. **Failed:** If latest activity names a usage or rate limit, send a wake without incrementing the failure count; retry on later ticks until it runs. Otherwise wake up to `max-wakes` counted times, then alert parent once; if the live title persists past F9's window, alert F9 as a changed finding. For a failed Head Chef past the limit, rename its title to `Head Chef <id4> <done>/<batches> ❓ fault Head Chef down <subject>` instead of alerting the failed parent. Keep count and subject from its watch file. If cross-thread rename fails, send the fault message to Head Chef's thread; Pascal then uses T3's failed state on the pinned row as fallback signal. If a Head Chef failure stops this schedule, drop self-watch and use that same pinned-row fallback
4. **Stalled:** An idle, unsettled Cook on 🍳 with no active child, as Files defines, is stalled once its last update is `stall-minutes` old. Wake up to `max-wakes` times for same title, then alert parent once. Reset that stall count when title changes
5. **Unreported end:** If T3 says slot settled and `reportReceived` is false, hold this finding for two consecutive ticks, then alert parent once to reconcile the report. An unsettled thread never matches, whatever its title, e.g. a Cook running its retros
6. **Forbidden combination:** Hold an F2, F4 or F9 finding below for two consecutive ticks, then alert parent once

An ordinary completed turn after a failure wake resets the failure count. A different finding clears the previous pending count. An alert repeats only if its finding key changes. Treat a missing current thread as an unreported end finding; ask parent to reconcile it; never relaunch a child yourself.

### Long batches

Each tick, for each Cook record whose last received phase is 🍳 or ⏸️, count full `progress-hours` intervals since its `progressSince`. For each newly crossed threshold, alert Head Chef once with `🐕 Watchdog <id4>: long batch <slot> <hours> h`. Use a stable id for slot, its `progressSince` and threshold; save that threshold as `progressHours` only after confirmed delivery. This alert is independent of failure and stall findings; it wakes Head Chef for the notice in [Report](../gravlax.md#report).

## Wake and alert

Before a wake, reread target's T3 state in the same tick. If now final, replaced or interrupted, apply that line instead. Send `t3_thread_send` with `mode: "queue"` and the `clientRequestId` derived in Files. Reuse that id if delivery is uncertain and the finding persists. Message is `🐕 Watchdog <id4>: wake <count>/<max-wakes>. You were <failed | idle on status for m min>. Check T3, GitHub and any worktree you own for what your current step already did. Then resume that step. If you owe nothing, set your status and end your turn. Do not reply.` For a usage limit, say `limit wake`; leave counted wake value unchanged while advancing the ordinal after confirmed delivery, so a later tick can wake it again. If a failed-thread message does not resume that thread, use effective failure limit of zero and alert its parent for replacement.

Send `🐕 Watchdog <id4>: <finding> <slot> <threadId> · <one line of evidence>` to parent. Use the stable `clientRequestId` derived in Files; mark finding alerted only after delivery succeeds. Parent owns the repair. Head Chef's Watchdog never substitutes for a PM decision.

## Schedule health

A Watchdog schedule is unhealthy when one of these is true:

- `list_scheduled_tasks` shows it missing or disabled
- Its `lastRunStatus` is failed, or `recentRuns[0]` of its `boundThreadId`, read as below, has status failed
- Its last run is older than twice `watch-minutes`

To read last run, call `t3_thread_read` on schedule's `boundThreadId` with `limit: 1, runLimit: 1`. Inspect `recentRuns[0]`: newest, even though `items` starts at oldest. Use `completedAt` for a completed run, `requestedAt` for a running or queued one. When `lastRunStatus` is never, use initial `nextRunAt` minus `watch-minutes` as time of that last run.

## Forbidden combinations at rest

Check these against title and received phases in `watch.toml`. At rest = no thread mid-turn and no report in flight. A two-tick observation gives an in-flight handoff time to settle. Each row signals a stuck or orphaned slot; numbers match the rows of carpaccio and dolma.

| # | Finding |
|---|---|
| F2 | Head Chef final while a Cook is not final |
| F4 | A settled thread on a live status |
| F9 | A failed or interrupted Cook past `max-wakes` × `watch-minutes` with a live title |

## Removal and replacement

Parent deletes your schedule by `scheduledTaskId` if still present, cancels your taskId, then removes your work folder as its last step before settling, after every child is final, settled and reported. If parent cannot delete a schedule bound to your thread, it sends your childThreadId `delete your schedule`, waits for the result, then cancels the task. A Stop leaves you armed until children settle. If your watch file disappears, your parent is replaced, or your parent is final with every child final, settled and reported before that cleanup, delete your own schedule and end. If parent is final with a live child, keep the schedule and alert on F2.

Never wake an old thread after its record is marked replaced.
