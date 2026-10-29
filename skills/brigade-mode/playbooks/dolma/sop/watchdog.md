# watchdog

Run in one delegated thread for the Head Chef or one Chef. Read this SOP and the brief at every scheduled tick. Use 🧰 t3-runtime for T3 calls. The parent owns `watch.toml` and removes the Watchdog's work folder; you own `wake.toml` and the schedule bound to your thread. Keep the parent's context quiet while the watched threads are healthy.

## Arm

The parent delegates you with `delegate_task`, `mode: "async"`, and the `[watchdog]` model for its own provider. Use `🐕 Watchdog · Head Chef <id4>` or `🐕 Watchdog · Chef <b> <id4>` as both delegate and schedule title. The parent retains your taskId and childThreadId. Its brief supplies:

```text
$brigade-mode ; dolma ; watchdog
Role: Watchdog for <Head Chef | Chef b> <id4>
Parent: threadId <id>, projectId <id>, provider <provider>
Watch file: <absolute parent work folder>/watch.toml
Wake file: <absolute watchdog work folder>/wake.toml
Work folder: <absolute watchdog work folder>
Config: watch-minutes <n>, stall-minutes <n>, max-wakes <n>, max-wait-minutes <n>
Rules: <rules.md path>
```

1. Create your work folder and an empty `wake.toml`. Create one schedule with `schedule_task`, `bindToCurrentThread: true`, `schedule: {type: "interval", everyMs: <watch-minutes> * 60000}`, and the title above. Its prompt is `$brigade-mode ; dolma ; watchdog — one tick. Read <absolute sop/watchdog.md>, <watch file> and <wake file>, then run one tick.` Use a stable `clientRequestId` for a retry and check `list_scheduled_tasks` before creating a second schedule. Done when `schedule_task` returns the schedule
2. Keep the schedule id in `wake.toml` and return `armed <scheduledTaskId>` as your delegation result. The parent reads the completed task result, checks with `list_scheduled_tasks` that the schedule's `boundThreadId` is the childThreadId that `delegate_task` returned, and records the id. If it differs, the parent deletes that schedule and handles it as a scheduling failure. If scheduling fails, return the reason; the parent retries once, then escalates if it cannot arm you. End your turn without an alternate polling loop. Done when the parent has the id and healthy ticks need no parent message

## Files

The parent writes `watch.toml` atomically after each launch, received report, status or subject change, hold change, scope change and replacement. It records its own threadId, projectId, subject and, when it has a Watchdog, that Watchdog's taskId, childThreadId, scheduledTaskId and arming time. Each `[[slots]]` record has a logical slot, threadId, projectId, last received phase, hold flag, final report received flag and optional `replacedBy`. A slot registered before its launch has `threadId = ""` and `lastReceivedPhase = "queued"`. It stays live and counted, but the tick makes no thread or schedule lookup for it until the parent writes its threadId into that record at launch. If Stop or a cut ends it before launch, the parent sets `lastReceivedPhase = "⏹️"` and `reportReceived = true`; it has no thread to settle. A `🍽️ Stack ready` report is a phase report, not a final report. The Head Chef's file has its own `head-chef` record plus Chef records; a Chef's file has its Cook's records. The Head Chef marks its own record's `reportReceived` after sending the final report to Pascal. On replacement, retain the old record with `replacedBy` and append one new current record for the same logical slot without it. A split uses `replacedBy = "split"` on the old record and new slots for the successors. Ignore late messages from the old threadId; watch only current records.

Use these field names. Add batch metadata to the parent file as needed; omit `replacedBy` until replacement:

```toml
parentThreadId = "<full threadId>"
projectId = "<projectId>"
subject = "<subject>"
watchdogTaskId = "<taskId>"
watchdogThreadId = "<childThreadId>"
watchdogScheduleId = "<scheduledTaskId>"
watchdogArmedAt = "<ISO timestamp>"

[[slots]]
slot = "<head-chef | chef-b | cook-b.c>"
threadId = "<full threadId>"
projectId = "<projectId>"
workFolder = "<absolute path>"
lastReceivedPhase = "<status emoji the last received report implies, or queued>"
hold = false
reportReceived = false
```

Keep in `wake.toml`, per slot, the counted failure wakes, counted stall wakes and the title for that stall series. Also keep the last pending finding and its consecutive tick count, and the last delivered alert. A finding key includes the slot, current threadId, kind and relevant status or title; changing threadId starts new counters. Derive a stable `clientRequestId` from `scheduleId`, that key and the saved `nextWakeOrdinal` for a wake, or from `scheduleId` and the key for an alert. Advance the ordinal and count a wake only after T3 confirms delivery; mark an alert delivered only after confirmation. If delivery is uncertain, recompute the live finding next tick and retry with the same id only while it still applies. The parent and Watchdog write their respective files through a temporary file in the same folder followed by an atomic rename. Use `scheduleId` and `nextWakeOrdinal` at the root. In each `[[slots]]`, use `slot`, `threadId`, `failureWakes`, `stallWakes`, `stallTitle`, `pendingFinding`, `pendingTicks` and `alertedFinding`. Add no other key. Write the file only when a value changes. Read each threadId from `watch.toml`. Never build a threadId.

