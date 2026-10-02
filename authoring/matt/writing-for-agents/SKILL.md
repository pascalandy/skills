---
name: "writing-for-agents"
description: "Use when creating, editing, or reviewing a skill, AGENTS.md, CLAUDE.md, or another document agents read."
kind: "general"
---

Write documents an agent reads so that it takes the same _process_ every run: a skill, an `AGENTS.md` or `CLAUDE.md`, a doc reached by a pointer. The packaging differs; the best practices below do not.

## Terms

- **This skill**: `writing-for-agents`, the skill you are reading
- **Target skill**: the skill being created, edited, improved, or reviewed
- **Target document**: any other document an agent reads, such as `AGENTS.md`
- **Skill validator**: `scripts/validate_skill.py` in this skill's folder. It checks the target skill you point it at
- **BP**: a best practice from the checklist below, cited by its fixed ID, such as `BP_06`

## Pick the branch

- **Create, edit, or improve a target skill**: follow [Create, edit, or improve a skill](#create-edit-or-improve-a-skill)
- **Review a target skill or target document**: follow [Review](#review)
- **Write or edit a target document**: apply the "Any agent document" BPs; the skill validator does not apply

## Create, edit, or improve a skill

Copy this checklist and track your progress:

```
Skill progress:
- [ ] Step 1: BP checklist filled (existing skill)
- [ ] Step 2: Evaluations and baseline
- [ ] Step 3: Frontmatter
- [ ] Step 4: Body
- [ ] Step 5: Scripts and prerequisites
- [ ] Step 6: Skill validator silent
- [ ] Step 7: Evaluations beat the baseline
- [ ] Step 8: BP checklist complete
```

**Step 1: BP checklist filled.** For an existing target skill, fill the [BP checklist](#best-practices-checklist) with Review steps 1 and 2, so the evaluations and fixes target what fails. Skip this step for a new skill.

**Step 2: Evaluations and baseline.** Write three scenarios from real failures and run them without the target skill (BP_20). Skip steps 2 and 7 for a wording-only edit.

**Step 3: Frontmatter.** Write the name and the trigger (BP_13, BP_14, BP_21).

**Step 4: Body.** Steps first; move what only some branches need into files linked from `SKILL.md` (BP_01).

**Step 5: Scripts and prerequisites.** Turn work that must give the same result every run into a script, and name each tool it needs (BP_17, BP_18).

**Step 6: Skill validator silent.** Run the skill validator, fix each error, and rerun. Done when it prints nothing, or every warning left has a reason you tell the user.

**Step 7: Evaluations beat the baseline.** Rerun the scenarios. Done when the target skill passes every expected behavior; otherwise return to Step 4.

**Step 8: BP checklist complete.** Fill the BP checklist again. Done when every BP is ticked.

## Review

1. Run the skill validator on the target skill. For a target document, skip this step
2. Fill the [BP checklist](#best-practices-checklist) against the target
3. Report the findings grouped by BP, with a count per BP and a fix per finding. End with a `Pass:` line naming every applicable BP without findings, so each applicable BP appears once

```
BP_06 Every line relevant: 2
- SKILL.md:40 "Be thorough." changes nothing → delete the sentence
- references/api.md:12 restates the package.json scripts → point to package.json
BP_14 Description is a trigger: 1
- SKILL.md:3 says what the skill is, never when to load it → "Use when …"
Pass: BP_01–BP_05, BP_07–BP_13, BP_15–BP_21
```

A finding that fits two BPs goes under the more specific one.

## Skill validator

Requires `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/)). Confirm it with `uv --version`, then run from any folder:

```bash
uv run <this-skill-folder>/scripts/validate_skill.py <target-skill-folder>
```

It prints nothing for a clean target skill. Each finding is one line, `path:line: error|warning: BP_NN Title: message`, and any error exits 1. It checks the BPs marked _(validator)_; every other BP needs your judgment.

The link check covers inline links with at most one level of parentheses, angle-bracket destinations, and single-line reference definitions inside the target folder. Check other links and inline-code paths yourself. The validator checks inline-code paths for backslashes only.

## Best practices checklist

Copy the IDs and titles into your reply: every section for a target skill, "Any agent document" alone for a target document. Tick a BP when it passes, or when it does not apply and you give the reason. Leave it open with its finding count when it fails.

IDs never change and are never reused. To change a practice, move its line under a `### Voided` heading at the end with `void <date>, replaced by BP_NN`, and give the new practice the next free ID.

### Any agent document

- [ ] **BP_01 Progressive disclosure**: the top holds the steps and what every branch needs; the rest sits one link away, each pointer saying when to read it _(validator: links between reference files)_
- [ ] **BP_02 One place per meaning**: no meaning stated twice; each concept under one heading; nothing a file or command already shows
- [ ] **BP_03 One term per concept**: one word per concept, everywhere
- [ ] **BP_04 Leading words**: a word the model already knows replaces a spelled-out description
- [ ] **BP_05 Positive phrasing**: state what to do; a ban only as a hard guardrail, paired with what to do
- [ ] **BP_06 Every line relevant**: no line the agent would follow by default, no stale layers
- [ ] **BP_07 No dated text**: the current method only; a deprecated one moves to a collapsed "Old patterns" section _(validator)_
- [ ] **BP_08 Concrete examples**: input/output pairs where quality depends on them; a template as strict as the output needs
- [ ] **BP_09 Workflows**: complex tasks as numbered steps with a copyable checklist; each decision point sends each case to a named branch
- [ ] **BP_10 Completion criteria**: every step ends on a condition the agent can check
- [ ] **BP_11 Feedback loops**: quality-critical work runs validate, fix, repeat, with a rule for when to stop
- [ ] **BP_12 Links resolve**: every relative link reaches a file, written with forward slashes _(validator)_

### Skills only

- [ ] **BP_13 Name**: lowercase letters, digits, and hyphens, at most 64 characters, matching the folder; specific; a gerund such as `processing-pdfs` preferred _(validator: format)_
- [ ] **BP_14 Description is a trigger**: says when to load the skill, in the words a request would use; at most 1,024 characters, no XML tags _(validator: limits)_
- [ ] **BP_15 SKILL.md under 500 lines** _(validator)_
- [ ] **BP_16 Contents list**: a reference file over 100 lines starts with a Contents list, added only after the user approves _(validator)_
- [ ] **BP_17 Scripts for repeatable results**: work that must give the same result every run ships as a script the skill runs
- [ ] **BP_18 Prerequisites named**: each tool a step needs, with its install command and a check that it is available, before the first step that uses it
- [ ] **BP_19 Works on any agent**: instructions any agent can follow; a step tied to one agent names it and gives the fallback
- [ ] **BP_20 Evaluations first**: three scenarios and a baseline before the instructions
- [ ] **BP_21 Invoke by a word**: a skill that must never fire on its own says ``Use only when explicitly invoked as `<word>`.``, with the word in backticks and no actor named _(validator: warning)_

## References

- [writing-levers.md](references/writing-levers.md): BP_01 to BP_06, plus context pointers and the two loads. Read when writing or reviewing any document
- [patterns.md](references/patterns.md): BP_07 to BP_11. Read when the document has steps, examples, templates, or a validation step
- [skill-format.md](references/skill-format.md): BP_13 to BP_16, BP_19, and BP_21, plus invocation and layout. Read when writing a skill's frontmatter or deciding its files
- [scripts-and-evals.md](references/scripts-and-evals.md): BP_17, BP_18, BP_20. Read when a skill runs code, or before writing a new skill
