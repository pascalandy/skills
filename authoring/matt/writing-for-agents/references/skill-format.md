# Skill format

What changes when the document is a skill: frontmatter, invocation, and layout. Each `BP_` section explains one best practice listed in `SKILL.md`.

## BP_13 Name

The open Agent Skills specification and the strictest agent platforms require:

- 1 to 64 characters: lowercase letters, digits, and hyphens
- No hyphen at the start or end, and no `--`
- The same name as the skill's folder
- No reserved word: `anthropic`, `claude`

Prefer the gerund form: `processing-pdfs`, `analyzing-spreadsheets`, `writing-documentation`. Noun phrases such as `pdf-processing` and actions such as `process-pdfs` also work. Avoid vague names such as `helper` or `utils`, generic ones such as `documents` or `data`, and a mix of patterns within one collection.

In a review, report a weak name on an existing skill and leave the rename to the user: renaming breaks every trigger and link that uses the old name.

## BP_14 Description is a trigger

The description is the skill's top-level context pointer (see context pointers in `writing-levers.md`). It says when to load the skill, in the words a request or another skill would use, with one trigger per branch. It may say why. It says what the skill does only when the name does not:

```yaml
description: "Use when extracting text or tables from PDFs, filling PDF forms, or merging PDFs."
```

Limits: 1 to 1,024 characters and no XML tags. A placeholder such as `<route>` counts as a tag, so name a real value instead.

Agents list each installed skill's name and description, but a large catalog can drop descriptions to fit its budget. A skill that must load every session also needs a line in the always-loaded `AGENTS.md`, or the agent's equivalent.

### Invocation

- A **model-invoked** skill keeps a description the agent matches, so the agent and other skills can reach it, and the human can still type its name. The description is permanent context load paid for discovery. A model-invoked skill that is all reference is also a home for reference several skills share
- A **user-invoked** skill is hidden from matching by the agent's own setting: no context load, but the human is the index that must remember it. The setting differs per agent, and a host `AGENTS.md` may forbid it
- An **explicitly invoked** skill is the portable middle ground: it keeps its description, so it costs context load, but loads only when a prompt or another skill calls it by its word. Write it as BP_21 describes

Make a skill model-invoked only when the agent or another skill must reach it unaided. Split off a new model-invoked skill only for a distinct trigger word you actually use, or for a skill another skill must reach: its description costs context load every turn.

When hand-fired skills multiply past what you remember, a **router skill** names them and says when to reach for each, so you remember one skill instead of many.

## BP_21 Invoke by a word

A skill that fires only when called by a word still keeps a description: agents hide skills through settings that differ, and a host `AGENTS.md` may keep every skill model-invocable. Write ``Use only when explicitly invoked as `<word>`.`` plus an optional tail for what it does:

- Write _invoked_: a mention also fires on talk about the skill, and a common word like `plan` fires on everyday prompts and on other skills' descriptions
- Mark `<word>`, usually the skill name, with backticks. Quote anything else with backticks or single quotes: when the frontmatter wraps the description in double quotes, an inner `"` ends the value
- Name no actor: _the user_ makes the agent judge who is speaking, so a delegated prompt or another skill's call gets refused

```yaml
description: "Use only when explicitly invoked as `tdd`."
```

## BP_15 SKILL.md under 500 lines

The agent loads all of `SKILL.md` once the skill fires. Keep it under 500 lines, a ceiling rather than a target, and move detail into the files it links (BP_01).

## Layout

```
pdf-processing/
├── SKILL.md       overview and navigation
├── references/    read on demand
├── scripts/       run, not read
└── assets/        templates and data
```

Three ways to link reference from `SKILL.md`:

1. **Guide with references**: a quick start in `SKILL.md`, then one line per advanced topic, such as `**Form filling**: see [FORMS.md](FORMS.md) for the complete guide`
2. **By domain**: one file per domain, such as `reference/finance.md` and `reference/sales.md`, so a sales question loads only the sales schemas. Add a `grep` line per file so the agent can search without reading
3. **Conditional details**: the basic path inline, the advanced path linked, such as `**For tracked changes**: see [REDLINING.md](REDLINING.md)`

## BP_16 Contents list

A reference file over 100 lines starts with a Contents list that matches its headings, so a partial read still shows the whole file. Add one only after the user approves: across a collection, the change touches many files at once.

## BP_19 Works on any agent

Write for any agent that loads skills, such as Claude Code, Codex, Pi, or OpenCode. Say "the agent" rather than a product name, and give instructions any agent can follow: shell commands, paths relative to the skill's folder, and plain Markdown. A step that needs one agent's tool or setting names that agent and gives the fallback.
