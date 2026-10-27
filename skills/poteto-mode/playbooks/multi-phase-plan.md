---
description: "Write the plan for work that spans several phases or stacked PRs, as a checklist an owner runs box by box."
---

### Multi-phase or multi-PR plan

Read [agent runtime](../references/agent-runtime.md) before delegating, resuming, reading history, or authoring a skill.

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** The plan is the deliverable. Do not implement.

1. When the change is one or two files with an obvious approach, skip the plan. Say so and stop. For a config, text, or tool-removal rollout where no PR changes an interaction or a measured path, skip the skeleton and `scripts/check-plan.mjs`. Write a checklist with one named-file proof per machine or repository and explain why the exception applies. If any PR changes an interaction or a measured path, every PR keeps the full skeleton.
2. Settle open questions by prototype before you write. Run `playbooks/prototype.md` for each. Keep the branch, the SHA, and the screenshots for Appendix A. Ask the operator only about a product or preference call that no run can settle. Give options (the **Never Block on the Human** principle).
3. Explore in available subagents with bounded briefs and supported model choices per the agent-runtime reference (the **Guard the Context Window** principle). Each returns file pointers, conventions, test commands, and entry points. No inlined dumps.
4. Create one tracking GitHub issue as the canonical plan when you deliver it, before the operator's go and the first PR. Use the checklist from step 1 when its exception applies, including boxes for each PR's tracking line, updates after each merge or stack append that record `appended/ready` for an append and `merged` only after an actual merge, and naming who updates the issue after later actual merges. Otherwise fill the skeleton below in that issue, keeping every heading and sub-block in order, with one section per PR. Include a short implementation prompt and a step table with each step's deliverable, location, and state. Each PR body names `Part of #N · Step X of Y`. Update the issue first when the plan changes, then regenerate any local copy. Update step state after each merge or stack append. Record an append as `appended/ready` and record `merged` only after an actual merge. For skeleton plans, keep a local plan file only as a copy for `scripts/check-plan.mjs`. Unless the operator names a path, keep that copy under the resolved durable state directory's `docs/`. One PR is one change with its own evidence (the **Sequence Work into Verifiable Units** principle). Name the execution playbook in **How to read this**, or in the checklist for the exception. For a stack one agent builds in this session, choose Feature or Refactoring with `gh-stack`. For an autonomous run, pick between `playbooks/autopilot-full.md` and `playbooks/autopilot-stack.md` per the rule at the end of `playbooks/autopilot-stack.md`. A standing program takes `playbooks/orchestrate.md`.
5. Write under `/technical-writing` in full, then `/unslop`. The body is one Diátaxis mode, how-to. Appendices hold explanation and reference. Each heading states the task or the finding. No long dashes. No mid-sentence colons.
6. For skeleton plans, run `node <skill-dir>/scripts/check-plan.mjs -v <plan.md>`, where `<skill-dir>` is poteto-mode's folder. Fix each plan line its `errors` name and rerun until it answers `{"ok":true}` (the **Encode Lessons in Structure** principle). `-v` adds each PR section's box counts on stderr.
7. Hand back. Post the tracking issue URL, a short implementation prompt, and either the script's output or the reason for the checklist exception. For an unmerged stack, name who updates the issue after later actual merges. Then stop. Execution starts on the operator's explicit go, under the execution playbook the issue names.

The following verification and control surface requirements apply to plans that use the full skeleton.

**Verification.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked (the **prove-it-works** principle skill). That sentence is the verification rule. Every verification block opens with it. The live block is mandatory. Ten verification lanes at the PR head drive the real surface through an available driver, per the **swarm** skill. Each lane is one box with a concrete scenario, the screenshot it saves, and its pass predicate. One lane is the **Regression lane against trunk.** It runs the same load-bearing scenario on trunk and head. If trunk does not have the feature, the lane records that fact and gates the behavior the diff adds plus the end state the user waits for instead of inventing a trunk result. The perf gate is dual-sided. Trunk and head must both produce the named metric. If trunk lacks the feature, also isolate the work the diff adds and set an absolute budget for that work plus the end-to-end state the user waits for. Do not claim a ratio between unlike scenarios. The perf block names the metric, the interleaved probe, the trunk baseline measured first, and the rule with the number that fails. A PR that changes an interaction is review-gated. The operator reviews it in chat with screenshots and a video before merge. A PR that changes no interaction writes `**Review gate.** None. <PR id> is not review-gated.` and no boxes under it.

**Control surface.** Load the project's verification skill when available. Browser and Electron UIs use an available browser/CDP driver, CLIs use shell commands, TUIs use a PTY, and native apps use an available native or simulator driver. Preserve screenshots, traces, or output that proves the stated behavior. A PR that touches two surfaces gets lanes on both. A surface with no available driver is a risk in Appendix C, and its live block still names how each lane drives it.

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the PR ids in order.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs poteto-mode's `playbooks/<execution playbook>.md`. <Who merges, and which PR ids are the operator's items that stop at merge-ready.>

The canonical plan is the tracking issue `<URL>`. <Short implementation prompt.>

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Steps

