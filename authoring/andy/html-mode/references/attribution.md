# Attribution

`html-mode` adapts the [effective-html](https://github.com/plannotator/effective-html) skills by [Plannotator](https://github.com/plannotator).

Source revision: [`2ac1dfecb0f2474e75260cb6d3c9b9d6d9b5062e`](https://github.com/plannotator/effective-html/tree/2ac1dfecb0f2474e75260cb6d3c9b9d6d9b5062e/skills), inspected on 2026-09-19.

Copyright (c) 2026 plannotator. Original material uses the [MIT license](LICENSE-effective-html.txt), reproduced here.

## Source mapping

Upstream paths are relative to the pinned `skills/` directory.

| Upstream source | Adapted destination |
| --- | --- |
| `html/SKILL.md` | [Shared workflow](../SKILL.md) and [artifact](../playbooks/artifact.md) |
| `html-wireframe/SKILL.md` | [Wireframe](../playbooks/wireframe.md) |
| `html-prototype/SKILL.md` | [Prototype and mockup](../playbooks/prototype.md) |
| `html-plan/SKILL.md` | [Plan](../playbooks/plan.md) |
| `html-diagram/SKILL.md` | [Diagram](../playbooks/diagram.md) |
| `design-artifact/SKILL.md` | [Design](design.md) and shared verification |
| `html/references/creative-direction.md` | [Design](design.md) |
| `html/references/documents-and-presentations.md` | [Documents and presentations](documents-and-presentations.md) |
| `html/references/interfaces.md` | [Interfaces](interfaces.md) |
| `html/references/diagrams.md` | [Diagram techniques](diagram-techniques.md) |
| `html/references/charts-and-data.md` | [Charts and data](charts-and-data.md) |

## Slides

The [slides playbook](../playbooks/slides.md) replaces retired `html-slides`, whose metadata credited `claude-office-skills` and declared the MIT license. That package recorded no upstream URL or revision. Retained reveal.js concepts were rechecked against current official documentation. Agent, model, and MCP metadata were omitted.

The [slides template](../assets/slides-template.html) loads [reveal.js 6.0.2](https://github.com/hakimel/reveal.js/releases/tag/6.0.2) from jsDelivr. reveal.js is copyright (c) 2011-2026 Hakim El Hattab and contributors, under the [MIT license](LICENSE-revealjs.txt).

## Adaptations

- Replaced six registered skills with one entry point and plain playbooks, per local `poteto-mode` structure
- Combined shared build, verification, and overlapping creative-direction rules
- Resolved conflicting typography guidance with purpose-driven roles, without font or color quotas
- Kept user and project design constraints first, including single-theme and motion policies
- Replaced upstream `tot` installation and public sharing with authorized delivery, checking publication constraints before implementation
- Omitted upstream per-skill agent metadata. Automatic selection uses the shared description
- Replaced separate `html-slides` with one reveal.js playbook and template in `html-mode`

## Further reading

Upstream wireframe and prototype skills link to Plannotator's [HTML wireframes and prototypes for coding agents](https://docs.plannotator.ai/learn/code-context/html-wireframes-and-prototypes-for-coding-agents).
