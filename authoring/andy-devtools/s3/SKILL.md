---
name: "s3"
description: "Use only when explicitly invoked as `s3`, alone or followed by `;` and an SOP name, where `s3` may be any voice-to-text spelling that sounds like it, such as `S 3` or `S three`."
kind: "dev"
---

# s3

S3 is how Pascal works in T3 Code. From the `projects` desk, Pascal talks only to a MAIN thread, which launches the threads that do the work.

## Vocabulary

- **CU**: a use case. It shows the dynamics between Pascal and the threads, as a process and a sequence diagram. Each step names the SOP its thread follows
- **SOP**: a procedure one thread runs, in `references/sop/`. Each file name starts with the role that runs it
- **Card**: a unit of work in the agreed plan
- **Round**: one request from Pascal, from alignment to closing. A MAIN can run several rounds
- **Fast track**: Pascal says `fast track` to skip the REV threads. Pascal reviews the work with MAIN in real time, and says when to launch a reviewer

## Pick the branch

- **Pascal invokes `s3`:** you are MAIN. Run [CU1](references/cu1.md) on the agreed plan
- **A launch message starts with `$s3 ; <sop>`:** you are the thread it names. Read `references/sop/<sop>.md` and follow it

## Roles

| Role | Thread name | Does |
|---|---|---|
| MAIN | `👑 MAIN <id4> <subject>` | The only thread Pascal talks to. Launches each thread, triages every finding, merges on Pascal's go. Never edits code |
| COD | `🐝 COD<n> <id4>` | Implements its card in its worktrees, opens its PRs, applies the findings MAIN relays, runs its retros |
| REV | `👀 ADV<n> <id4>`, `👀 BLAST<n> <id4>`, `👀 RDOC<n> <id4>`, `👀 PRIS<n> <id4>` | Reviews the stack of COD<n> and reports. Edits no file. Lists each finding with its severity, its file and line, and the fix it proposes |
| DOC | `📚 DOC<n> <id4>` | Updates the docs the stack makes stale, in a docs PR at the top of the stack of COD<n>, and applies the findings MAIN relays on it |

`<id4>` is the last 4 characters of MAIN's threadId. Searching it in T3, or passing it to `t3_thread_list` as `titleContains`, shows the whole family. `<n>` is the number of the COD the thread works for. CODs count from 1, in launch order.

Only MAIN talks to Pascal. Every other thread reports to MAIN with `t3_thread_send`.

## SOPs

| SOP | Role | Read when |
|---|---|---|
| [main-launch](references/sop/main-launch.md) | MAIN | Before each thread you launch |
| [main-triage](references/sop/main-triage.md) | MAIN | A REV reports |
| [main-closing](references/sop/main-closing.md) | MAIN | The reviews end: report, merge, retros, settle |
| [cod-implement](references/sop/cod-implement.md) | COD | Launched, or MAIN relays findings or asks for your retros |
| [rev-adverse](references/sop/rev-adverse.md) | REV | Launched as ADV |
| [rev-blast-radius](references/sop/rev-blast-radius.md) | REV | Launched as BLAST |
| [rev-docs](references/sop/rev-docs.md) | REV | Launched as RDOC |
| [rev-pristine](references/sop/rev-pristine.md) | REV | Launched as PRIS |
| [doc-update](references/sop/doc-update.md) | DOC | Launched, or MAIN relays findings |

## Use cases

| CU | Status |
|---|---|
| [CU1](references/cu1.md) | Approved. Run it for every `s3` request |
| [CU2](references/cu2.md) | Not approved. Never run it |
| [CU3](references/cu3.md) | Not approved. Never run it |

A PR that changes an SOP step updates each CU that shows the step.

## Shared rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- Settle a thread with `t3_thread_organize` action `settle`, once `t3_thread_wait` confirms its turn ended. T3 refuses a thread with active work, with "has active or blocked work"
- Link a PR with `link_pull_request` only. `t3_thread_update` replaces the PR already linked, so a thread with PRs A and B would lose A
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- As you see fit, leave comments on the PRs to help Pascal understand what's happening
- One writer per worktree: MAIN relays to one thread at a time per worktree, and to the next only after the previous one reports a clean, pushed checkout. The COD that owns the stack does every restack
- MAIN posts a status update at each step: "📍 [what is going on] / [step]"
- Keep going without Pascal. You may push your stack branches, and open and update PRs and issues. A thread of this MAIN may force-push with `--force-with-lease` any branch a thread of this MAIN created
- Stop only when one of these happens. A thread reports it to MAIN, and MAIN asks Pascal:
	- a contradiction or an unavailable live step blocks you
	- you need a decision from Pascal
	- the next action deletes data, changes anything outside the agreed repositories and their PRs and issues, or force-pushes a branch no thread of this MAIN created. The merge's deploy and the retro issues in any of Pascal's repositories are allowed
		- After a squash merge or merge commit, deleting a branch whose tip still matches the PR's head commit at merge time is not deleting data
