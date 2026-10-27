---
name: "html-mode"
description: "Use for standalone HTML artifacts or HTML presentations, including shorthand such as 'plan; html'. Exclude ordinary application code changes."
kind: "general"
---

# HTML mode

Create or revise one self-contained HTML artifact. Choose the playbook for the reader's main question. For application code or non-HTML presentations, use their workflows.

Resolve bundled paths from this directory. Read files only when their conditions apply.

## Workflow

1. Read the brief, source material, and project instructions. Record audience, review question, content to preserve, fidelity, and useful interaction. Set the [level](#levels). Follow user decisions, then project conventions, then subject and audience. Use `coding-language` for technical choices without asking the user. Run Python through `uv`. Finish when purpose, boundaries, and level are clear.
2. Read one primary playbook below. For mixed artifacts, add only references or playbook sections needed for embedded content. Finish when one playbook covers the main review question.
3. Set visual direction. If palette, type, composition, or register is open, read [design](references/design.md). Load `frontend-design`. `html-mode` takes precedence. Follow active theme and motion rules. Before implementation, choose local-only or authorized publication. An explicit local-only request wins. For authorized publication, load `html-publish`. Finish when design, interactions, and delivery are clear.
4. Build under the shared contract and selected playbook. Before changing product components, complete any project-required variant review. Finish when the file contains every intended section, control, and state.
5. Run shared checks and playbook checks. For pages readers use, confirm `uv --version` and, if missing, install `uv` from https://docs.astral.sh/uv/getting-started/installation/ within session permissions. Then, from this directory, run `uv run scripts/check_page.py <absolute page path>`. Dependencies install on first run. `--help` lists screens and browser setup. Fix failures. A mockup that faithfully reproduces third-party colors may retain contrast failures only inside an identified reproduction frame that names its source, palette, and version. Annotate every retained finding from `check_page.py --all` with its location, ratio, and threshold on the page and in the handoff. Fix every finding outside the reproduction and every label needed to choose an option, even inside it. Ordinary reading pages must pass contrast. Finish when checks pass, the handoff names unavailable checks, or the reproduction meets these conditions with the check still red.
6. Return the absolute file path and playbook handoff. Report browser rendering, external network dependencies, host and client delivery, private URL, and receipt persistence separately. Private hosting neither makes the artifact offline nor hides external dependencies. For local-only work, do not invoke a host or change a receipt. For authorized publication, use `html-publish`. Report a private URL only from a verified result. If publication fails, keep the local artifact and receipt attempt. Report the exact retry from `html-publish`. Reuse the publication identity.

## Playbooks

| Main review question | Read |
| --- | --- |
| What content belongs here, and how should navigation or layout work? | [Wireframe](playbooks/wireframe.md) |
| How should a product look or a bounded flow behave? | [Prototype](playbooks/prototype.md), static mockup or working prototype |
| What work happens in what order, with which commitments? | [Plan](playbooks/plan.md). Read [document guidance](references/documents-and-presentations.md) with the source plan |
| How do components, events, states, or concepts relate? | [Diagram](playbooks/diagram.md). Read [diagram techniques](references/diagram-techniques.md) for notation and rendering |
| How should an HTML presentation tell a story one screen at a time? | [Slides](playbooks/slides.md) |
| How do readers use a page, such as a document turned into a guided reading page? | [Interactive page](playbooks/interactive-page.md) |
| A report, explainer, landing page, tool, data story, or mixed artifact without a narrower playbook | [Artifact](playbooks/artifact.md). For reports, briefs, explainers, and comparisons, read [documents and presentations](references/documents-and-presentations.md). For calculators, editors, and tools, read [interfaces](references/interfaces.md). For relational diagrams, read [diagram techniques](references/diagram-techniques.md) |

For quantitative content, read [charts and data](references/charts-and-data.md).

For pages readers use, read these when applicable:

- [Quality bar](references/quality-bar.md): when building or reviewing
- [Pitfalls](references/pitfalls.md): for a matching feature or defect
- [QA loop](references/qa-loop.md): for QA rounds
- [Learnings](learnings/README.md): when recording lessons or tracing a rule's origin

## Levels

| Level | When | QA rounds |
| --- | --- | --- |
| Esquisse | By default, to see an idea on the web | 2 to 3 |
| Livrable | Only when the user asks for a client deliverable | The number the user gives; ask for it when missing |

## Grow this skill

At the end of a Livrable, record lessons per [learnings](learnings/README.md).

## Shared build contract

- Deliver one `.html` file with essential CSS and JavaScript inline, usable without a build step, authentication, or live API
- Embed required assets inline or as data URLs. External dependencies require user permission except for exact-version reveal.js CDN files authorized by the slides playbook
- Use source content and representative domain labels. Separate illustrative data and assumptions from facts
- Use semantic HTML, responsive composition, accessible contrast under [Workflow step 5's third-party rule](#workflow), visible keyboard focus, and meaning that survives without color or motion
- Match behavior to fidelity. Working flows need working controls. State static mockups' review boundaries
- Contain wide tables, code, and canvases in separate scroll or pan regions. Prevent accidental horizontal overflow in the page body
- Define a small token set for the direction. Use project theme requirements over an upstream palette or theme toggle
- Use motion only for explanation or feedback. Respect reduced motion and stricter project motion rules

## Shared verification

Open the file in a browser at wide desktop and narrow mobile widths. Inspect reading order, wrapping, contrast, clipping, overlap, overflow, and console errors. Test every implemented control and reachable state with pointer and keyboard. Check visible focus and, where motion exists, reduced-motion behavior.

Confirm custom fonts loaded. Where inheritance could hide text, inspect computed foreground and background colors on distinct surfaces. Compare against the brief and playbook completion criteria.

If browser tooling is unavailable, check the source and report visual and interaction checks as unverified.

## Attribution

For sources, revisions, adaptations, and licenses, read [attribution](references/attribution.md).
