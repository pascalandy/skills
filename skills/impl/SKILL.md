---
name: "impl"
description: "Use to implement a plan or an issue."
kind: "dev"
---

# Impl

Time to implement this! My "implement" or my `impl` is my instruction to merge when step 6 allows it. When neither came from me, stop after step 5 and ask before merging.

#### Agency

Do everything you think is advisable based on all of that, and start trying to close the biggest gaps yourself, especially the ones with the most "bang for the buck" in terms of the work needed to get a huge benefit in moving us closer to achieving the stated goals of the project (things like wiring in finished code that just isn't properly connected yet would be examples of that, but you can interpret the remit more broadly yourself using your own expert judgment).

I want you to show real agency and follow your gut instincts as to what will most improve the project. Also, start systematically, methodically, meticulously, and diligently executing any remaining issues/tasks in the optimal logical order!

Remember: use your expert judgment on all decisions to make the optimal choice. I believe in you! Keep cranking away on all that, friend! You're doing a great job.

#### Step by step

Run these steps in order. Finish each one before you start the next:

**1. Execute**
- Use skill 🧰 poteto-mode to implement the FMO we agreed on, or the issue, and open the PRs
- Order the work by value for effort. Wiring in finished code that isn't connected yet is the typical quick win
	- When you find a gap outside the scope, leave it unfixed and file it as a new issue. Label it with 🧰 label-for-issues
- Done when every item is implemented with green checks, or reported as blocked with the reason

**2. Self-check**
- Run a $2nd-pass

**3. Impacts**
- Start a 🧰 headless `--review-only` run and ask it: "Delegated by impl. Use $poteto-mode and $blast-radius on 'stack PR URLs'. Then run a premortem: assume this stack merged and broke something a week later. Which blind spots explain it?"
- While it runs, write your own premortem. What could go wrong? Are we adding debt or code smells?
- Fix every high-severity finding from both premortems, then run 🧰 2nd-pass again

**4. External review**
- Start a 🧰 headless `--review-fix` run in the stack's checkout and ask it: "Delegated by impl. Use $poteto-mode to review the stack at 'URL'. The solution works. Make it great and pristine while keeping the solution simple. Fix what you find by editing the files directly, leave the changes uncommitted, and list each change with its reason."
	- the agent leaves commits and pushes to you. Review its diff, run the checks, commit each change to the layer it belongs to with $gh-stack, and push
- If the stack changed documented behavior, run 🧰 andy-mode ; docs, then commit its edits to the layer they belong to and push

**5. Report**
- PR links, links to the issues you filed
- Every change outside the FMO or the issue, and why
- What you couldn't confirm, and where you looked
- Confidence to merge: XX %

**6. Merge gate**
- If confidence is at least 90 %, checks are green on every PR (or the repo has no CI and you say so), and no high-severity finding is open, land the stack with poteto's Shipping playbook, through the project's merge command and any deploy it runs.
	- if applicable, explicitly share why we don't get a 100%
- Otherwise, ask me how to unblock it (format below).

**7. Close**
- Feedback on my skills: run 🧰 andy-mode ; retro-skill-usage. Publish its issues as needed (max: 3)
- Environment feedback: run 🧰 andy-mode ; retro-global
- Say goodbye

#### Rules

- One PR per verifiable unit, stacked with 🧰 gh-stack when they depend on each other. Assign each PR to pascalandy
- 🧰 headless use **Codex with GPT-6.1 Sol at xhigh**. Show the command in a code block before you run it.
	- If you are running on the cloud env, it's OK that you don't have access to codex. Just mention this fact that you could not use it.
- If a skill is missing (sync issues happens), see : https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md
- Keep going without me. You may push your own stack branches (`--force-with-lease` is fine), open and update PRs and issues, and merge when step 6 allows it.
- Stop and ask only when :
	- a contradiction or an unavailable live step blocks you (report it)
	- you need a decision from me
	- the next action deletes data, changes anything outside this repository and its PRs and issues (step 6's merge and the deploy it runs are allowed), or force-pushes a branch you didn't create

#### When You Need Me

Ask in the question format from $oem. If nothing is left to decide, write:

0) ⛳ Implemented. [high-level summary of what landed]

After my answers, apply them and resume at the earliest step they change.
