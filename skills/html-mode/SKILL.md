---
name: "html-mode"
description: "Use when the user requests a standalone HTML artifact or HTML presentation, including shorthand such as 'plan; html'. Do not use for ordinary application code changes."
kind: "general"
---

# HTML mode

Create or revise one self-contained HTML artifact. Use the playbook that owns the reader's main question. Ordinary application implementation and non-HTML presentation formats stay with their own workflows.

Resolve bundled paths relative to this skill directory. Playbooks and references are plain files, not separately installed skills. Read only the files whose conditions apply.

## Workflow

1. Read the brief, source material, and project instructions. Record the audience, review question, content to preserve, fidelity, and useful interaction, and set the [level](#levels). Follow explicit user decisions, then project conventions, then the subject and audience. Decide technical choices, such as a script's language and tooling, from `coding-language` without asking the user; Python runs through `uv`. This step is complete when the artifact's purpose, boundaries, and level are concrete.
2. Select and read one primary playbook from the table below. For mixed artifacts, add only the references or playbook sections needed for embedded content. This step is complete when the primary review question has one owner.
3. Set the visual direction. When palette, type, composition, or register remain open, read [design](references/design.md). Follow the active theme and motion policy. Before implementation, resolve whether the result is local-only or authorized for publication. An explicit local-only request wins. For any authorized publication, read `html-publish` from the active skill catalog; it is the sole owner of hosted delivery and durable receipts. `html-mode` owns artifact design and browser verification for this run. This step is complete when the design, interactions, and delivery choice are concrete.
4. Build under the shared contract and selected playbook. Preserve any project-required variant review before changing real product components. This step is complete when the file exists and every intended section, control, and state is accounted for.
5. Verify the file using the shared checks and playbook-specific criteria. For a page readers use, run `uv run scripts/check_page.py <page>` from this skill's directory first; `--help` lists screens and browser setup. Fix observed failures. This step is complete when checks pass or unavailable checks are named in the handoff.
6. Return the absolute file path and playbook-specific handoff. Report browser rendering, external network dependencies, host and client delivery, private URL, and receipt persistence as separate facts. Private hosting does not make an artifact offline or hide its external dependencies. For local-only work, do not invoke a host or change a receipt. For authorized publication, use `html-publish` and report a private URL only when a verified result carries one. If publication cannot complete, keep the local artifact and retained receipt attempt, then report the exact retry from `html-publish` without creating another publication identity.

## Playbooks

| Main review question | Read |
| --- | --- |
| What content belongs here, and how should navigation or layout work? | [Wireframe](playbooks/wireframe.md) |
| How should the product look, or how should a bounded flow behave? | [Prototype](playbooks/prototype.md), choosing static mockup or working prototype |
| What work happens in what order, with which commitments? | [Plan](playbooks/plan.md) |
| How do components, events, states, or concepts relate? | [Diagram](playbooks/diagram.md) |
| How should an HTML presentation tell its story one screen at a time? | [Slides](playbooks/slides.md) |
| How do readers move through a page built for them, such as a document turned into a guided reading page? | [Interactive page](playbooks/interactive-page.md) |
| A report, explainer, landing page, tool, data story, or mixed artifact without a narrower owner | [Artifact](playbooks/artifact.md) |

For quantitative content in any playbook, read [charts and data](references/charts-and-data.md).

For a page readers use, consult these when their conditions apply:

- [Quality bar](references/quality-bar.md): what the page meets, and which items `check_page.py` fails
- [Pitfalls](references/pitfalls.md): look up a matching feature or observed defect
- [QA loop](references/qa-loop.md): QA threads, how to split them, the brief, and the journal
- [Learnings](learnings/README.md): read when recording a new lesson or tracing a rule's origin

## Levels

| Level | When | QA rounds |
| --- | --- | --- |
| Esquisse | By default, to see an idea on the web | 2 to 3 |
| Livrable | Only when the user asks for a client deliverable | The number the user gives; ask for it when missing |

## Grow this skill

At the end of a Livrable, add a learning and move each lesson into a reference, a check, or a playbook step. This repository is public: describe the use case, never the client, its product, a private URL, or its text.

## Shared build contract

- Deliver one `.html` file with essential CSS and JavaScript inline, usable directly without a build step, authentication, or live API
- Keep required assets local to the file through inline content or data URLs. External dependencies require user permission except for the exact-version reveal.js CDN files authorized by the slides playbook
- Use source content and representative domain labels; distinguish illustrative data and assumptions from facts
- Use semantic HTML, responsive composition, accessible contrast, visible keyboard focus, and meaning that survives without color or motion
- Match behavior to fidelity. Working flows need working controls; static mockups make their review boundary explicit
- Contain wide tables, code, and canvases in their own scroll or pan region, keeping the page body free of accidental horizontal overflow
- Define a small token set for the selected direction. Respect project theme requirements rather than importing an upstream palette or theme toggle
- Use motion only for explanation or feedback, respect reduced motion, and follow any stricter project motion constraints

## Shared verification

Open the actual file with available browser tooling at wide desktop and narrow mobile widths. Inspect reading order, wrapping, contrast, clipping, overlap, overflow, and console errors. Exercise every implemented control and reachable state with pointer and keyboard. Check visible focus and reduced-motion behavior where motion exists.

For custom fonts, confirm they loaded. Inspect computed foreground and background colors on distinct surfaces where inheritance could hide text. Compare the result against the source brief and the selected playbook's completion criteria.

If browser tooling is unavailable, perform source checks and name the remaining visual and interaction checks as unverified. Source inspection does not prove rendering or behavior.

## Attribution

Adapted from Plannotator's effective-html collection and the retired `html-slides` package. Read [attribution](references/attribution.md) for source mapping, revision, adaptations, and applicable licenses.
