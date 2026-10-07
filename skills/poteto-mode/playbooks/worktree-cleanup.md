---
description: "Reclaim disk space by pruning merged or abandoned git worktrees and stale iOS simulators."
---

### Worktree and simulator cleanup

Read [agent runtime](../references/agent-runtime.md) before choosing delegation, models, skill loading, live controls, state storage, or watchers. Follow its capability checks and report unavailable guarantees.

**You own the disk and the safety gate.** Prune merged or abandoned git worktrees and stale iOS simulators to reclaim space. Deletion is irreversible, so every step guards against deleting something in use or holding uncommitted work.

1. Snapshot and audit. Record `df -h /`, then run `scripts/worktree-audit.sh <repo-path> [transcripts-dir]` with an explicitly project-scoped transcript directory, or `PSTACK_TRANSCRIPTS_DIR` (the **Build the Lever** principle). It reads paths from `git worktree list`, never hand-typed, because worktrees can live outside the repository (the **Encode Lessons in Structure** principle). It answers a `worktrees` list, largest first, that classifies each worktree by size, age, merge state, uncommitted work, PR state, and the newest chat that touched it, then suggests a `bucket`. Missing transcript access means usage is unknown and needs review. Run a slow scan as a monitored background job only when supported.
2. The bucket is advice, not permission. The pinned and active chats are the real artifact (principle-prove-it-works). Get that set from the user or sidebar and cross-check every candidate. The lever has marked `safe` a worktree the user had pinned, so the pinned set wins.
3. Verify usage before deleting. For every worktree in the `verify-recent-chat` bucket, or anything you doubt, fan subagents out to read the transcripts and report whether the chat is pinned or ongoing and which worktrees it touches (the **Guard the Context Window** principle, since transcripts are bulk). A pinned chat spawns arena and repro trees into sibling worktrees via background subagents, and those are in use even when their names never hit the sidebar.
4. Pause on irreversible loss. `wip:N` is N tracked uncommitted edits. Show the diff and get a decision first, since removing a clean worktree is recoverable from its branch but uncommitted work is gone. `scratch:N` is untracked throwaway, safe to drop, but name the files. Per Autonomy, clean and merged and not-in-use proceeds. `wip` and in-use pause.
5. Prune the confirmed set. Per path, `git worktree remove --force <path>`. If the dir survives on ignored build artifacts, `rm -rf` it, then `git worktree prune`. Branch refs survive, so no commits are lost. Confirm with `df -h /` and re-list.
6. Simulators and other reclaimers. Simulators are usually the next-biggest win. `xcrun simctl --set testing delete all` (XCTestDevices clones), `xcrun simctl delete unavailable`, and `xcrun simctl runtime list` then `runtime delete <id>` for old runtimes. More when needed: Xcode `DerivedData` and `iOS DeviceSupport`, verified disposable caches for the active harness, and package caches (pnpm, uv, brew). Clear only caches the user has not said to keep.

This is the one playbook that deletes user state with no code review to catch a slip, so the gates above are the review.

**Reply:** `df -h /` before and after with space reclaimed, the worktrees pruned, and a one-line reason for each held back (in-use by which chat, or uncommitted work).
