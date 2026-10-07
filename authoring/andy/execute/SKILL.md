---
name: "execute"
description: "Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan."
kind: "dev"
configuration-is-needed: true
---

Execute all of this! Show real **agency**: use your expert judgment on every decision and follow your gut on what most improves the project.

Post a status update at each step: "📍 [what is going on] / [step name]"

#### Step by step

- Run these steps in order, and finish each one before you start the next
- When the agreed work involves no PR, such as issue edits only, skip the Code review on each PR, Blast-radius impacts, Code review across the whole stack, Docs, Checks, and Merge gate steps, and say so in the report

**STEP: Execute**
- Use 🧰 poteto-mode to implement everything we agreed on, and open the PRs
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- Note each out-of-scope gap you find for the report. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Done when every item is implemented and checks are green, or each remaining item is reported as blocked, with the reason

**STEP: Self-check**
- Run a $2nd-pass
- Done when each 2nd-pass finding is fixed or reported

**STEP: Code review on each PR**
- Run 🧰 headless `--review-only` and ask it:
	> Use $poteto-mode to review <PR URL> like you're looking for a reason to reject it. Don't hold back. You saved me in the past :) Basically, I want to make sure that I'm not about to do anything overkill. I want to keep things simple, efficient, and grounded in common sense.
- Fix or dismiss each finding with a reason. If you pushed fixes, rerun the review on the new head (max 3 rounds)
- Done when every PR's latest head is reviewed and every finding is fixed or explicitly dismissed, or you reported the blocker

**STEP: Blast-radius impacts**
- Start only once the stack is ready for review
- Run 🧰 headless `--review-only` and ask it:
	> Use $poteto-mode and $blast-radius on <stack PR URLs>. Then run a premortem: assume this stack merged and broke something a week later. Which blind spots explain it?
- While it runs, write your own premortem. What could go wrong? Are we adding debt or code smells?
- Fix or dismiss each finding with a reason. If you pushed fixes, rerun the review on the affected PR heads (max 2 rounds)
- Done when each medium or high finding from the review and both premortems is fixed and pushed to its layer, or dismissed with a written reason

**STEP: Code review across the whole stack**
- Run 🧰 headless `--review-fix` in a sandbox (`.git` read-only, no network) within the stack's checkout, and ask it:
	> Use $poteto-mode to review this stack: every change from <base branch> to HEAD. The solution works; now make it great and pristine while keeping it simple. Fix what you find by editing the files directly, leave the changes uncommitted, and list each change with its reason.
- Keep or revert each change with a reason. Commit the kept ones to their owning layers, restack, and push. If you pushed, rerun the review on the restacked HEAD (max 4 rounds)
- Done when the current stack is reviewed and each change is pushed to its layer or reverted with a reason, or you reported the blocker

**STEP: Docs**
- Run 🧰 andy-mode ; docs on the stack's final diff, and commit its edits to the layer they belong to
- Until the merge, run this step again on each later fix that changes documented behavior (max 4 rounds)
- Done when each doc that describes a behavior the stack changes matches the new behavior, and its edits are pushed

**STEP: Checks**
- On each PR's final commit, run the project's checks (local CI) and wait for its GitHub checks. Fix each failure in the PR that owns the code, push, and repeat
- Done when checks are green on every PR's final commit, each failing check is reported as blocked with the reason, or the repo has no CI (say so in the report)

**STEP: Report**
- PR links and links to the issues you filed
- Every change you made outside what we agreed, and why
- The out-of-scope gaps you did not file
- What you couldn't confirm, and where you looked
- Confidence to merge: XX%, and why it is below 100% when it is
- Done when the report includes every item above

**STEP: Merge gate**
- HITL: Ask me whether to merge (see Questions), and end your reply on that question
- When I say merge, land the stack with poteto's Shipping playbook, through the project's merge command and any deploy it runs. The merge command can exit 0 after a failed deploy, so read its output and report a failed deploy
- Done when either:
	- I said merge, each PR is merged, and its deploy succeeded or you reported the failure
	- or I said not to merge. A "not yet" keeps this step open

**STEP: Close**
- Run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global
	- From each, file at most 2 issues: the fixes with the most bang for the buck
- End with "⛳ Implemented. [high-level summary of what you completed]" and say goodbye
- Done when both retros are complete, the selected issues are filed, and you've said goodbye

#### Rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- Use Codex for 🧰 headless runs, and show the command in a code block before you run it
	- Where Codex isn't installed, as in a cloud environment, skip those runs and say so in the report
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- As you see fit, leave comments on the PRs to help me understand what's happening
- Keep going without me. You may push your own stack branches (`--force-with-lease` is fine), and open and update PRs and issues
- Stop and ask only when:
	- a contradiction or an unavailable live step blocks you (report it)
	- you need a decision from me
	- the next action deletes data, changes anything outside this repository and its PRs and issues, or force-pushes a branch you didn't create. The Merge gate's deploy and the Close step's retro issues in any of my repositories are allowed
		- After a squash merge or merge commit, deleting a branch whose tip still matches the PR's head commit at merge time is not deleting data

#### Questions

Ask question(s) in the format of 🧰 oem's "When You Need Me".
- After my answers, apply them and resume at the earliest step they change

If nothing is left to decide, say:
- ⛳ Implemented. [high-level summary of what you completed]
