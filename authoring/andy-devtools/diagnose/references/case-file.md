# The case file

One Markdown file holds the whole state of a case, so an agent resuming after compaction, a new session, or a fresh subagent after a retraction reads `case.md` and knows where the case stands. It is also the fact packet `interrogate` reviews. Every section is a strict table; a cell never holds `|`.

## Template

```markdown
# Case <YYYY-MM-DD>-<slug>: <one-line symptom>

- Requested outcome: diagnosis | fix
- Variable: <hosts, users, versions, time window>
- Report: <where the report and its attachments live>
- Verify loop: <verify-<app> path, or none named>
- Ladder: <cli | service | desktop | web | mobile>
- Current layer: <n>

## Controls
| id | control | type | differs by | matches | not broken the same way because |
|---|---|---|---|---|---|

## Facts
| id | kind | layer | where | statement | variable | control | source | artifact | supersedes |
|---|---|---|---|---|---|---|---|---|---|

## Hypotheses
| id | claim | from | killed if | origin | status | by |
|---|---|---|---|---|---|---|

## Judgments
| h | f | mark | because | by |
|---|---|---|---|---|

## Log
| step | type | target | detail | result |
|---|---|---|---|---|

## Interventions
| step | who | quote | category |
|---|---|---|---|

## Decisions
| question | options | recommended | chosen | by |
|---|---|---|---|---|

## Close
```

## Column rules

- **Controls.** `differs by` names the suspected factor; `matches` lists what is held equal; `not broken the same way because` is required
- **Facts.** `kind` is `signal`, `noise`, `symptom`, or `context`. `where` is `field` or `lab`. `variable` and `control` hold readings with units, and the control's id. `source` names the probe or report, who ran it, the host, the window, and the tool version. `artifact` is a saved file under `artifacts/`, or the report itself. An absence states its coverage in `statement`. `supersedes` names the fact a re-gathered fact replaces
- **Hypotheses.** `from` cites at least one fact; `killed if` is the prediction that would eliminate it. `origin` is `new`, `split:H2`, `merge:H4,H5`, `combine:H3,H6`, `repro`, `human`, or `reviewer`. A split or a merge sets its parent's `status` to `replaced`, so the parent stops counting toward strength. A combination row names its members and their roles in `claim`
- **Judgments.** Append-only. A later row for the same hypothesis and fact supersedes the earlier one and says why in `because`, so a misread fact is corrected without touching it. Every `x` cites the fact it rests on. When a fact is superseded, the judgments on it reopen
- **Log.** `type` is `discriminate` (with what each live hypothesis predicted, written before the probe ran), `descend` (with the reason), `tactic`, `reverify`, `validate`, `interrogate`, or `note`
- **Interventions.** Quote every human input that changed the course of the case. `category` is `control`, `fact`, `check`, `pushback`, `access`, `proxy`, or `decision`. The retros read this section

## Who writes what

| Part | Agent | Reviewer | Pascal |
|---|---|---|---|
| Facts | Appends rows for saved artifacts or quoted reports. Never edits | Proposes `reverify` rows for gathering defects | Appends observations, retires a fact with a reason |
| Hypotheses | Adds with `from` and `killed if` | Reports facts no hypothesis explains | Adds as `by: human`, judged like any other |
| Judgments | Writes with a reason. Corrects by appending a superseding row | Proposes `x` rows citing a fact | Appends `x` rows citing a fact |
| Decisions | Writes options and a recommended default | Nothing | Chooses |

The reviewer writes nothing. The agent appends each row the reviewer proposes, with `by: reviewer`.

## Reading the matrix by hand

A hypothesis is **eliminated** when its current judgment on a current in-scope fact is `x`. The **strength** of a signal or symptom is the number of live hypotheses marked `+` on it. A **candidate** is marked `+` on every in-scope signal and symptom and `x` on none. Before each step, take the first row that holds:

| Condition | Next |
|---|---|
| No control | Choose one (step 2) |
| No signal or symptom fact | Gather at the current layer |
| No live hypothesis | Hypothesize from the unexplained facts, after the repair tactics |
| A live hypothesis has an unjudged in-scope signal or symptom | Judge those cells |
| Two or more candidates | Discriminate with their killing predictions, or descend if no layer-local probe can split them |
| One candidate, validation incomplete | Validate: killing prediction, noise and context cells, parity, review |
| One candidate, validated | Decide (step 7) |
| No `tactic` row since the last descent, and a signal of strength 2 or less | Repair tactics (step 6) |
| Otherwise | Descend |