A watched status is 🍳, 🔀, 🧹 or 🟢, or ⏳ for a Chef with no counted Cook on 🍳 or ⏸️. A watched thread writes `<its work folder>/wait` before it ends a turn on a watched status to wait. It can wait for delegates, a PR watch, a check or a child. Write the dependency, its task or thread ids and the current time after setting the title, and refresh it when the wait remains active. Remove it when the wait ends. For an idle stalled candidate, read with `t3_thread_read` the `startedAt` of its newest run that has one. The wait file protects it only when its modification time is at or after that turn's start and its age is less than `max-wait-minutes`. T3 updates the thread after the turn ends, so comparing the file to the thread's last update would reject a wait written during that turn.

Final phases: a Head Chef or Chef on ⛳ or ⏹️; a Cook on ⏹️, or on 🍽️ only after T3 shows it settled. An unsettled Cook on 🍽️ is live readiness, not an unreported end. All other phases are live.

## One tick

1. Resolve the parent and current slots:
   - Read `watch.toml`, `wake.toml` and the config values in your brief. If the watch file is gone, its `parentThreadId` differs from the parent in your brief, or its parent is replaced, delete your schedule and end
   - Call `t3_thread_list` once per run project with `titleContains: <id4>`. Match each slot and the parent by threadId, not title alone. Read an exact thread only to investigate an absent slot, a finding visible in the list or a final transition. A Chef's parent is read for combination checks; only its Head Chef's Watchdog wakes it
   - If a current slot is absent from the active list, read its exact threadId with `t3_thread_read`. The list can omit settled threads. Distinguish a settled or archived thread from a missing thread
   - To inspect the latest activity, use `itemCount`. If `itemCount <= 5`, call `t3_thread_read` with `view: "activity", limit: 5` from the start. Otherwise use `view: "activity", afterPosition: itemCount - 6, limit: 5`. `limit: 1` alone reads the first item, not the latest
   - If the parent is final, check F2 or F3 first

   Done when the parent and every launched current slot have a T3 state, title and last update, or a missing-thread finding

2. For each current slot, apply the first matching line below. Persist its finding before any new send. A skipped slot clears a pending two-tick finding. Done when each slot has exactly one new outcome for this tick
3. Check the Chef Watchdog schedules if you watch the Head Chef. Check forbidden combinations only for slots without a higher-precedence finding. Use the same two-tick and once-per-finding alert rule for both checks. If the parent is final, every child is final, settled and reported, and no finding remains pending or active, delete your schedule and end. Done when every standing finding is recorded or alerted once

First matching line for a watched thread:

1. **Replaced or accounted final:** Skip a slot with `replacedBy`, or a final phase whose final report was received. A Cook's 🍽️ at readiness is still live until Closing and settlement. Clear its pending finding
2. **Interrupted:** If the list shows `cancelled`, read the exact thread. Ignore cancelled runs with no `startedAt`; they never ran and prove neither an interruption nor F9. Judge the newest remaining run. An older cancelled run followed by a newer run is transient. If the judged run is cancelled, leave an interrupted Head Chef alone and record no F9; Pascal may have stopped it. For an interrupted Chef or Cook, alert the parent once with `🐕 Watchdog <id4>: interrupted <slot> <threadId>`. Never wake an interrupted thread. If a Chef's or Cook's live title persists past F9's window, alert F9 as a changed finding
3. **Failed:** If the latest activity names a usage or rate limit, send a wake without incrementing the failure count, and retry on later ticks until it runs. Otherwise wake up to `max-wakes` counted times, then alert the parent once; if the live title persists past F9's window, alert F9 as a changed finding. For a failed Head Chef past the limit, rename its title to `Head Chef <id4> <done>/<batches> ❓ fault Head Chef down <subject>` instead of sending an alert to the failed parent. Preserve the count and subject from its watch file. If cross-thread rename fails, send the fault message to the Head Chef's thread; Pascal then uses T3's failed state on the pinned row as the fallback signal. If a Head Chef failure stops this schedule, drop self-watch and use that same pinned-row fallback
4. **Stalled:** An idle, unsettled thread on a watched status is stalled at `stall-minutes` unless it has a fresh wait file. A parent on 🔀 or 🧹 with a nonfinal child is waiting by design. Wake up to `max-wakes` times for the same title, then alert the parent once. Reset that stall count when the title changes
5. **Unreported end:** If the role's phase is final as defined above or T3 says settled, and `reportReceived` is false, hold this finding for two consecutive ticks, then alert the parent once to reconcile the report
6. **Forbidden combination:** Hold an F1–F11 finding below for two consecutive ticks, then alert the parent once

