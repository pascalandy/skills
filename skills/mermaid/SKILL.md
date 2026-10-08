---
name: "mermaid"
description: "Use when choosing, creating, editing, or validating Mermaid diagrams to explain concepts, systems, processes, or data."
kind: "general"
---

# Mermaid

Choose the representation by the question it answers. A flowchart is one option, not the default for every concept.

Resolve bundled paths relative to this skill directory. Load only the reference needed for the current question.

## Workflow

1. State the reader's question and the takeaway in one sentence each. Identify whether the input is measured data, an estimate, or a hypothetical example
2. Choose the diagram using the table below. For an exploratory request, compare two or three views that reveal different facts about the same subject. For a routine request, use one view
3. Read the matching reference. Check the target renderer and supported Mermaid version before using recent syntax. If the destination is unknown, deliver a rendered SVG or PNG alongside the source and state the tested version
4. Model the meaning before styling. Define units, direction, relationship semantics, and any scoring scale. Do not invent observations or turn a hypothesis into a proven cause
5. Render every new or changed example, inspect its image, and check its intended conclusion against the input. Fix clipped labels, ambiguous arrows, unreadable contrast, and misleading scales
6. Deliver the visible diagram, its editable Mermaid source, one sentence explaining how to read it, and the validation evidence. A source block alone is insufficient when the user asks to see examples

## Choose by question

| Reader's question | Representation | Read when selected |
|---|---|---|
| What happens next, or under which condition? | Flowchart | [Flowcharts](references/flowcharts.md) |
| Who exchanges what, and in what order? | Sequence | [Sequences](references/sequence-diagrams.md) |
| Who owns each business step? | Sequence for handoffs; native swimlane when supported | [Business processes](references/business-processes.md) |
| What entities and relationships exist? | Class or ERD | [Classes](references/class-diagrams.md), [ERD](references/erd-diagrams.md) |
| At what architectural level are we speaking? | C4 | [C4](references/c4-diagrams.md) |
| How are infrastructure services connected? | Architecture | [Architecture](references/architecture-diagrams.md) |
| Where does the budget, time, or volume actually go? | Sankey | [Data perspectives](references/data-perspectives.md) |
| What deserves attention given two explicit criteria? | Quadrant | [Data perspectives](references/data-perspectives.md) |
| Which tradeoffs disappear inside an average score? | Radar | [Data perspectives](references/data-perspectives.md) |
| Where is a total concentrated within a hierarchy? | Treemap | [Data perspectives](references/data-perspectives.md) |
| Which states can coexist without a combinatorial list? | Composite state with concurrent regions | [Concept perspectives](references/concept-perspectives.md) |
| What overlaps, fails, or interrupts an interaction? | Sequence with par, critical, break | [Concept perspectives](references/concept-perspectives.md) |
| Which requirement has implementation and verification links? | Requirement | [Concept perspectives](references/concept-perspectives.md) |
| What feedback could amplify or dampen a problem? | Flowchart with signed causal links | [Concept perspectives](references/concept-perspectives.md) |
| What should we build, buy, or let evolve? | Wardley | [Emerging perspectives](references/emerging-perspectives.md) |
| Should we apply a procedure, analyze, experiment, or stabilize? | Cynefin | [Emerging perspectives](references/emerging-perspectives.md) |
| What separates a command, a recorded fact, and a read model? | Event modeling | [Emerging perspectives](references/emerging-perspectives.md) |
| How do we configure layout, contrast, accessibility, or links? | Renderer configuration | [Advanced features](references/advanced-features.md) |

