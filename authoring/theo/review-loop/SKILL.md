---
name: "review-loop"
description: "Use when the user says 'review loop', or when codex-loop, cc-loop, or dsf-loop hands over its reviewer."
kind: "dev"
role: "helper"
---

# review-loop

Get a second opinion from one reviewer model, in rounds, until it approves or
the budget ends. The subject is whatever the user names: a code change, a
plan, a file, a text.

Make the most minimal possible changes to appease the reviewer. Be careful of
scope creep and don't be scared to push back.

## Reviewer

A loader skill, such as `codex-loop` or `cc-loop`, gives the model, its
effort, its T3 provider and effort option, its native route, and its name.
Without a loader, take the reviewer of the other family than the author of
the subject: `codex-loop` for an author on Claude, `cc-loop` for an author on
GPT. Other author, or unknown: ask.

A version or effort the user names wins. Do not hardcode an ID. From here on,
"the reviewer" means the chosen one.

## Budget

- Default: 3 rounds total. Round 1 is full. Later rounds check only
  changed parts and open findings.
- Extend to 5 only for security, permissions, auth, data loss, or
  state/concurrency, while a blocker or should stays open with evidence. Or when
  the user asks.
- Stop early if a round returns only nits. Declined nits and comment,
  wording, or format-only fixes need no new round, unless wording is the goal.
- One reviewer only. The reviewer must not start subagents or reviewers.
- Keep a ledger: id, severity, outcome, usage if returned. Never guess it.

## 1. Subject

State the goal and out-of-scope in 1-2 sentences.

**Code change.** Run `git status --short`. Do not stash, discard, or include
unrelated changes. Limit review to the change paths if they separate cleanly.
Otherwise stop and ask. Find the base after `git fetch origin`:

- PR: `gh pr view <n> --json baseRefName,headRefOid`. Check out the branch
  only if clean. Confirm `HEAD` is the PR head, or ahead only by this
  change. Base: `git merge-base HEAD origin/<baseRefName>`.
- Local: `git merge-base HEAD origin/<default-branch>`. No remote: a base
  the user names, or `HEAD` for uncommitted changes only.

The change is base to working tree in those paths, with untracked files.
Use one diff command all rounds. Run covering checks. Do not send code this
change breaks. Note missing or pre-failing checks in the brief.

**Anything else.** The subject is the files the user names. When it lives
only in the conversation or online, write it to one file in your scratch
directory; the reviewer reads that file, since it gets no history.

## 2. Start the reviewer

In T3, call `orchestrator_capabilities` with `search` set to the model name,
since the short list can omit it. Pass the effort through the reviewer's effort
option. Record provider, model, and effort only if exposed. Use `delegate_task`
every round (`role: "review"`, `mode: "async"`). Save `taskId`. New
`clientRequestId` per round. `childThreadId` is storage, not the next target.
Do not use `t3_thread_send`, `create_threads`, or `t3_thread_launch` for review.

If T3 tools are not listed, try one direct capability call. Outside T3, use
the reviewer's native route and keep its ID. If no route runs the reviewer,
report the blocker. Do not substitute a model.

Do not edit the subject while review runs. Wait for the notice. Do not
poll or start a second reviewer. Timeout, error, or no reply is not
approval. On failure, cancel, verify stop, restart with the ledger.

Round 1 brief (T3 children get no history):

```
Review only. Do not edit, commit, push, comment, or start subagents.
Goal: <goal> Out of scope: <scope>
<subject block>
Hold to the smallest change. Flag anything the goal does not need. Other
paths, rare cases, small perf, extra compat: nits.
Reply:
VERDICT: APPROVE or CHANGES
S1 [blocker|should|nit] <location> <claim>. Fix: <suggestion> (stable ids)
```

Code subject block:

```
Repo: <abs path> Base: <sha> Checks: <results>
See: git diff <base> [-- <paths>]; git status --short (read untracked).
Read surrounding code. Find bugs, broken callers, mismatch with the goal.
Skip style unless it hides a bug.
blocker = intended case wrong. should = real bug callers will hit, in goal. nit = rest.
```

Other subject block:

```
Read: <abs paths>. Context you may read: <abs paths or repo>.
Find wrong facts, false assumptions, gaps, contradictions with the context,
mismatch with the goal. Judge what the subject says; judge its wording only
when wording is the goal.
blocker = the subject misses its goal. should = a real gap that will bite. nit = rest.
```

## 3. Answer findings

Check each finding and severity yourself. Another path, rare case, or
small cost is a nit, whatever label it came with.

- Agree: smallest fix. Prefer delete or narrow over new lock, cache,
  helper, option, or section. Fix the case that happened. For code, add one
  focused test that fails without the fix, if the goal needs it.
- Disagree: say why, with evidence (file:line, test, output, source).
- Out of scope or nit: decline in one line. List as follow-up.

Update the ledger. For code, re-run checks and `git diff --shortstat <base>`.
If review grew the subject, cut first. Do not agree just to end the loop.

## 4. Next round

Start one only if budget remains and a blocker or should is open, the
subject changed in substance, or approval does not cover the current
subject. Use a fresh `delegate_task` in T3, or follow up the saved native ID.
Send the round 1 brief, the ledger (`fixed:` / `disagree:` / `declined:` +
evidence), and the change since last round. Tell the reviewer: open ids and
changed parts only. Mark each old id `resolved` or `still open: <reason>`.

## 5. Stop and report

Agreed: APPROVE on the current subject, no blocker or should open, no
concern of your own. Stuck: an item stays disputed after two replies, or
budget ends. Show both sides in 2-3 lines each. The user decides. Budget end
is not approval.

Change only the subject's local files. Do not commit, push, or post.

Report: rounds, model, effort if verified, what the reviewer changed, size
before/after, fixed and declined findings with reasons, usage if exposed
(else say not).
