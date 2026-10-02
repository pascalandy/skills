# Retro global

Review the coding agent's **environment** so future runs go better. This is not an incident postmortem or a review limited to the skills loaded in the session.

## Procedure

1. Read the primary sources for the session the user names: conversation, tool results, relevant diffs, and checks. Default to the current session. If the relevant history is inaccessible, identify what is missing and ask for it rather than reconstructing events.
2. Look for candidates for improvement in the categories below. Treat them as prompts, not a requirement to produce a finding in each category. Inspect the existing mechanism before proposing a replacement.
3. Keep a finding only when you can cite a specific session observation and explain how the proposed change would help a future run. Rank by likely impact and recurrence, taking implementation cost into account. Separate facts from inference.
4. Present the findings to the user. A finding is easier to act on when it covers what happened and the evidence, what exists today, the smallest change, and how to check it worked; tradeoffs and blast radius help when material. If none pass the evidence bar, say so and stop. Suggest changes; do not edit the environment as part of the retrospective.

## Where to look

- **Navigation**: how easy was it for the agent to find the right files? Are there hidden dependencies between files? Would a **navigation pointer**, such as a "Read on demand" line in the repo's `AGENTS.md`, make it easier? _Use when_ the session took a long time to find a piece of information.
- **Automated checks**: could a check have caught a mistake the agent made? Read the repo's `justfile` (usually `just check`) and `lefthook.yml` first, so a check that exists but sits unwired or silently broken is the finding, not a reinvention. A repo with no **guardrail** (no `just check`, or no lefthook hook running it) is itself a finding. _Use when_ the agent made a mistake a check could have caught, or the repo has no guardrail.
- **Coding standards**: standards live in skills (`coding-language`, `coding-standard`, the `principle-*` skills). Should a skill gain, drop, or clarify a rule? Classify the violation first: a **mechanical** one (a fixed syntactic pattern, a banned API, an import shape, a file-location rule) gets a deterministic check in `just check`, not a rule in prose. Keep skill rules for **judgement calls** no check can replace. Load `writing-for-agents` before proposing edits to a skill or steering file. _Use when_ a review missed a mistake, or the agent broke a rule a skill states.
- **Steering files**: should always-loaded instructions move behind a pointer, into a skill, or into a check? These load every turn: the global `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, and `~/.config/opencode/AGENTS.md`, the repo's `AGENTS.md`, the agent's memory index (`MEMORY.md`), and every skill description. _Use when_ one of them is large, or a skill fired when it should not have, or failed to fire.
- **Tool economy**: did the agent make expensive tool calls that could be streamlined? Is any custom tooling (a CLI, an MCP server, a `just` recipe) particularly token-inefficient? _Use when_ the agent made an expensive tool call.
- **No-ops**: look for instructions in steering files or skills that don't change the agent's behavior. Distinguish a useless instruction from one the agent failed to follow. _Use when_ the steering files are large and unwieldy.
- **Information access**: look for opportunities to increase the agent's access to information, such as teeing dev server logs or read-only access to third-party services. _Use when_ a crucial piece of information was not available to the agent.

## Publishing findings

If the user wants issues, draft one per finding in the repository that owns the change: the project for its `AGENTS.md`, `justfile`, or hooks, `pascalandy/skills` for a skill, and `pascalandy/dotfiles` for global config it tracks. A finding with no owning repository stays in the report. Write in the language of the conversation. Compress with the `concise` skill.

**Titles.** Use Conventional Commits in the form `type(scope): subject`, where the scope names the area to change, for example `feat(lefthook): run just check before push`. Use `fix` when an instruction or check is wrong, `docs` when an instruction is only unclear or a pointer is missing, and `feat` when a check, step, or tool is missing. Keep the subject short and imperative, naming the change. Name a real symbol when one carries the change, such as a recipe, file, or flag. Do not add a trailing period.

**Body.** The issue is a briefing for whoever triages and fixes it. Use these sections in order. Drop a section when it has nothing to say.

- `## Why`. Open with the user story: "As an agent working in `<repo>`, I want …, so that …". Then, in one or two short paragraphs, say what you were trying to do, what went wrong and the evidence, how you worked around it, and the change you propose.
- `## Scope`. Use bullets to list the files, recipes, hooks, or tools to change. Name both sides of a move or rename. State what is in and out only when the boundary matters.
- `## Tradeoffs`. Name only alternative fixes a reviewer would otherwise ask about.
- `## Blast Radius`. In one to three sentences, name which agents, repos, or workflows the change reaches, why it is safe or risky, and the continuing cost if nothing changes.
- `## Verification`. Name the scenario that failed and the outcome that proves the fix, so whoever fixes it can rerun it.

Before publishing:

1. For each finding, search the target repository's open issues. If one already reports the problem, draft a comment on it instead of a new issue.
2. If the repository is public, remove session IDs, absolute local paths, hostnames, private repo or project names, and any conversation content that isn't about the finding.
3. Run the `2nd-pass` skill on the drafts.

Then, once the user authorizes it, publish with labels `1-needs-triage` and `2-type:postmortem` (or `2-type:task` where the repository lacks it), link the session's PR when one exists, read each issue back, and return the links.
