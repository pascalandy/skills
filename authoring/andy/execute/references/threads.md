# Threads route

MAIN is the T3 thread I talk to.

## Names

The T3 roles in `AGENTS.md` define each role. Each thread title follows this format, where `<id4>` is the last 4 characters of MAIN's threadId and `<n>` counts each role's threads from 1, in launch order:

- `👑 MAIN <id4> <title>`
- `🐝 COD<n> <id4>`
- `👀 RVW<n> <id4>`
- `📚 DOC<n> <id4>`

## Who runs each step

| Step | Who and how |
|---|---|
| Start | MAIN renames itself `👑 MAIN <id4> <title>` with `t3_thread_update` action `rename` before it launches any thread, then follows the T3 workflow in `AGENTS.md`: names, `t3_thread_launch` at root, `git -C`, `link_pull_request`, and reports through `t3_thread_send` |
| Execute, Self-check | One 🐝 COD per card in the plan |
| Blast-radius impacts | One 👀 RVW per card, on that card's PRs. MAIN writes its own premortem and relays each fix to the owning COD |
| Code review across the whole stack | One 👀 RVW per stack, bound to its COD's worktree (`workspaceStrategy` `existing_worktree`) while the COD stays idle. The COD then keeps or reverts each change, as Reviews in `SKILL.md` says |
| Docs | One 📚 DOC per repository whose docs change, bound to the worktree of that repository's COD while the COD stays idle. It opens the docs PR as the top layer of the stack with 🧰 gh-stack |
| Final review | One 👀 RVW per stack, from base to top, with the **report** ending. MAIN relays each finding to the COD or DOC that owns its layer |
| Report, Closing | MAIN |
| Merge | MAIN relays the go to each COD, which lands its stack with 🧰 poteto-mode ; shipping through the project's merge command. MAIN settles each thread with `t3_thread_organize` action `settle` once `t3_thread_wait` confirms its turn ended |

## Launch

- Each launch message carries MAIN's full threadId, the worktree paths and PR URLs the thread needs, and:
	- for a 🐝 COD or a 📚 DOC: the plan or its card, and its steps and the Rules copied from `SKILL.md`
	- for a 👀 RVW: its brief and ending
- Every 👀 RVW sets `modelSelection` in `t3_thread_launch`:
	- MAIN on Claude: provider `codex`, model `gpt-6.1-sol`, `reasoningEffort` `xhigh`
	- MAIN on Codex: provider `claudeAgent`, model `claude-opus-5-5`, `effort` `xhigh`
- 🐝 COD and 📚 DOC inherit MAIN's model

## Relays

- MAIN never edits code. It relays each finding to the thread that owns the layer with `t3_thread_send`. The owner fixes, commits, restacks, pushes, and reports back
- A thread that must stop and ask reports to MAIN, and MAIN asks me
- Rule override: MAIN's threads may force-push with `--force-with-lease` any branch that one of this MAIN's threads created. Stop and ask before force-pushing any other branch
