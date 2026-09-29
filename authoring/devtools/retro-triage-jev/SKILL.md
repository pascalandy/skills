---
name: "retro-triage-jev"
description: "Use when triaging retro or agent-feedback issues about skills into accept or refuse decisions. For issue labels, use label-for-issues-jev."
---

# Retro triage with Jev

Decide which user stories from a skill-feedback retro change a skill. The bar: fix what makes a skill wrong, contradictory, or confusing for an agent, leave edge cases to agents, and keep each fix to one sentence or one changed line.

Read-only reviewers check every story against the source. Jev then answers three yes/no questions per story, and `scripts/retro_triage.py` decides in code. Jev is a second opinion: its scores drift a few hundredths between runs, so a `contested` story is your call and the user's, not the script's.

## Workflow

1. **Collect.** Read each issue the user names with `gh issue view <n> -R <owner/repo> --comments`, and give every user story an id such as `147-4`. *Complete when every story has an id.*
2. **Review.** Give each issue to one read-only reviewer with [the reviewer brief](references/reviewer-brief.md), and collect their JSON lines in one `stories.jsonl` inside a `mktemp -d` directory. Work inline when delegation is unavailable or disallowed. *Complete when every story has a line with verified evidence and a fix.*
3. **Judge.** Run `uv run <skill_dir>/scripts/retro_triage.py <stories.jsonl>`, and see its `--help` for flags. A private repository needs the consent `label-for-issues-jev` records: before asking for it, show the user the `--dry-run` output and the terms. *Complete when every story has a decision.*
4. **Decide.** Re-read the evidence of each `contested` story and make the call, saying why when you overrule Jev or the reviewer. Show the user one table: story, decision, and the exact fix or a one-line reason. *Complete when the user accepts or changes each decision.*
5. **Ship.** After approval, open one PR per skill with its evidence in the body, following the repository's rules for changing a skill. Put `Fixes #n` in the PR that holds an issue's last accepted story. Comment every story's decision on its issue, and close an issue with no accepted story as not planned. Keep session IDs out of public repositories. *Complete when every issue has a decision comment or is closed.*
