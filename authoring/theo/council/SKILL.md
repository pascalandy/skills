---
name: "council"
description: "Trigger this if the user says 'council'."
kind: "dev"
configuration-is-needed: true
---

# Council

Bring in three delegates to help with the user's request, usually for review
or feedback. Each seat takes the reviewer card of a loader skill: model,
effort, T3 provider and effort option, route outside T3, and name in the
report. Read only the card. Do not run `review-loop`.

| Seat | Card |
| --- | --- |
| 1 | `cc-loop` |
| 2 | `codex-loop` |
| 3 | `dsf-loop` |

A member or effort the user names wins. In T3 Code, call
`orchestrator_capabilities` with `search` set to each model name, then start
the three delegates in parallel with `delegate_task`. Outside T3, use each card's route. If a seat
cannot run, report it instead of substituting.

Give each delegate the request and relevant context. For review or feedback,
keep their work read-only. Collect their responses and summarize the useful
findings, disagreements, and recommended next steps.

For a code review, ask each delegate for a score out of 10.
Count each full review pass as one round.
A fresh review after fixes starts a new round.

If the work ends in a pull request, put the results in the PR description.
Put this section before the model and harness line at the end:

```markdown
## Council review

Rounds: 2

| Delegate | Round 1 | Round 2 |
| --- | --- | --- |
| Opus | 7/10 | 9/10 |
| Sol | 8/10 | 10/10 |
| DeepSeek Flash (`ds4p1-slow`) | 7/10 | 9/10 |
```

If a delegate gives no score, write `no score`. Do not invent one.
If the PR is open, edit the description. Do not post a comment for this.
If there is no PR, put the same results in the final reply only.

If you agree with their recommendations, make the changes and request a fresh
review after. Continue this process until all delegates are satisfied with the
outcome.

Do not let repeated reviews result in scope creep. It is your job to fight to
keep scope limited.
