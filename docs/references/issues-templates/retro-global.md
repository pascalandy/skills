# Issue template: retro-global

Verbatim copy of the title and body rules in `authoring/andy/andy-mode/playbooks/retro-global.md` (`andy-mode ; retro-global`), taken 2026-10-04. The playbook gives no fenced template, only these rules. Published with labels `1-needs-triage` and `2-type:postmortem` (or `2-type:task` where the repository lacks it)

**Titles.** Use Conventional Commits in the form `type(scope): subject`, where the scope names the area to change, for example `feat(lefthook): run just check before push`. Use `fix` when an instruction or check is wrong, `docs` when an instruction is only unclear or a pointer is missing, and `feat` when a check, step, or tool is missing. Keep the subject short and imperative, naming the change. Name a real symbol when one carries the change, such as a recipe, file, or flag. Do not add a trailing period.

**Body.** The issue is a briefing for whoever triages and fixes it. Use these sections in order. Drop a section when it has nothing to say.

- `## Why`. Open with the user story: "As an agent working in `<repo>`, I want …, so that …". Then, in one or two short paragraphs, say what you were trying to do, what went wrong and the evidence, how you worked around it, and the change you propose.
- `## Scope`. Use bullets to list the files, recipes, hooks, or tools to change. Name both sides of a move or rename. State what is in and out only when the boundary matters.
- `## Tradeoffs`. Name only alternative fixes a reviewer would otherwise ask about.
- `## Blast Radius`. In one to three sentences, name which agents, repos, or workflows the change reaches, why it is safe or risky, and the continuing cost if nothing changes.
- `## Verification`. Name the scenario that failed and the outcome that proves the fix, so whoever fixes it can rerun it.
- `<details>` with `<summary>👨🏻‍🍳 Details for the agent</summary>`. Free form, for the agent doing the work; the human reading the issue can skip it: technical details, non-functional requirements, links to related issues or PRs.
