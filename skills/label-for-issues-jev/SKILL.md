---
name: "label-for-issues-jev"
description: "Use when labeling or triaging many GitHub issues at once, such as 'label all issues' or 'triage the backlog'. For one or a few issues, use label-for-issues."
---

# Label many issues with Jev

`jevlabel` asks Jev one typed question per condition about each issue, such as "is a way to reproduce the bug stated?", and code turns the answers into labels. `label-for-issues` owns the vocabulary, the classification rules, and comments; this skill adds a bulk first pass in front of it.

Run the CLI with `uv run <skill_dir>/scripts/jevlabel.py`. Every command accepts `--help` and `--json`. Previews and run records go to `$XDG_STATE_HOME/label-for-issues-jev/runs/`, by default `~/.local/state/label-for-issues-jev/runs/`.

## Workflow

1. **Load the owner.** Load `label-for-issues` from the active skill catalog. The CLI reads its `## Labels` JSON from the sibling skill directory. If it is missing, report the missing dependency and stop.
   *Complete when `label-for-issues` is loaded.*
2. **Check readiness.** Run `jevlabel doctor -R <owner/repo>` and fix what it names. Missing canonical labels need the setup-only request of `label-for-issues` first. A missing TypeSafe key blocks live runs, not previews.
   *Complete when every check passes, or each failure is reported with its fix.*
3. **Get consent for a private repository.** Issue text goes to TypeSafe, which hosts in the US. When `doctor` reports that a private repository has no consent, run the preview in step 4, then show the user the payload file it names and the terms that `jevlabel consent --help` prints. Ask whether its issue text may be sent. Only after they approve, run `jevlabel consent add <owner/repo> --by "<their name>"`. Never approve on their behalf.
   *Complete when the repository is public, consent is recorded, or the user declined.*
4. **Preview.** Run `jevlabel run -R <owner/repo> --dry-run`. Select issues with `--issue N` (repeatable), `--search QUERY`, or `--state open|closed|all`, and cap requests with `--max-requests N`. The preview names each skipped issue and why, the requests, the estimated tokens and cost, and the payload file holding the exact request bodies. Nothing goes to TypeSafe.
   *Complete when the preview file exists and its counts are reported.*

## Change the questions

`assets/questions.toml` holds every question, its criteria, and its thresholds. Before changing one, load `typesafe-ai` and apply the question review checklist in the `references/jev-principles.md` file of `create-a-jev-cli-decision-wrapped-in-a-skill`. The CLI enforces the mechanical rules: the question set matches what the policy code consumes, criteria keep the `cannot-tell` option, backticked paths exist in the state, and every Noul has ordered thresholds. Thresholds are per question; never copy one to another question.
