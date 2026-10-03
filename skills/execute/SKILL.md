---
name: "execute"
description: "Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan."
kind: "dev"
---

Execute all of this!

#### Agency

Do everything you think is advisable based on all of that, and start trying to close the biggest gaps yourself, especially the ones with the most "bang for the buck" in terms of the work needed to get a huge benefit in moving us closer to achieving the stated goals of the project (things like wiring in finished code that just isn't properly connected yet would be examples of that, but you can interpret the remit more broadly yourself using your own expert judgment).

I want you to show real agency and follow your gut instincts as to what will most improve the project. Also, start systematically, methodically, meticulously, and diligently executing any remaining issues/tasks in the optimal logical order!

Remember: use your expert judgment on all decisions to make the optimal choice. I believe in you! Keep cranking away on all that, friend! You're doing a great job.

Help me understand what is happening :
- all steps, review delays, litch fixes can be confusing as you are hiding many details. Give me status updates regularly: "📍 [concise status about what is going on] / Step N/X"

#### Step by step

Run these steps in order, and finish each one before you start the next
- when the agreed work opens or updates no PR, such as issue edits only, skip the Independent review, Codex on each PR, and Merge gate steps, and say so in the report

**STEP: Execute**

- Use 🧰 poteto-mode to implement everything we agreed on, and open the PRs
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- Note each gap you find outside the scope for the report. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Done when either:
	- every item is implemented and checks are green
	- or each remaining item is reported as blocked, with the reason

**STEP: Self-check**
- Run a $2nd-pass
- Done when each 2nd-pass finding is fixed or reported

**STEP: Blast-radius**

- Run 🧰 headless `--review-only` and ask it:
	- "Use $poteto-mode and $blast-radius on 'stack PR URLs'. Then run a premortem: assume this stack merged and broke something a week later. Which blind spots explain it?"
- While it runs, write your own premortem. What could go wrong? Are we adding debt or code smells?
- Done when:
	- every medium or high severity finding from the review and both premortems is fixed or dismissed with a written reason, and each fix is committed to the layer it belongs to with 🧰 gh-stack and pushed

**STEP: Codex on each PR**
- On each PR, comment "@codex review" and babysit, wait for its review
- Fix or dismiss each finding. After you push a fix, comment "@codex review" once more on that PR
- Done when each PR has a Codex review of its latest head or has had two, or Codex is unavailable and you say so in the report

**STEP: Code review | across the whole stack**
- Run 🧰 headless ; review-fix in a sandbox (`.git` read-only, no network) within the stack's checkout, and ask it:
	- "Use $poteto-mode to review this stack: every change from 'base branch' to HEAD. The solution works; now make it great and pristine while keeping it simple. Fix what you find by editing the files directly, leave the changes uncommitted, and list each change with its reason."
- The agent can't commit, so the commit is yours. Review its diff, run the checks, commit each change to the layer it belongs to with $gh-stack, and push

**STEP: Report**
- PR links and links to the issues you filed
- Every change you made outside what we agreed, and why
- The gaps outside the scope you did not file
- What you couldn't confirm, and where you looked
- Confidence to merge: XX%, and why it is below 100% when it is
- Done when the report includes every item above

**STEP: Merge gate**
- Land the stack with poteto's Shipping playbook, through the project's merge command and any deploy it runs, when all of these hold:
	- confidence to merge is at least 94%
	- every agreed item is implemented, none blocked
	- checks are green on every PR's final commit (or the repo has no CI and you say so)
	- no mediumor high-severity finding is open
- Otherwise, ask me about the next steps (see below)
- Done when each PR is merged and its deploy succeeded. The merge command can exit 0 after a failed deploy, so read its output and report a failed deploy

**STEP: Close**

- Run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. From each, file at most 2 issues: the fixes with the most bang for the buck
- If the final code changed documented behavior
	- run 🧰 andy-mode ; docs
- Say goodbye
- Done when both retros are complete, the selected issues are filed, and you've said goodbye

#### Rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- Run 🧰 headless with Codex, and show the command in a code block before you run it
	- Where Codex is missing, as in a cloud environment, skip those runs and say so in the report
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- Whenever a change alters documented behavior, run 🧰 andy-mode ; docs and commit its edits to the layer they belong to
- As you see fit, leave comments on the PRs to help me understand what happened
- Keep going without me. You may push your own stack branches (`--force-with-lease` is fine), open and update PRs and issues, and merge when the merge gate allows it
- Stop and ask only when:
	- a contradiction or an unavailable live step blocks you (report it)
	- you need a decision from me
	- the next action deletes data, changes anything outside this repository and its PRs and issues, or force-pushes a branch you didn't create. The merge gate's merge and the deploy it runs are allowed, and so are the Close step's retro issues in any of my repositories
		- After a squash merge or merge commit, deleting a branch whose tip still matches the PR's head commit at merge time is not deleting data

#### Questions

Ask question(s) in the format of 🧰 oem's "When You Need Me".
- After my answers, apply them and go back to step 1

If nothing is left to decide, say:
- ⛳ Implemented. [high-level summary of what landed]