| Step | Deliverable | Location | State |
| --- | --- | --- | --- |
| <X of Y> | <What this step gives> | <Repository or machine and PR id> | <Current state> |

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on her explicit go.
- [ ] On her go, write `goal.md` with this exact text. "<The tracking issue URL, the PR ids in order, the verification rule, who merges, and the done condition.>"
- [ ] Read these at program start. Re-read them at every tick.
  - [ ] poteto-mode's `playbooks/<execution playbook>.md`
  - [ ] the swarm skill's `SKILL.md`
  - [ ] `git show origin/main:<control skill path>`
  - [ ] poteto-mode's `playbooks/opening-a-pr.md`
  - [ ] each other skill the program uses, from its installed copy
- [ ] Arm the 30-minute audit tick. Use a supported scheduler or monitored watcher with bounded waits, and record the next audit time. If the harness cannot wake an idle session, checkpoint the next check and state that unattended continuation is unavailable.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk and goal.md. Audit the operation against both and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stop a stuck lane, confirm it has stopped writing, then dispatch its replacement. Then send the operator a status message, whether or not anything changed, with the queue table of PR, owner, state, and head SHA, the verdicts since the last tick, what merged, open operator gates, and blockers."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Under Feature or Refactoring, the session agent owns every PR and is the sole `gh-stack` writer. For a named program, follow its playbook's owner lifecycle.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
  - [ ] <PR id> and <PR id> are independent and first. Both branch from `main`.
  - [ ] <PR id> after <PR id>.
- [ ] Hold the file boundaries. <PR id or class> touches only `<glob>`.
- [ ] Hold the review gate. <PR ids> change an interaction. They wait for the operator's review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`; if `command -v origin` succeeds and Origin can resolve the repository, use `origin pr` for every PR operation. Record any fallback to `gh`. Never require `gt`.
- [ ] Open the PR ready, never draft, with `origin pr create --status open --base <base-branch>` or `gh pr create --base <base-branch>` according to the resolved forge. A stack child targets its parent branch.
- [ ] Include `Part of #<N> · Step <X> of <Y>` in the PR body, naming the tracking issue and step.
- [ ] Run the repo's lint and typecheck once before the PR-facing push. Push with hooks on.
- [ ] Remove redundant abstractions, dead code, and debug leftovers before each commit; load `no-comments` before review when the diff changes source code.
- [ ] Triage comments from review agents present on the PR per `../references/review-bot-triage.md`.
- [ ] Rebase onto current trunk before babysit and again before the merge-ready report.

### Verdict and merge, for every PR

- [ ] At the merge-ready head SHA, run the swarm per the **swarm** skill. One gates lane. The ten live lanes from the PR's **Verify, live** block. The perf lane from its **Verify, perf** block. One audit lane that reads the diff and the receipts and distrusts the PR body.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner. A new head gets a fresh swarm and a fresh verdict.
- [ ] <For Feature or Refactoring, name who lands the stack under the repository's merge procedure. For a named program, use its playbook's merge or append rule, with the patch-id rule from `playbooks/shipping.md`.>
- [ ] After each merge or stack append, update the step's actual state in the tracking issue, then regenerate the local copy. Record `appended/ready` for an append and `merged` only after an actual merge.

### Boot recipe, for every live lane

Each live lane runs at the PR head in an isolated workspace or verified remote environment. Use the available driver and project verification recipe. Run lanes serially when concurrent isolated sessions are unavailable; preserve independent reviewer identity where required.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] <Start the backend and the surface. Wait for ready.>
- [ ] <Deliver input only through the control skill's commands. Name the read-only diagnostics.>
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return the paths with the report.

## <Task as a verb phrase> (<PR id>)

**Depends on.** <PR id, or None.>

**Files.**

- [ ] Edit `<path>`.
- [ ] Create `<path>`.
- [ ] Delete `<path>`.

**Build.**

- [ ] <One change. Name the symbol and the file.>

**You see.**

- [ ] <One observable result, with the exact log line or screen state.>

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] <Test file and the case it gains.> Run `<command>`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten verification lanes at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run <the same load-bearing scenario> at trunk and head. If trunk lacks the feature, record that and gate <the behavior the diff adds plus the end state the user waits for>. Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 2. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 3. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 4. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 5. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 6. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 7. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 8. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 9. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 10. <Scenario.> Save `<slug>.png`. Pass when <predicate>.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. <What is measured at both trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.>
- [ ] Probe. <The command or procedure, run at trunk and at the head, interleaved. Both sides must produce the metric.>
- [ ] Baseline. Record the trunk <value> first.
- [ ] Rule. <Head against trunk, with the number that fails. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.>

**Review gate.** The operator reviews before merge.

- [ ] Copy lane <n> screenshots into `<media path>/<pr-id>-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of the change on a lane VM. Save it as `<media path>/<pr-id>-review.mp4`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Applicable review-agent findings triaged, or no review agent configured.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] <The landing rule recorded under Verdict and merge for this PR.>

## Close the program

- [ ] For an unmerged stack, name who updates the canonical issue after later actual merges in the handback.
- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

<Each open question a prototype answered, with the branch, the SHA, and the artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected

<Each approach weighed and why it lost.>

## Appendix C. Risks

<Each risk with the PR it lands in and what the owner watches.>

## Appendix D. Links and reading list

<Docs to read before editing. Which PRs get the **how** and **interrogate** skills. The trail per the **show-me-your-work** skill.>
````

**Reply:** the tracking issue URL and a short implementation prompt, the PR ids with their dependencies and the review-gated set, what the prototypes proved and what stays unproven, either the check script's output or the reason for the checklist exception, and the owner of issue updates after later actual merges for an unmerged stack.
