# cook-review

## Delegate

1. Select each barrage with shared Model selection. Record the stack's current heads and the passes needed: manic-1 plus manic-2 after Implement; manic-3 plus manic-5 after Docs. Done when every target is supported and every brief identifies the same heads
2. For each pass call `delegate_task` with `mode: "async"`, `role: "review"`, the target, title from Roles and brief below. Use `clientRequestId: <id4>-<b>.<c>-<sop>-<k>`; `<k>` counts this Cook's delegations from 1 without resetting. Reuse the key only to retry that call. Retain each taskId. Submit a pair in the same turn, then end your turn for completion notifications. Done when every requested pass has a taskId

```text
$brigade-mode ; carpaccio ; <sop>
Role: Barrage <sop>, pass <k>, Cook <b>.<c> <id4>. Your final message is your report.
Scope: <absolute Cook worktree>, <base branch>, <branch/head pairs>, <PR URLs>
Plan: <cards, acceptance criteria and batch threat model>
Docs: <Cook's docs PR or no-docs decision, for manic-3>
Prior rounds: <original brief, findings, decisions, fixes with commits and unresolved objections>
Contract: Review only; edit no project file. Execute code only in a detached worktree inside your work folder. Never move a Cook branch ref: no checkout, commit, rebase, reset or push that touches it. A trial rebase follows gh-stack with git -c rebase.updateRefs=false; abort it on conflict. Respect prior decisions unless new evidence reopens them. Give each finding its severity, file, line and proposed fix. Run 🧰 2nd-pass on your findings, then list open questions in your report.
```

## Triage

1. Wait for all currently running passes on the same heads, then accept or reject every finding with a one-line reason. Treat a CI failure or conflict as an accepted finding; decide on external reviews like barrage findings. Done when every result and watch wake has a recorded decision
2. Apply accepted findings through `cook-implement` Fix. Each barrage keeps its decisions and counts its own normal passes against `max-passes`. If a fix needs review and passes remain, delegate a fresh pass with the full brief and prior rounds. Otherwise record why its review ended. Done when each review ended or a new taskId is recorded
3. When the last allowed pass yields a code fix, delegate one extra pass limited to that fix. This pass is final; list any fix it yields under what you could not confirm. Done when that final result is triaged and any unreviewed fix is reported

Do not commit while any barrage runs in your worktree. Queue watch findings while passes are running, then triage them with those results. When none is running, triage watch findings at once; fast track retains its skips. A failed or interrupted pass remains unconfirmed: retry it with a fresh delegation or report the blocker to the Chef before readiness.

Advance to the next process step only when every review in the current pair has ended with its reason recorded.
