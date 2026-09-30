# Routing cases

Maintainer reference. Ordinary use does not load this file.

Replay these cases after a change to the description, a route, its "Use when", or the routing rules in `SKILL.md`, and after an upstream refresh adds or removes a playbook.

Run each request in a fresh headless session. Use a throwaway Git project with corey-mode installed as a project skill beside the usual skill catalog. The project holds a README that describes a product called Acme Notes, a landing page `index.html` with an FAQ section, and a `build.sh` that fails because it copies `index.htm`. A case passes when the session's `command_execution` events read the expected files in order and the final answer opens as expected.

| Request | Reads | Answer |
|---|---|---|
| `marketing: my landing page in index.html isn't converting. What should I change?` | `SKILL.md`, then `cro` | Opens with `Route: cro` |
| `My landing page in index.html isn't converting. What should I change?` | Nothing from corey-mode | Answers without the mode |
| `marketing ; copywriting for the hero section of index.html` | `SKILL.md`, then `copywriting` | Opens with `Route: copywriting` |
| `marketing: we launch Acme Notes next month. Plan the launch, then write the welcome email sequence and the landing page copy.` | `SKILL.md`, then `launch`, `emails`, and `copywriting` | Opens with a route line naming all three |
| `marketing: improve my homepage` | `SKILL.md` only | Asks whether `cro` or `copywriting` fits. Runs nothing |
| `Our marketing site build fails when I run ./build.sh. Fix it.` | At most `SKILL.md` | Opens with `Route: none` when the mode loaded. Fixes `build.sh` |
| `marketing: add FAQ schema to index.html` | `SKILL.md`, then `schema` | Opens with `Route: schema`. `index.html` gains `FAQPage` JSON-LD |
| `marketing: write a marketing plan for my client, Acme Notes` | `SKILL.md`, then `marketing-plan` | Opens with `Route: marketing-plan` |
| `Peux-tu m'aider avec le marketing de mon app ? Je manque d'idées pour la faire connaître.` | `SKILL.md`, then `marketing-ideas` | Opens with `Route: marketing-ideas` |
| `$corey-mode rewrite the hero section of index.html` | `SKILL.md`, then `copywriting` | Opens with `Route: copywriting` |
| `marketing ; Copy Editing: tighten the FAQ answers in index.html` | `SKILL.md`, then `copy-editing` | Opens with `Route: copy-editing` |
| `$matt-mode grill me: should Acme Notes do its marketing through a podcast?` | At most `SKILL.md` and one playbook as a reference | Matt-mode's interview, with no route line |
| `marketing: set up social listening for Acme Notes` | `SKILL.md`, then `social` | Opens with `Route: social`. The source list starts from `playbooks/social/references/listening-sources-template.md` |

A playbook may load the routes it calls for after the expected ones, as `copywriting` loads `copy-editing` and `marketing-plan` loads `product-marketing`.

In the recorded Codex replays, the `workspace-write` sandbox blocked writes to `.agents/`. Playbooks saved `.agents/product-marketing.md` and `.agents/listening-sources.md` elsewhere and reported the new paths. When replay permissions require another path, judge the case by the files read and the answer.
