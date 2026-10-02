# Routing cases

Replay these cases with `just replay-routing andy-mode`, and run `just replay-routing --help` for the table format. A route that the chosen playbook calls for may load after it.

| Request | Reads | Opens with |
|---|---|---|
| `andy-mode ; RetroSkillUsage` | `playbooks/retro-skill-usage.md` | |
| `andy-mode ; retro skill usage` | `playbooks/retro-skill-usage.md` | |
| `andy-mode ; retro` | no route | |
| `andy-mode ; retro-skill` | no route | |
| `andy-mode ; retro global` | `playbooks/retro-global.md` | |
| `andy-mode ; 2nd-pass` | `../2nd-pass/SKILL.md` | |
| `andy-mode ; 2nd pass` | `../2nd-pass/SKILL.md` | |
| `andy-mode ; pa-retro` | no route | |
| `ND mode ; retro skill usage` | `playbooks/retro-skill-usage.md` | |
| `indie mode ; retro global` | `playbooks/retro-global.md` | |
| `andy-mode ; QA` | `playbooks/qa.md` | |
| `andy-mode ; pa-qa` | no route | |
| `andy-mode ; note this idea: a shared inbox for agent feedback` | `playbooks/idea.md` | |
| `andy-mode ; docs reorg` | `playbooks/docs-cleaner.md` | |
| `andy-mode ; docs cleaner` | `playbooks/docs-cleaner.md` | |
| `andy-mode ; document the change we just shipped` | `playbooks/docs.md` | |
| `andy-mode ; fix our docs` | no route | |
| `andy-mode ; ontology-map` | no route | |
| `andy-mode ; Wiki Map` | `playbooks/wiki-map.md` | |
| `andy-mode ; think` | `playbooks/think.md` | |
| `andy-mode ; I think this architecture is simpler. Challenge me` | `playbooks/sparring.md` | |
| `andy-mode ; simple editor` | `playbooks/simple-editor.md` | |
| `andy-mode ; storytelling ; style modeler` | `playbooks/storytelling.md` | |
| `andy-mode ; meta skill creator` | `playbooks/meta-skill-creator.md` | |
| `andy-mode ; meta-sc` | no route | |
