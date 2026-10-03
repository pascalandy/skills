---
name: "execute"
description: "Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan."
kind: "dev"
---

#### Agency

Show real agency: use your expert judgment on every decision, follow your gut on what most improves the project, and work through every agreed task relentlessly.

Help me understand what is happening. All these steps, review delays, and glitch fixes can be confusing. Share a status update regularly, like: "📍 [concise status about what is going on] / Step N/7"

#### Step by step

Run these steps in order. Finish each one before you start the next:

**1. Execute**
- Use 🧰 poteto-mode to implement everything we agreed on, and open the PRs
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- If the change alters documented behavior, run 🧰 andy-mode ; docs and commit its edits to the layer they belong to
- Note each gap you find outside the scope for the report. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Done when either:
	- every item is implemented and checks are green
	- or each remaining item is reported as blocked, with the reason

**2. Self-check**
- Run 🧰 2nd-pass
- Done when each 2nd-pass finding is fixed or reported

**3. Independent review**
- Run 🧰 headless `--review-only` and ask it:
	- "Use $poteto-mode and $blast-radius on 'stack PR URLs'. Then run a premortem: assume this stack merged and broke something a week later. Which blind spots explain it?"
- While it runs, write your own premortem. What could go wrong? Are we adding debt or code smells?
- Done when every medium- or high-severity finding from both premortems is fixed, committed to the layer it belongs to with 🧰 gh-stack, and pushed

**4. Codex on each PR**
- On each PR, leave the comment "@codex review"
- Within 2 min, Codex posts a summary comment whose table says `Running`. When none appears, the repo lacks the Codex GitHub app: skip the rest of this step and say so in the report
- Babysit: poll that comment until no row says `Running` (about 4–8 min), then read the reviews, inline comments, and reactions newer than your request. A 👍 with no review means the PR is clean
- Fix each valid finding, commit, and push
- Done when Codex has reviewed every PR, or you skipped this step

**5. Report**
- PR links and links to the issues you filed
- The gaps outside the scope you did not file
- What you couldn't confirm, and where you looked
- Confidence to merge: XX%, and why it is below 100% when it is

**6. Merge gate**
- Land the stack with poteto's Shipping playbook, through the project's merge command and any deploy it runs, when all of these hold:
	- confidence to merge is at least 94%
	- every agreed item is implemented, none blocked
	- checks are green on every PR's final commit (or the repo has no CI and you say so)
	- no medium- or high-severity finding is open
- Otherwise, ask me about the next steps (see below)

**7. Close**
- Run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. From each, file at most 2 issues: the fixes with the most bang for the buck
- Say goodbye

#### Rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- Run 🧰 headless with Codex, and show the command in a code block before you run it
	- Where Codex is missing, as in a cloud environment, skip those runs and say so in the report
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- As you see fit, leave comments on the PRs to help me understand what happened
- Keep going without me. You may push your own stack branches (`--force-with-lease` is fine), open and update PRs and issues, and merge when the merge gate allows it
- Stop and ask only when:
	- a contradiction or an unavailable live step blocks you (report it)
	- you need a decision from me
	- the next action deletes data, changes anything outside this repository and its PRs and issues, or force-pushes a branch you didn't create. The merge gate's merge and the deploy it runs are allowed, and so are the Close step's retro issues in any of my repositories
		- After a squash merge or merge commit, deleting a branch whose tip still matches the PR's head commit at merge time is not deleting data

#### When You Need Me

Ask in the format of 🧰 oem's "When You Need Me". If nothing is left to decide, say:

0) ⛳ Implemented. [high-level summary of what landed]

After my answers, apply them and resume at the earliest step they change
