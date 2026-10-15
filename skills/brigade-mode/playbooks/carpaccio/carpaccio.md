---
description: "Run batches under a Head Chef: Cooks implement, document, watch and delegate reviews; each Chef validates, merges and closes its batch."
---

# CU1. Batches under one Head Chef

## Vocabulary

- **SOP**: a role's procedure in `sop/`
- **Batch**: one Chef's work in one repository, grouped by the plan, such as an epic or milestone
- **Card**: a unit of work within a batch
- **Chain**: a barrage reports to its Cook, a Cook to its Chef, a Chef to the Head Chef, and the Head Chef to Pascal
- **Fast track**: `$brigade ; carpaccio ; manic-4`, or Pascal's request during a run. The Cook implements only, skipping docs and barrages

## Roles

| Role | Runs as | Title | Responsibility |
|---|---|---|---|
| Head Chef | Pascal's pinned thread | `Head Chef <id4> · <done>/<batches> · <subject>` | Bridges needs and requirements, splits batches, launches and guides Chefs, resumes coordination on escalation. Never edits code or opens PRs |
| Chef | Thread in the batch's repository project | `🧑‍🍳 Chef <b> <id4> · <step>/6 · <batch>` | Creates worktrees, launches Cooks, prevents conflicts, validates, merges, releases and closes. Never edits code |
| Cook | Thread bound to its own worktree | `🐝 Cook <b>.<c> <id4> · <batch>` | Owns implementation, PRs, watches, docs, barrage delegation and triage, then reports readiness. Leaves merging to the Chef |
| Barrage | Cook's delegate | `👀 <sop> · Cook <b>.<c> <id4>` | Reviews under the contract in its brief |

`<id4>` is the last four characters of the Head Chef's threadId. `<b>` numbers batches in launch order; `<c>` numbers a batch's Cooks. `<done>` counts merged batches and batches done without a PR. `<step>` names the current process step.

## SOPs

Read only the SOP for your current role and step.

| SOP | Read when |
|---|---|
| [head-chef](sop/head-chef.md) | Coordinating the run |
| [chef-run](sop/chef-run.md) | Launching Cooks, following progress or relaying Stop |
| [chef-closing](sop/chef-closing.md) | Validating a stack, merging or closing the batch |
| [cook-implement](sop/cook-implement.md) | Implementing, fixing, documenting, reporting, stopping or running retros |
| [cook-review](sop/cook-review.md) | Delegating reviews or triaging results and watch wakes |
| [manic-1](sop/manic-1.md) | Delegated adversarial review |
| [manic-2](sop/manic-2.md) | Delegated blast-radius review |
| [manic-3](sop/manic-3.md) | Delegated docs review |
| [manic-5](sop/manic-5.md) | Delegated pristine review |

## Settings

Read [config.toml](config.toml) for settings and their readers; edit the source copy when changing them.

## Process

Copy the table and check off your role's steps:

| # | Step | Owner and SOP |
|---|---|---|
| 0 | Align | Head Chef and Pascal, `head-chef` |
| 1 | Implement | Cook, `cook-implement` |
| 2 | manic-1 and manic-2 side by side through interrogate | Cook leads, delegates and triages, `cook-review` |
| 3 | Docs | Cook, `cook-implement` Docs |
| 4 | manic-3 and manic-5 side by side through interrogate | Cook leads, delegates and triages, `cook-review`; manic-3 uses technical-writing |
| 5 | Validation and merge | Chef, `chef-closing`; Head Chef for held batches |
| 6 | Closing | Chef and Cook, `chef-closing` and `cook-implement` Retros |

For a batch that opens no PR, its Chef does the work alone, skips steps 1 to 5, and reports that choice. Fast track goes from Implement to the Cook's Ready section, then step 5.

## Shared rules

