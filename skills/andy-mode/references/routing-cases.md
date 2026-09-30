# Routing cases

Run each request in a fresh session that has andy-mode installed. A case passes when the first route file the agent reads is the expected one. A route that the chosen playbook calls for may load after it.

| Request | Expected |
|---|---|
| `andy-mode ; RetroSkill` | `playbooks/retro-skill.md` |
| `andy-mode ; retro skill` | `playbooks/retro-skill.md` |
| `andy-mode ; retro` | `playbooks/retro-skill.md` |
| `andy-mode ; retro general` | `playbooks/retro-general.md` |
| `andy-mode ; 2nd-pass` | `../2nd-pass/SKILL.md` |
| `andy-mode ; 2nd pass` | `../2nd-pass/SKILL.md` |
| `andy-mode ; pa-retro` | The route tables and a question. No route runs |
| `ND mode ; retro` | `playbooks/retro-skill.md` |
| `indie mode ; retro general` | `playbooks/retro-general.md` |
| `andy-mode ; QA` | `playbooks/qa.md` |
| `andy-mode ; pa-qa` | The route tables and a question. No route runs |
| `andy-mode ; note this idea: a shared inbox for agent feedback` | `playbooks/idea.md` |
| `andy-mode ; docs reorg` | `playbooks/docs-cleaner.md` |
| `andy-mode ; docs cleaner` | `playbooks/docs-cleaner.md` |
| `andy-mode ; document the change we just shipped` | `playbooks/docs.md` |
| `andy-mode ; fix our docs` | The route tables and a question, since `docs` and `docs-cleaner` both fit |
| `andy-mode ; ontology-map` | The route tables and a question. No route runs |
| `andy-mode ; Wiki Map` | `playbooks/wiki-map.md` |
