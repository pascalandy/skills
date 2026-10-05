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
- When the agreed work involves no PR, such as issue edits only, skip the Code review on each PR, Code review across the whole stack, Docs, Checks, Review coverage, and Merge gate steps, and say so in the report

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
- The trigger comment is this single line:

	```txt
	Paula Review PR
	```

- On each PR, request a review through the GitHub comment rules, then babysit, wait for "Revue Paula" covering the PR's current head SHA
- Fix or explicitly dismiss each finding with a reason. After pushing fixes, request a review of the new head
- Done when every PR's latest head is reviewed and every finding is fixed or explicitly dismissed, or you reported the blocker

**STEP: Code review across the whole stack**
- The trigger comment is these five lines. Replace every placeholder with current remote values:

	```txt
	Paula Review Stack
	PRs: <PR numbers from bottom to top, e.g. #502 #503 #504>
	Base: <base branch of the bottom PR, e.g. main>
	Base-SHA: <full 40-character current base SHA of the bottom PR>
	Head-SHA: <full 40-character current head SHA of the top PR>
	```

- After all changes are pushed, request a review on the top PR through the GitHub comment rules, then babysit, wait for "Revue Paula — Stack" covering the current base and all PR heads
- Fix or explicitly dismiss each finding with a reason. Commit fixes to their owning layers, restack and push, then request another stack review with refreshed remote values
- Done when the current stack is reviewed and every finding is fixed or explicitly dismissed, or you reported the blocker

**STEP: Docs**
- Run 🧰 andy-mode ; docs on the stack's final diff, and commit its edits to the layer they belong to
- Until the merge, run this step again on each later fix that changes documented behavior
- Done when each doc that describes a behavior the stack changes matches the new behavior, and its edits are pushed

**STEP: Checks**
- On each PR's final commit, run the project's checks (local CI) and wait for its GitHub checks. Fix each failure in the PR that owns the code, push, and repeat
- If the repo has no CI, say so in the report
- Done when local checks and any GitHub checks are green on every PR's final commit, or each failing check is reported as blocked, with the reason

**STEP: Review coverage**
- Check that completed reviews cover each PR's final head and the stack's final base and PR heads
- If Docs or Checks changed them, return to the affected review steps within the request limits, then continue in order from there
- Done when completed reviews cover the final PR heads and stack base, or you reported each gap as a blocker

**STEP: Report**
- PR links and links to the issues you filed
- Every change you made outside what we agreed, and why
- The gaps outside the scope you did not file
- What you couldn't confirm, and where you looked
- Confidence to merge: XX%, and why it is below 100% when it is
- Done when the report includes every item above

**STEP: Merge gate**
- HITL: Ask me whether to merge (see below), and end your reply on that question
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

#### GitHub comment rules

- Paula reviews open PRs in pascalandy/skills only; publish there through the authorized pascalandy account. In any other repository, report that Paula is not configured and that its PRs have no Paula review. Name any other reviewer you use instead
- Before requesting a review, check for an existing Paula review covering the current PR head or the current stack's base and all PR heads. Use it if present; do not post another trigger or wait for a duplicate
- To request a review, create a new top-level conversation comment in the step's format. A push or an edited comment does not trigger a review
- Post the comment as plain text, with no code fences, indentation, quotation marks or bullet markers. Preserve the colons and # signs required by the stack fields
- The first nonempty line must be exactly Paula Review PR or Paula Review Stack, with no extra text or punctuation on that line
- Request at most 4 reviews per PR and 4 reviews for the whole stack. If either limit is reached before its completion criteria are met, or Paula is unavailable, report the blocker; do not treat it as a pass
- BLOCKED or STALE does not count as a completed review
- For a PR, if Paula already answered BLOCKED for the current head SHA, report the blocker to me. Do not request another review of that same SHA or create an empty commit to bypass deduplication
- If a PR unexpectedly receives STALE, re-read its current head. If it changed, follow the check-first flow above for that head; otherwise report the blocker
- For a stack answered BLOCKED or STALE, resolve the stated problem, refresh the remote values, and request another review
- Paula performs static review and reports findings; you own fixes and tests
- A Paula review does not authorize merging. Follow the project's separate checks and merge-approval requirements

#### Questions

Ask question(s) in the format of 🧰 oem's "When You Need Me".
- After my answers, apply them and resume at the earliest step they change

If nothing is left to decide, say:
- ⛳ Implemented. [high-level summary of what you completed]
