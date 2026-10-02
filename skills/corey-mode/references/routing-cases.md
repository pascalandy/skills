# Routing cases

Maintainer reference. Ordinary use does not load this file.

Replay these cases after a change to the description, a route, its "Use when", or the routing rules in `SKILL.md`, and after an upstream refresh adds or removes a playbook.

Replay them with `just replay-routing corey-mode --project authoring/corey-mode/tests/routing-project`, and run `just replay-routing --help` for the table format. The project holds a README that describes a product called Acme Notes, a landing page `index.html` with an FAQ section, and a `build.sh` that fails because it copies `index.htm`.

| Request | Reads | Opens with |
|---|---|---|
| `marketing: my landing page in index.html isn't converting. What should I change?` | `playbooks/cro/cro.md` | `Route: cro` |
| `My landing page in index.html isn't converting. What should I change?` | none |  |
| `marketing ; copywriting for the hero section of index.html` | `playbooks/copywriting/copywriting.md` | `Route: copywriting` |
| `marketing: we launch Acme Notes next month. Plan the launch, then write the welcome email sequence and the landing page copy.` | `playbooks/launch/launch.md`, `playbooks/emails/emails.md`, `playbooks/copywriting/copywriting.md` | `Route:` |
| `marketing: improve my homepage` | no route |  |
| `Our marketing site build fails when I run ./build.sh. Fix it.` | no route |  |
| `marketing: add FAQ schema to index.html` | `playbooks/schema/schema.md` | `Route: schema` |
| `marketing: write a marketing plan for my client, Acme Notes` | `playbooks/marketing-plan/marketing-plan.md` | `Route: marketing-plan` |
| `Peux-tu m'aider avec le marketing de mon app ? Je manque d'idées pour la faire connaître.` | `playbooks/marketing-ideas/marketing-ideas.md` | `Route: marketing-ideas` |
| `$corey-mode rewrite the hero section of index.html` | `playbooks/copywriting/copywriting.md` | `Route: copywriting` |
| `marketing ; Copy Editing: tighten the FAQ answers in index.html` | `playbooks/copy-editing/copy-editing.md` | `Route: copy-editing` |
| `$matt-mode grill me: should Acme Notes do its marketing through a podcast?` | manual |  |
| `marketing: set up social listening for Acme Notes` | `playbooks/social/social.md` | `Route: social` |

Judge three things by hand, from a full run: row 4 opens with a route line naming all three routes, row 6 fixes `build.sh` and opens with `Route: none` when the mode loads, and row 12 runs matt-mode's interview with no route line, reading at most `SKILL.md` and one playbook as a reference.

A playbook may load the routes it calls for after the expected ones, as `copywriting` loads `copy-editing` and `marketing-plan` loads `product-marketing`.

In the recorded Codex replays, the `workspace-write` sandbox blocked writes to `.agents/`. Playbooks saved `.agents/product-marketing.md` and `.agents/listening-sources.md` elsewhere and reported the new paths. When replay permissions require another path, judge the case by the files read and the answer.
