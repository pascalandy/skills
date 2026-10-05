---
name: "execute"
description: "Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan."
kind: "dev"
configuration-is-needed: true
---

Execute all of this!

#### Agency

Show real agency: use your expert judgment on every decision and follow your gut on what most improves the project

Post a status update at each step: "📍 [what is going on] / [step name]"

#### Step by step

- Run these steps in order, and finish each one before you start the next
- When the agreed work involves no PR, such as issue edits only, skip the Blast-radius, Code review on each PR, Code review, Docs, Checks, and Merge gate steps, and say so in the report

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

**STEP: Code review on each PR**
- On each PR, post a NEW top-level conversation comment containing exactly this single line:

	```txt
	Paula Review PR
	```

- First, check whether “Revue Paula” already covers the PR’s current head SHA. If it does, use that review; do not post another trigger or wait for a duplicate
- Otherwise, post a NEW top-level Conversation comment containing exactly Paula Review PR
- Then babysit, wait for the review covering that head SHA
	- Fix or explicitly dismiss each finding with a reason. After pushing fixes, post a NEW trigger comment
	- Request at most 4 reviews per PR. If the limit is reached or Paula is unavailable, report the blocker; do not treat it as a pass
	- Done when every PR’s latest head is reviewed and every finding is fixed or explicitly dismissed

**STEP: Code review across the whole stack**
- After all changes are pushed, post a NEW top-level Conversation comment on the TOP PR using these five lines. Replace every placeholder with current remote values:

	```txt
	Paula Review Stack
	PRs: <PR numbers from bottom to top, e.g. #502 #503 #504>
	Base: <base branch of the bottom PR, e.g. main>
	Base-SHA: <full 40-character current base SHA of the bottom PR>
	Head-SHA: <full 40-character current head SHA of the top PR>
	```

- Then babysit, wait for “Revue Paula — Stack” linked to that trigger comment and covering the current base and all PR heads
- Fix or explicitly dismiss each finding with a reason. Commit fixes to their owning layers, restack and push, then post a NEW stack comment with refreshed remote values
- Request at most 4 stack reviews. If the limit is reached or Paula is unavailable, report the blocker; do not treat it as a pass
- Done when the current stack is reviewed and every finding is fixed or explicitly dismissed

**STEP: Docs**
- Run 🧰 andy-mode ; docs on the stack's final diff, and commit its edits to the layer they belong to
- Until the merge, run this step again on each later fix that changes documented behavior
- Done when each doc that describes a behavior the stack changes matches the new behavior, and its edits are pushed

**STEP: Checks**
- On each PR's final commit, run the project's checks (local CI) and wait for its GitHub checks. Fix each failure in the PR that owns the code, push, and repeat
- If the repo has no CI, say so in the report
- Done when local checks and any GitHub checks are green on every PR's final commit, or each failing check is reported as blocked, with the reason

**STEP: Report**
- PR links and links to the issues you filed
- Every change you made outside what we agreed, and why
- The gaps outside the scope you did not file
- What you couldn't confirm, and where you looked
- Confidence to merge: XX%, and why it is below 100% when it is
- Done when the report includes every item above

**STEP: Merge gate**
- HITL: Ask the user whether to merge (see below), and end your reply on that question
- When I say merge, land the stack with poteto's Shipping playbook, through the project's merge command and any deploy it runs. The merge command can exit 0 after a failed deploy, so read its output and report a failed deploy
- Done when either:
	- I said merge, each PR is merged, and its deploy succeeded or you reported the failed deploy
	- or I said not to merge. A "not yet" keeps this step open

**STEP: Close**
- Run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global
	- From each, file at most 2 issues: the fixes with the most bang for the buck
- Done when both retros are complete, the selected issues are filed, and you've said goodbye

#### Rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- As you see fit, leave comments on the PRs to help me understand what happened
- Keep going without me. You may push your own stack branches (`--force-with-lease` is fine), and open and update PRs and issues
- Stop and ask only when:
	- a contradiction or an unavailable live step blocks you (report it)
	- you need a decision from me
	- the next action deletes data, changes anything outside this repository and its PRs and issues, or force-pushes a branch you didn't create. The Merge gate's deploy and the Close step's retro issues in any of my repositories are allowed
		- After a squash merge or merge commit, deleting a branch whose tip still matches the PR's head commit at merge time is not deleting data

#### Github comment rules:

- Before requesting a review, check for an existing Paula review covering the current PR head or the current stack’s base and all PR heads. Use it if present; do not wait for a duplicate
- To request a review, create a NEW top-level Conversation comment using the appropriate PR or stack format. A push or an edited comment does not trigger a review
- Post the comment as plain text, with no code fences, indentation, quotation marks or bullet markers. Preserve the colons and # signs required by the stack fields
- The first nonempty line must be exactly Paula Review PR or Paula Review Stack, with no extra text or punctuation on that line
- Publish through the authorized pascalandy account on open PRs in pascalandy/skills. Post stack requests on the top PR, with PRs:, Base:, Base-SHA: and Head-SHA: populated from current remote values
- Request at most 4 reviews per PR and 4 reviews for the whole stack. If either limit is reached before its completion criteria are met, or Paula is unavailable, report the blocker; do not treat it as a pass
- If Paula answers BLOCKED or STALE, resolve the stated problem before requesting another review
- Paula performs static review and reports findings; the implementation agent owns fixes and tests
- A Paula review does not authorize merging. Follow the project’s separate checks and merge-approval requirements

#### Questions

Ask question(s) in the format of 🧰 oem's "When You Need Me".
- After my answers, apply them and resume at the earliest step they change

If nothing is left to decide, say:
- ⛳ Implemented. [high-level summary of what you completed]
