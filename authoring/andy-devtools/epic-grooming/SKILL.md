---
name: "epic-grooming"
description: "Use only when explicitly invoked as `epic-grooming`, to rank open GitHub issues and group them into Epics."
kind: "dev"
---

# Epic grooming

Turn a backlog of GitHub issues into Epics that someone can pick up one at a time: check which issues still hold, rank them by return, group them by outcome, describe each one in plain words, then create the Epics once the user approves. Planning, implementing, and reviewing an Epic happen later, in the user's own steps, so the Epics describe problems only.

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

**1. Scope.** By default, take the open issues that belong to no Epic, plus every open Epic and the state of its members; use the overview and Epic filters of `label-for-issues`. When the user names another set, such as a label, take that set and the open Epics. Read each issue's body and comments, and each Epic's body and sub-issues. Done when every issue and Epic in scope is read.

**2. Verify.** Fetch the default branch, then check each issue against that branch's current files and the recently merged PRs. Give each issue one verdict with its evidence:

- **Holds**: the problem is still in the current files
- **Fixed**: a merged change already solves it; cite the PR or commit
- **Stale fix**: the problem holds, but its proposed fix quotes text that has since changed

Also flag a closed issue that the set refers to and that was closed as completed while its fix never landed, and an open Epic whose members are all closed, to close once its completion criterion holds. Done when every issue has a verdict.

**3. Rank.** Find the patterns across the issues: the skills or areas that keep collecting findings, and the recent PRs that left a problem unsolved or created one. Rank by return: how often the problem recurred and what each occurrence cost, against the work the fix takes. Group the issues that one change fixes. Tier the result as P1 (at most three), P2, and P3, and list the issues to close or mark as duplicates, each with its reason. Done when every issue that holds sits in one tier or on the close list.

**4. Propose.** Present the tiers, the Epics, and the cleanup, and change nothing on GitHub yet.

- Group by outcome: one Epic per result, with a completion criterion someone can check. Group neither by skill nor by priority
- Place an issue in an open Epic when that Epic's outcome covers it; open a new Epic otherwise. Inside an Epic, group the issues by pipeline step or subsystem
- Each issue lands in exactly one place: an Epic, the cleanup list, or a short list of issues left out with the reason
- Write each issue as an issue entry from the template, so the user decides without opening the issue
- An Epic holds no open decision. Settle a decision that belongs to the user here, or leave its issues out
- Ask only about decisions that belong to the user, in the question format the user sets

Done when the user approves the proposal.

**5. Package.** After the approval, write to GitHub:

1. List the open issues again, and verify each one that arrived since the proposal as in Step 2. Place it only when an Epic's outcome covers it and it needs no decision from the user, and flag it in the report as added after the approval; otherwise add it to the left-out list with the reason
2. Number each new Epic after the highest `Epic N` title among all Epic issues, closed ones included
3. Create each new Epic from the template, labeled `4-epic:parent`
4. Attach each member as a sub-issue and label it as `label-for-issues` describes. A `2-type:postmortem` issue takes the work type its title names: `fix` gives bug, `feat` gives feature, and any other prefix gives task
5. When an existing Epic gains or loses a member, update its body so it still describes every member
6. Close each issue on the cleanup list, label it as `label-for-issues` describes, and comment the reason and the evidence. Close as completed only when the fix landed, as duplicate when another issue covers it, and as not planned otherwise
7. Read back with the `label-for-issues` filters: each Epic lists exactly its planned members, no member lacks a parent, and every issue in the set is in an Epic, closed, or on the left-out list
8. Report a table of each Epic with its member count and URL, then the cleanup and the left-out issues

Done when every write is read back as applied.
