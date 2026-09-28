---
name: "label-for-issues-jev"
description: "Use when labeling or triaging many GitHub issues at once, such as 'label all issues' or 'triage the backlog'. For one or a few issues, use label-for-issues."
---

# Label many issues with Jev

`jevlabel` asks Jev one typed question per condition about each issue, such as "is a way to reproduce the bug stated?", and code turns the answers into labels. `label-for-issues` owns the vocabulary, the classification rules, and comments; this skill adds a bulk first pass in front of it.

Each issue in a run lands in one queue:

- `routine`: every answer the labels rest on is clearly yes or no, and the labels only fill empty families
- `review`: an answer is uncertain, or a label needs a person or new evidence: ready, wontfix, p0, an impediment, or a change to an existing label. Each carries its reasons, and its `fill`: the judged type and p2, each only for an empty family, and none when its text may steer triage
- `skip`: closed, a pull request, agent work in progress, or not asked

Run the CLI with `uv run <skill_dir>/scripts/jevlabel.py`. Every command accepts `--help` and `--json`. Previews and run records go to `$XDG_STATE_HOME/label-for-issues-jev/runs/`, by default `~/.local/state/label-for-issues-jev/runs/`.

## Workflow

1. **Load the owner.** Load `label-for-issues` from the active skill catalog. The CLI reads its `## Labels` JSON from the sibling skill directory. If it is missing, report the missing dependency and stop.
   *Complete when `label-for-issues` is loaded.*
2. **Check readiness.** Run `jevlabel doctor -R <owner/repo> --online` and fix what it names. For missing canonical labels, run `jevlabel labels -R <owner/repo> --dry-run`, then, for a request that allows changes, the same without `--dry-run`. It creates missing labels and fixes the color or description of exact names. Report each case variant or near-duplicate it names; migrating one needs the user's approval. Without a TypeSafe key, only previews work: report the missing key and stop after step 4.
   *Complete when every check passes, or each failure is reported with its fix.*
3. **Get consent for a private repository.** Issue text goes to TypeSafe, which hosts in the US. When `doctor` reports that a private repository has no consent, run the preview in step 4, then show the user the payload file it names and the terms that `jevlabel consent --help` prints. Ask whether its issue text may be sent. Only after they approve, run `jevlabel consent add <owner/repo> --by "<their name>"`. Never approve on their behalf.
   *Complete when the repository is public, consent is recorded, or the user declined.*
4. **Preview.** Run `jevlabel run -R <owner/repo> --dry-run`. Select issues with `--issue N` (repeatable), `--search QUERY`, or `--state open|closed|all`, and cap requests with `--max-requests N`. The preview names each skipped issue and why, the requests, the estimated tokens and cost, and the payload file holding the exact request bodies. Nothing goes to TypeSafe.
   *Complete when the preview file exists and its counts are reported.*
5. **Run.** Run the same selection without `--dry-run`, adding `--json` to read each issue's queue, `add`, `remove`, `fill`, `reasons`, and `missing`. The record file it names also holds every answer and probability. A failure stops the run and keeps a partial record; fix the cause it names and rerun.
   *Complete when a run record exists.*
6. **Apply the clear labels.** For a request that allows changes, run `jevlabel apply <run-id> --dry-run`, then `jevlabel apply <run-id>`. It adds each routine issue's labels and each review issue's `fill`. It rereads each issue first, adds only labels whose family is still empty, never removes one, and reads the labels back. An issue changed since the run is `stale`: run it again before applying. A review-only request stops at the dry run.
   *Complete when `apply` reports no failure, or each failure is reported with the log it names.*
7. **Investigate review issues.** Work through each review issue with the Inspect and Assess steps of `label-for-issues`, then apply what the evidence supports. Read the reasons as leads, not verdicts: each names the condition to check, and `missing` names what the issue lacks. A type or priority that `apply` filled is Jev's judgment; change it when the evidence disagrees. Nominated labels need the evidence `label-for-issues` requires, such as a recorded readiness review for ready. A comment is written only when the user asks for one.
   *Complete when each review issue has an assessment, or is reported as left open with the reason.*
8. **Report.** Give the run ID, the queue counts, the tokens and cost, the labels changed, the review outcomes, and any failures. Report the calibration status that `calibration` in `assets/questions.toml` records, such as `partial`, with its caveats.

## Calibrate

Thresholds in `assets/questions.toml` start as guesses. To measure them, run over issues whose labels a person has reviewed, for example `jevlabel run -R pascalandy/skills --state all`, then `jevlabel compare last`. It counts where the judged type and state agree with the existing labels, which are a baseline, not ground truth. Follow principle 10 of the `references/jev-principles.md` file in `create-a-jev-cli-decision-wrapped-in-a-skill`: assign development and final cases before tuning, tune on development cases only, and report too few cases as undersampled. Record the result in `calibration`.

## Change the questions

`assets/questions.toml` holds every question, its criteria, and its thresholds; the `decide` function in `scripts/jevlabel.py` turns the answers into labels. Before changing a question, load `typesafe-ai` and apply the question review checklist in the same `jev-principles.md`. The CLI enforces the mechanical rules: the question set matches what `decide` consumes, criteria keep the `cannot-tell` option, backticked paths exist in the state, and every Noul has ordered thresholds. Thresholds are per question; never copy one to another question.