- One PR per verifiable unit, in one stack per Cook and repository with 🧰 gh-stack, even for independent cards. Assign each PR to `pr-assignee`
- The Cook is the sole writer in its worktree and owns every restack. The Chef uses it for merging only after the Cook reports a clean, pushed checkout
- Put each fix in the layer that last changed its line; for a line from the trunk, use the layer whose change made it wrong
- The Cook follows the repository's `AGENTS.md` procedure first; 🧰 poteto-mode fills what it leaves open. Treat issue proposals as drafts: verify each command, flag and message against the tool's source or a throwaway run before copying it. Report each false line and its fix to the Chef
- Append `Rules: <inherited Rules plus each relevant standing rule the target project does not load>` to every launch message and barrage brief. Preserve inherited Rules for delegates, which see only their brief; omit an empty field
- A comment posted through Pascal's account does not wake the Cook's watch; the Chef also sends it to the Cook with `t3_thread_send`
- A question climbs the chain with the sender's default. Each level answers from its context or escalates. A Chef unable to resolve a batch problem asks the Head Chef to decide, split the work again or relaunch the Chef
- Keep going without Pascal within the agreed repositories and their PRs and issues. The run may push and open or update PRs and issues, and force-push its own branches with `--force-with-lease`. Merge deploys and retro issues in Pascal's repositories are allowed
- Escalate before deleting data, changing anything outside that scope or force-pushing a branch the run did not create. Deleting a merged branch whose tip matches its recorded PR head preserves the merged work
- If a skill is missing, find it in https://raw.githubusercontent.com/pascalandy/skills/refs/heads/main/docs/references/remote-skills.md

### Retros

For each enabled role, run 🧰 andy-mode ; retro-skill-usage, then 🧰 andy-mode ; retro-global. Each retro files the issues with the most value, up to `retro-max-issues` per thread. Done when each has issue links or a recorded no-findings result.

## Work folders

Use `~/.cache/brigade-<id4>/<thread>/` for temporary files and caches, with `TMPDIR` set to its `tmp/` subfolder. `<thread>` is `head-chef`, `chef-<b>`, `cook-<b>.<c>` or `<sop>-<b>.<c>-<k>`. Create both folders before work and remove the work folder before your final report, removing a barrage's detached worktree first. Recreate them when resumed. Append these instructions as an expanded `Work folder: <absolute path and instructions>` field to every launch message and barrage brief. At run close the Head Chef removes `~/.cache/brigade-<id4>/` and runs `git worktree prune` in every run repository after all workers stop.

## Model selection

The Head Chef selects `[chef]`, the Chef selects `[cook]`, and the Cook selects each barrage's table from `config.toml`.

1. Read your selection with `t3_thread_configuration`. For a thread, choose `chef-on-claude` or `chef-on-codex` from the launching role's provider; for a barrage, choose `cook-on-claude` or `cook-on-codex` from the Cook's provider. `inherit` keeps your instance, model and reasoning level. Otherwise resolve `instance` to a live provider instance in `orchestrator_capabilities`. Done when the provider and model exist
2. Map `reasoning-level` to Codex `reasoningEffort` or claudeAgent `effort`. Map `service-tier` `standard`/`fast` to Codex `serviceTier` `default`/`priority` or claudeAgent `fastMode` `false`/`true`. Table values override top-level defaults. For Cook side work on Claude, use `[cook].delegate-on-claude` through `delegate_task`. Done when the catalog supports each option and every barrage uses the other provider
3. Threads inherit runtime and interaction modes at launch; delegates inherit them from the Cook. Keep `runtime-mode = "inherit"` throughout the run, with no mode change. For launches use `modelSelection`; for delegations use `target`, renaming `instanceId` to `providerInstanceId`. Escalate an unavailable setting through the chain. Done when the selection is supported

## Report

Use this report for the Cook's 🚦, the Chef's report and the Head Chef's closing report. Aggregate earlier reports rather than repeating their contents in each SOP:

- Outcome, PR links, each branch with its head SHA, and issue links
- Out-of-scope gaps not filed; changes outside the agreement and why
- Review passes, accepted and rejected findings with reasons, and why each review ended
- Steps skipped or replaced and why, including a no-docs decision
- What you could not confirm and where you looked
- Confidence to merge as a percentage, explaining anything below 100%
