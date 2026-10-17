# cook-review

The Cook stays 🍳 during barrages and triage. Apply [Statuses and Messages](../carpaccio.md#statuses) at phase entry and turn end.

## Delegate

1. Run each pair through 🧰 interrogate as its lead, with one reviewer per barrage: manic-1 plus manic-2 after Implement; manic-3 plus manic-5 after Docs. Select each barrage with shared Model selection. manic-3 keeps its technical-writing method. Give the pair the same evidence snapshot at the stack's current heads. Done when every target is supported and both briefs use the same recorded heads
2. Delegate each review pair:
   - For each pass, call `delegate_task` with `mode: "async"`, `role: "review"`, the target and the brief below. Copy the barrage title from Roles word for word
   - Use `clientRequestId: <id4>-<b>.<c>-<sop>-<k>`; `<k>` counts this Cook's delegations from 1 without resetting. Reuse the key only to retry that call
   - Retain each taskId. Submit a pair in the same turn
   - Write `<work folder>/wait` with both taskIds, then end your turn for completion notifications
   - When both results arrive, remove the wait file

   Done when every requested pass has a taskId and the wait file names every active pass

```text
$brigade-mode ; carpaccio ; <sop>
Role: Barrage <sop>, delegation <k>, Cook <b>.<c> <id4>. Your final message is your report.
Scope: <absolute Cook worktree>, <base branch>, <branch/head pairs>, <PR URLs>
Plan: <cards, acceptance criteria and batch threat model>
Intent: <one paragraph stating the intended behavior>
Evidence: <context the reviewer needs beyond the diff defined by Scope>
Docs: <Cook's docs PR or no-docs decision, for manic-3>
Prior rounds: <original brief, findings, decisions, fixes with commits and unresolved objections>
Rules: <rules.md path, plus additions>
Work folder: <absolute path>
Contract: Review only; edit no project file. Work alone, with no subagent or other model. Execute code only in a detached worktree inside your work folder. Never move a Cook branch ref: no checkout, commit, rebase, reset or push that touches it. A trial rebase follows gh-stack with git -c rebase.updateRefs=false; abort it on conflict. Respect prior decisions unless new evidence reopens them. Give each finding its severity, file, line and proposed fix. Run 🧰 2nd-pass on your findings, then list open questions in your report.
```

## Triage

1. Wait for all currently running passes on the same heads, then use interrogate's `references/lead-judgment.md` to categorize every finding with a one-line reason: accept `Act on`; carry `Consider` in your Detail message for the Chef; reject `Noted` and `Dismissed` with their reasons. Keep reviewer attribution and what each checked in the verdict. Treat a CI failure or conflict as an accepted finding; judge external reviews like barrage findings. Done when every result and watch wake has a recorded decision
2. Apply accepted findings through `cook-implement` Fix. Each barrage keeps its decisions and counts its own normal passes against `max-passes`. If a fix needs review and passes remain, delegate a fresh pass with the full brief and prior rounds. Otherwise record why its review ended. Done when each review ended or a new taskId is recorded
3. When the last allowed pass yields any fix, including docs, delegate one extra pass limited to that fix. This pass is final; list any fix it yields under what you could not confirm. Done when that final result is triaged and any unreviewed fix is reported

Do not commit while any barrage runs in your worktree. Queue watch findings while passes are running, then triage them with those results. When none is running, triage watch findings at once; fast track retains its skips. A failed or interrupted pass remains unconfirmed: retry it with a fresh delegation or report the blocker to the Chef before readiness.

Advance to the next process step only when every review in the current pair has ended with its reason recorded.
