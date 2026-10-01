---
name: "andy-mode"
description: "Use only when explicitly invoked as `andy-mode ; <route>`, where `andy` may be any voice-to-text spelling that sounds like it, such as `ND` or `indie`."
kind: "general"
---

# Andy mode

Andy-mode carries the tools Pascal wrote, one route per tool. Poteto-mode runs engineering work with PStack, and matt-mode prepares it with Matt Pocock's procedures.

## Pick the route

A request names its route after the mode, as in `andy-mode ; qa`. Compare names with case, spaces, hyphens, and underscores ignored, so `RetroSkill`, `retro skill`, and `retro-skill` name one route. An alias counts as its route's name.

- **A name matches.** Read that route's file and follow it to the route's own result.
- **No name, one clear owner.** Run the route whose "Use when" owns the request, and say which route you chose.
- **Two routes fit, or the name matches nothing.** Show the route tables and ask. Run nothing. A retired skill name such as `pa-retro` matches nothing.

Run one route per request. Load another route only when the running route calls for it.

A path that starts with `playbooks/`, `scripts/`, or `references/<route>/` names a file in this skill and resolves from this directory. Links and other paths resolve from the file that names them. A route's own inputs and outputs, such as a wiki's `references/` folder, keep the meaning the route gives them. Load a route's references only when its playbook points to them.

## Routes

### Retro

| Route | Aliases | Use when |
|---|---|---|
| [`retro-skill`](playbooks/retro-skill.md) | `retro` | A skill loaded this session was wrong or confusing enough to cost a detour |
| [`retro-general`](playbooks/retro-general.md) | | The agent's environment could serve the next run better: navigation, checks, steering files, or tools |

### Ideas and quality

| Route | Aliases | Use when |
|---|---|---|
| [`idea`](playbooks/idea.md) | | Write down a rough idea in its author's voice and export it |
| [`qa`](playbooks/qa.md) | | Validate a finished change, or capture a problem someone reports |

### Docs and knowledge

| Route | Aliases | Use when |
|---|---|---|
| [`docs`](playbooks/docs.md) | | Document a change, decision, or artifact that already exists |
| [`docs-cleaner`](playbooks/docs-cleaner.md) | `docs-reorg` | Maintain existing docs: drift, duplicates, frontmatter, or structure |
| [`wiki-map`](playbooks/wiki-map.md) | | Build or maintain a Markdown knowledge base with provenance and indexes |
| [`glossary`](playbooks/glossary.md) | | Create or revise a canonical glossary |
| [`ontology`](playbooks/ontology.md) | | Generate the five-file ontology of a folder of text |
| [`qmd`](playbooks/qmd.md) | | Search, retrieve from, or maintain local QMD collections |
| [`cass`](playbooks/cass.md) | | Search local coding-agent session history |
| [`distill`](playbooks/distill.md) | | Apply a distill prompt to a local text file |
| [`distill-prompt`](playbooks/distill-prompt.md) | | List, choose, or add a distill prompt |

### Reasoning

| Route | Aliases | Use when |
|---|---|---|
| [`sparring`](playbooks/sparring.md) | | Challenge an opinion or an argument |
| [`think`](playbooks/think.md) | | Improve the model of a situation before judging, deciding, or acting |
| [`2nd-pass`](../2nd-pass/SKILL.md) | `2pass` | Review finished work with fresh eyes. It also runs alone as the `2nd-pass` skill |

### Writing and visuals

| Route | Aliases | Use when |
|---|---|---|
| [`writer-sk`](playbooks/writer-sk.md) | | Edit prose for clarity and concision |
| [`simple-editor`](playbooks/simple-editor.md) | | Clean personal notes while keeping the author's raw voice |
| [`storytelling`](playbooks/storytelling.md) | | Discover, write, diagnose, adapt, or explain a narrative |
| [`illustration`](playbooks/illustration.md) | | Design and generate a 16:9 inline illustration |

### Agents and tools

| Route | Aliases | Use when |
|---|---|---|
| [`meta-skill-creator`](playbooks/meta-skill-creator.md) | | Create or refactor a skill with several internal branches behind one entry point |
| [`tavily`](playbooks/tavily.md) | | Search the web or discover URLs through Tavily |
| [`profile-routing-matrix`](playbooks/profile-routing-matrix.md) | | Pick the role, model, and reasoning level for a subagent |
| [`trello`](playbooks/trello.md) | | Manage Trello boards, lists, and cards |

## Callers

A skill or command outside this mode reaches one route by reading its playbook in the active `andy-mode` skill directory, such as `playbooks/retro-skill.md`. It keeps its own task and loads another route only when that playbook calls for it.

Use [routing cases](references/routing-cases.md) when changing a route name, an alias, or this file's routing rules.