An ordinary completed turn after a failure wake resets the failure count. A different finding clears the previous pending count. An alert repeats only if its finding key changes. Treat a missing current thread as an unreported end finding and ask the parent to reconcile it; never relaunch a child yourself.

## Wake and alert

Before a wake, reread the target's T3 state in the same tick. If it is now final, replaced or interrupted, apply that line instead. Send `t3_thread_send` with `mode: "queue"` and the `clientRequestId` derived in Files. Reuse that id if delivery is uncertain and the finding persists. The message is `🐕 Watchdog <id4>: wake <count>/<max-wakes>. You were <failed | idle on status for m min>. Check T3, GitHub and any worktree you own for what your current step already did. Then resume that step. If you owe nothing, set your status and end your turn. Do not reply.` For a usage limit, say `limit wake` and leave the counted wake value unchanged while advancing the ordinal after confirmed delivery, so a later tick can wake it again. If a failed-thread message does not resume that thread, use an effective failure limit of zero and alert its parent for replacement.

Send `🐕 Watchdog <id4>: <finding> <slot> <threadId> · <one line of evidence>` to the parent. Use the stable `clientRequestId` derived in Files; mark the finding alerted only after delivery succeeds. The parent owns the repair. The Head Chef's Watchdog never substitutes for a PM decision.

For each launched live Chef, read `watch.toml` in its Chef record's `workFolder`. Skip its Watchdog schedule check only when that file is readable and lists no current Cook slot. Otherwise find `🐕 Watchdog · Chef <b> <id4>` with `list_scheduled_tasks` in that Chef's project. When that schedule is unhealthy under [Schedule health](#schedule-health), alert the Head Chef once. The Head Chef asks that Chef to re-arm it. A Chef without a Cook slot stays watched through its Chef record.

## Schedule health

A Watchdog schedule is unhealthy when one of these is true:

- `list_scheduled_tasks` shows it missing or disabled
- Its `lastRunStatus` is failed, or `recentRuns[0]` of its `boundThreadId`, read as below, has status failed
- Its last run is older than twice `watch-minutes`

To read the last run, call `t3_thread_read` on the schedule's `boundThreadId` with `limit: 1, runLimit: 1`. Inspect `recentRuns[0]`, which is newest even though `items` starts at the oldest. Use `completedAt` for a completed run and `requestedAt` for a running or queued one. When `lastRunStatus` is never, use the initial `nextRunAt` minus `watch-minutes` as the time of that last run.

## Forbidden combinations at rest

Check these against the title and received phases in `watch.toml`. At rest means no thread is mid-turn and no report is in flight. A two-tick observation gives an in-flight handoff time to settle. A hold in the watch file permits F5's exception.

| # | Finding |
|---|---|
| F1 | Head Chef ⏸️ |
| F2 | Head Chef final while a Chef is not final |
| F3 | Chef final while a Cook is not final |
| F4 | A settled thread on a live status |
| F5 | Chef 🍽️ while Head Chef is not ❓, outside a hold |
| F6 | Chef 🍽️ below 1/1 |
| F7 | A child ⏸️ under an idle parent on ⏳ |
| F8 | ❓ on a Chef or a Cook |
| F9 | A failed or interrupted Chef or Cook past `max-wakes` × `watch-minutes` with a live title |
| F10 | A parent ⛳ below x/x |
| F11 | A Chef on 🔀 or 🧹 with a Cook on 🍳 or ⏸️ |

## Removal and replacement

The parent deletes your schedule by `scheduledTaskId` if still present, cancels your taskId, then removes your work folder as its last step before settling, after every child is final, settled and reported. If the parent cannot delete a schedule bound to your thread, it sends your childThreadId `delete your schedule`, waits for the result, then cancels the task. A Stop leaves you armed until the children settle. If your watch file disappears, your parent is replaced, or your parent is final with every child final, settled and reported before that cleanup, delete your own schedule and end. If the parent is final with a live child, keep the schedule and alert on F2 or F3.

Before a Chef is replaced, the Head Chef follows [Replace a Chef](head-chef.md#replace-a-chef) to stop any old Watchdog by its bound thread; only the owning Chef can call `task_cancel` on that task. The new Chef reuses the work folder but creates a new watch file and arms a Watchdog only when it has a current Cook slot. If an old tick sees a new `parentThreadId`, it deletes its own schedule and ends. Do not wake an old thread after its record is marked replaced.
