---
name: "epic-grooming"
description: "Use only when explicitly invoked as `epic-grooming`, to rank open GitHub issues and group them into Epics."
kind: "dev"
---

# Epic grooming

Turn a backlog of GitHub issues into Epics that someone can pick up one at a time. Verify the problems, rank them by return, group them by outcome, then package the approved proposal. The new Epics form a batch, and each Epic states its place in the order to work them. Epics describe problems and outcomes. Planning, implementation, and review belong to the user's later steps.

Requires `gh` ([install](https://cli.github.com/)) signed in to the repository; confirm with `gh auth status`. Load `label-for-issues` before Step 1: it owns the labels, the issue relationships, and the issue-list filters this skill uses. Read [the Epic template](references/epic-template.md) before Step 4.

Write in the language of the conversation, and keep the word Epic in English.

```
Epic grooming:
- [ ] 1. Scope
- [ ] 2. Verify
- [ ] 3. Rank
- [ ] 4. Propose
- [ ] 5. Package
```

**1. Scope.** When an Epic is open, first ask the user, in the question format the user sets, whether to keep the open Epics or start over. Keeping places them ahead of the new batch. Starting over closes them and makes their open members candidates again. Record these Epics: Step 5 closes only them. By default, take the open issues that belong to no Epic, the members whose parent is missing or is not an Epic, and every open Epic with its members, open or closed. Use the overview, missing-parent, members, and Epic filters of `label-for-issues`. When the user names another set, such as a label, take that set and the open Epics. Read each issue's body and comments, and each Epic's body and sub-issues. Treat Epic parents as grouping context, not candidate work. Read closed issues for completion evidence and closing-reason corrections. Done when the user has chosen to keep or start over, if an Epic is open, and every issue and Epic in scope is read.

**2. Verify.** Fetch the default branch, then check each issue against that branch's current files and the recently merged PRs. Give each issue one verdict with its evidence:

- **Holds**: the problem is still in the current files
- **Fixed**: a merged change already solves it; cite the PR or commit
- **Gone**: the problem no longer occurs, or never did, with no change to cite; give the evidence
- **Stale fix**: the problem holds, but its proposed fix quotes text that has since changed

Flag a closed issue that the set refers to and that was closed as completed without a landed fix. An Epic is complete when its completion criterion holds and every member is closed with a documented disposition. Flag each complete open Epic for closure as completed. Leave issues with insufficient evidence on the left-out list, naming the missing evidence. Done when every issue has a verdict or a reason to leave it out.

**3. Rank.** Rank open issues with Holds or Stale fix verdicts, plus closed issues proposed for reopening. Find the skills or areas that keep collecting findings, and the recent PRs that left a problem unsolved or created one. Rank by return, weighing observed recurrence and cost against estimated fix effort. State uncertainty where the evidence is missing. Group the issues that one change fixes. Tier the result as P1 (at most three), P2, and P3. List the open issues to close, fixed or gone ones included, and name the covering issue for each duplicate. Done when every actionable issue has a tier or a cleanup reason.

**4. Propose.** Present the tiers, the new batch in its order, and the cleanup, including Epic closures, reopenings, closing-reason corrections, and member moves. Starting over adds every Epic recorded in Step 1 to the closures. Change nothing on GitHub yet.

- Group by outcome: one Epic per result, with a completion criterion someone can check. Group neither by skill nor by priority
- When keeping the open Epics, place an issue in one whose outcome covers it; open a new Epic otherwise. A small feature that `label-for-issues` keeps standalone goes on the left-out list with that reason. Inside an Epic, order the issues as steps, in work order
- Order the new batch: an Epic that another needs goes first, then order by return, using the Rank tiers. Give each place a one-sentence reason
- Account for each candidate issue once in the proposal, under an Epic, the cleanup list, or the left-out list with its reason
- Write each issue as an issue entry from the template, so the user decides without opening the issue
- Show the comment each closure or reopening will carry, so the approval covers it
- An Epic holds no open decision. Settle a decision that belongs to the user here, or leave its issues out
- Ask only about decisions that belong to the user, in the question format the user sets

Done when the user approves the proposal.

**5. Package.** After the approval, write to GitHub:

1. Reread the affected issues and Epics before writing, as `label-for-issues` requires. Leave out an approved action whose scope, evidence, or membership changed, with its reason. Rerun the Step 1 query and put each new issue on the left-out list for the next grooming, since the approval does not cover it
2. Apply the approved corrections to issues closed as completed without a landed fix. Reopen those whose problem still holds and use their proposed placement. For those whose problem is gone, reopen and close as not planned with the evidence
3. Number each new Epic after the highest `Epic N` title among all Epic issues, closed ones included, in the batch's order
4. Create each new Epic from the template and apply its parent labels through `label-for-issues`
5. Close each issue on the approved cleanup list, except the Epics item 6 closes. Label it as `label-for-issues` describes, and comment the reason and evidence. Close as completed only when the fix landed, as duplicate with the covering issue identified, and as not planned otherwise. Close an Epic as completed only when it is complete, as Step 2 defines it
6. When starting over, close each Epic recorded in Step 1 that is still open and whose closure stays approved after item 1. Close a complete Epic as completed. Otherwise detach its open members as `label-for-issues` describes, then close it as not planned, with a comment that it was not executed, naming where each detached member goes. Its body stays as written
7. Attach each member as a sub-issue and label it as `label-for-issues` describes. A `2-type:postmortem` issue takes the work type its title names: `fix` gives bug, `feat` gives feature, and any other prefix gives task. Apply only approved membership changes through `label-for-issues`
8. Update each Epic body that no longer describes exactly its members, after gains, losses, or earlier drift, except for an Epic closed in item 6. Keep the Order sections of earlier batches. Build one batch list from the new Epics in the approved order, and fill in every new Epic's Order section from it, with the Package date and the kept Epics still open
9. Read back with the `label-for-issues` filters. Each Epic body outside item 6 matches its actual members, including closed ones. Every new Epic's Order section matches the batch list, with its own position and reason. An Epic closed in item 6 holds only closed members. Every applied placement matches the proposal. Every issue in the set is in an Epic, closed, or on the left-out list. Correct discrepancies within the approved scope and read back again, and report those that need a new approval
10. Report a table of the kept Epics, then of the new batch in its order, each with its member count and URL, then the cleanup and the left-out issues

Done when every write is read back as applied.
