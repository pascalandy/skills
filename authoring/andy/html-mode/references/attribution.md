# Attribution

`html-mode` adapts the [effective-html](https://github.com/plannotator/effective-html) skills by [Plannotator](https://github.com/plannotator).

Source revision: [`2ac1dfecb0f2474e75260cb6d3c9b9d6d9b5062e`](https://github.com/plannotator/effective-html/tree/2ac1dfecb0f2474e75260cb6d3c9b9d6d9b5062e/skills), inspected on 2026-09-19.

Copyright (c) 2026 plannotator. The original material is distributed under the [MIT license](LICENSE-effective-html.txt), reproduced alongside this attribution.

## Source mapping

Paths in the first column are relative to the pinned upstream `skills/` directory.

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

The [slides playbook](../playbooks/slides.md) supersedes the retired `html-slides` package, whose metadata credited `claude-office-skills` and declared the MIT license. That package recorded no upstream URL or revision. The retained reveal.js concepts were rechecked against the current official documentation instead of carrying over its agent, model, or MCP metadata.

The bundled [slides template](../assets/slides-template.html) loads [reveal.js 6.0.2](https://github.com/hakimel/reveal.js/releases/tag/6.0.2) from jsDelivr. reveal.js is copyright (c) 2011-2026 Hakim El Hattab and contributors and is distributed under the [MIT license](LICENSE-revealjs.txt).

## Adaptations

- Replaced six registered skills with one discoverable entry point and plain playbooks, following the local `poteto-mode` structure
- Consolidated shared build and verification rules and merged overlapping creative-direction guidance
- Resolved conflicting typography guidance in favor of purpose-driven roles without mandatory font or color quotas
- Kept user and project design constraints authoritative, including single-theme and motion policies
- Replaced the upstream `tot` installation and public-sharing procedure with the active authorized delivery workflow; publishing constraints are checked before implementation
- Omitted upstream per-skill agent metadata; automatic skill selection uses the shared description
- Replaced the separate `html-slides` entry point with one reveal.js playbook and template owned by `html-mode`

## Further reading

Plannotator's [HTML wireframes and prototypes for coding agents](https://docs.plannotator.ai/learn/code-context/html-wireframes-and-prototypes-for-coding-agents) is the further-reading link supplied by the upstream wireframe and prototype skills.