Other useful choices: Gantt for dependencies and dates, XY for changes on numeric axes, journey for perceived experience, mindmap for a conceptual hierarchy, gitGraph for branch history. Consult [official syntax documentation](https://mermaid.js.org/intro/) when these fit. Mermaid does not compute a critical path, causal inference, statistical uncertainty, or a simulation merely by drawing a diagram. Use a plotting tool when those analyses or precise quantitative comparisons are the task.

## Reading beyond the obvious

For requests seeking discovery or unusual examples, read the three perspectives references. Select examples for the insight they reveal, not their novelty alone.

Useful paired views of one subject:

- Sankey of a team's time plus a feedback loop of interruptions: allocation and a hypothesis explaining it
- Wardley plus a quadrant: evolution of dependencies and prioritization of actions, with distinct axes
- Event model plus concurrent states: recorded facts and combinations of state that must remain valid
- Radar plus raw values: tradeoff shape and exact comparison, avoiding a misleading overall score

Show the conclusion beneath the diagram. Label illustrative data as fictional. Explain what the diagram cannot establish.

## Syntax and meaning

- Quote flowchart labels containing spaces or punctuation: `api["API (public)"]`. Other diagram grammars have their own quoting rules
- Keep stable, short IDs separate from display labels
- In sequences, dashed lines are commonly used for returns; arrow appearance alone does not enforce synchronous behavior. Balance activation and deactivation across the whole source, including alternatives
- In ERDs, solid `--` means identifying and dotted `..` means non-identifying. Supported key markers are `PK`, `FK`, `UK`; combine them with commas
- In flowcharts, an external link to a subgraph's internal node can cause its local direction to be ignored
- Use text as well as color for distinctions. Avoid emojis unless they belong to an explicit notation with a tested renderer
- Do not animate edges by default

## Color baseline

Use a black canvas and white primary text. Retain Catppuccin Frappe accents; use dark text inside light filled nodes. There is no required external palette skill.

| Role | Hex |
|---|---|
| Canvas / text | `#000000` / `#ffffff` |
| Dark node fill | `#303446` |
| Primary blue | `#8caaee` |
| Success green | `#a6d189` |
| Error red | `#e78284` |
| Warning yellow | `#e5c890` |
| Info teal | `#81c8be` |
| Accent peach / mauve | `#ef9f76` / `#ca9ee6` |

Use [assets/theme.json](assets/theme.json) as the reusable black-canvas export configuration. Start with `theme: base` for custom theme variables. Diagram families may need additional variables; verify the actual export. The `background` theme variable alone does not guarantee the output canvas color; use the renderer's background option too. See [advanced features](references/advanced-features.md).

## Render and verify

Prefer a project's pinned Mermaid CLI. On Mac, install or update the global CLI with `PNPM_HOME="$HOME/Library/pnpm" "$HOME/Library/pnpm/bin/pnpm" add -g --config.minimum-release-age=10080 --config.strict-dep-builds=true --allow-build=puppeteer @mermaid-js/mermaid-cli`.

Use the installed CLI:

```bash
mmdc --help
mmdc -i diagram.mmd -o /tmp/diagram.svg -b '#000000'
```

On Linux, use `pnpm dlx --allow-build=puppeteer @mermaid-js/mermaid-cli` when no CLI is installed. Check `pnpm dlx --help` for build-permission support before running it.

An existing Chrome can be selected with `PUPPETEER_EXECUTABLE_PATH`; `PUPPETEER_SKIP_DOWNLOAD=true` skips downloading another browser. Do not change project dependencies merely to render a diagram.

For a reference containing multiple examples, use [scripts/render_examples.py](scripts/render_examples.py). Run its `--help` for extraction, output, and gallery options. It uses the bundled theme by default and keeps individual sources. It answers in one JSON line: `files` lists each SVG to inspect, and an example that fails to render fails the run, named by file and line under `errors`, so one broken example cannot hide behind the others.

```bash
# Run from this skill directory, with mmdc available on PATH
uv run scripts/render_examples.py references/*perspectives.md --output /tmp/mermaid-gallery --gallery
```

Record the CLI version and resolved Mermaid engine version separately when available. Successful CLI rendering proves compatibility with that engine, not with GitHub, Obsidian, or another host's bundled version. Check the actual host when required; export SVG/PNG as the fallback. If rendering is unavailable, identify the unverified examples explicitly.

Inspect the image as well as the exit code. Check labels, arrowheads, legend, totals, units, and whether the intended takeaway is visible. Add `accTitle` and `accDescr` where the selected grammar supports them; retain a prose equivalent alongside the image.
