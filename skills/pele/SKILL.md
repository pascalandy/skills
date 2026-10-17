---
name: "pele"
description: "Use when a request names pele or pele.run, or a project depends on the `pele` npm package: writing, rendering, or theming its diagrams, or calling its API."
kind: "general"
---

# Pele

Pele is a new renderer, not Mermaid. It reads Mermaid syntax and draws the diagram with its own layout, in a browser or in Node, with colors from CSS variables. Mermaid habits apply to syntax only. Before you reuse a Mermaid habit, read [Differences from Mermaid](references/source/compatibility.md#differences-from-mermaid).

Resolve bundled paths relative to this skill directory. `references/source/` holds the pele.run pages at the version that its [README](references/source/README.md) names. When the project uses a newer pele, read the live page at `https://pele.run/<page>.md`, such as `https://pele.run/api.md`.

To draw a diagram, follow [Draw a diagram](#draw-a-diagram). To add pele to an app, go to [Pele in an app](#pele-in-an-app).

## Draw a diagram

1. State the reader's question and the takeaway in one sentence each. Say whether the input is measured data, an estimate, or a made-up example
2. Choose the type in [Choose by question](#choose-by-question). For an exploratory request, compare two or three types that show different facts about the same subject. For other requests, use one type
3. List the headings of the type's examples page with `rg -n '^#' <page>`. Copy the closest example as the start
4. Model the meaning before the style: units, direction, the meaning of each arrow, and any scale. Do not invent observations or turn a hypothesis into a proven cause. When the type accepts them, add the accessibility title and description, `accTitle` and `accDescr`. Done when the diagram alone shows each unit and the meaning of each arrow
5. Run [Render and verify](#render-and-verify) until the script answers `{"ok":true,...}` and the screenshot shows the takeaway
6. Deliver the SVG, its screenshot, the editable source, one sentence on how to read the diagram, and the pele version that the script reported

## Choose by question

| Reader's question | Type and examples |
|---|---|
| What happens next, or under which condition? | [Flowchart](references/source/examples/flowchart.md) |
| Who performs each step of a process? | [Swimlane](references/source/examples/swimlane.md) |
| Who exchanges what, and in what order? | [Sequence](references/source/examples/sequence.md) |
| Which states exist, and what moves between them? | [State](references/source/examples/state.md) |
| What entities exist, and how do they relate? | [ER](references/source/examples/er.md), [Class](references/source/examples/class.md) |
| At what architectural level are we speaking? | [C4](references/source/examples/c4.md) |
| How are services connected? | [Architecture](references/source/examples/architecture.md) |
| How do AI agents pass work to each other? | [Agentflow](references/source/examples/agentflow.md) |
| How do commands, events, and views change a system over time? | [Event modeling](references/source/examples/eventmodeling.md) |
| Which goals does each actor reach with the system? | [Use case](references/source/examples/usecase.md) |
| Which elements satisfy or verify each requirement? | [Requirement](references/source/examples/requirement.md) |
| When does each task happen? | [Gantt](references/source/examples/gantt.md), [Timeline](references/source/examples/timeline.md) |
| What is in progress, by status? | [Kanban](references/source/examples/kanban.md) |
| How satisfying is each step of a task? | [Journey](references/source/examples/journey.md) |
| How did branches diverge and merge? | [Git graph](references/source/examples/git.md) |
| Where does a quantity flow? | [Sankey](references/source/examples/sankey.md) |
| How is a whole divided? | [Pie](references/source/examples/pie.md), [Treemap](references/source/examples/treemap.md) for a hierarchy |
| How does a value change along an axis? | [XY chart](references/source/examples/xychart.md) |
| What deserves attention given two criteria? | [Quadrant](references/source/examples/quadrant.md) |
| Which tradeoffs disappear inside an average score? | [Radar](references/source/examples/radar.md) |
| What do sets share? | [Venn](references/source/examples/venn.md) |
| Which causes contribute to a problem? | [Ishikawa](references/source/examples/ishikawa.md) |
| Should we apply a procedure, analyze, experiment, or stabilize? | [Cynefin](references/source/examples/cynefin.md) |
| What should we build, buy, or let evolve? | [Wardley](references/source/examples/wardley.md) |
| What ideas branch from one topic? | [Mindmap](references/source/examples/mindmap.md) |
| What does a hierarchy of files or folders hold? | [Tree view](references/source/examples/treeview.md) |
| What syntax does a grammar accept? | [Railroad](references/source/examples/railroad.md) |
| Which fields does a packet hold? | [Packet](references/source/examples/packet.md) |
| Where do blocks sit in a grid I arrange? | [Block](references/source/examples/block.md) |

A diagram computes nothing: no critical path, causal inference, or statistics. When the task is an exact quantitative comparison, use a plotting tool.

## Syntax and meaning

- Keep short, stable IDs apart from display labels. Quote each label that holds punctuation: `api["API (public)"]`
- Use text as well as color for each distinction
- Label made-up data as made-up. Below the diagram, say what the diagram cannot establish

## Render and verify

Requires `uv` (`uv --version`), Node.js 20 or later (`node --version`), and pnpm (`pnpm --version`). To use the project's pele, run [scripts/render_diagrams.py](scripts/render_diagrams.py) from the project's folder. When the script finds no pele, its error gives the install command.

```bash
# Check only, without files
uv run <this-skill-folder>/scripts/render_diagrams.py diagram.mmd
# Also write one SVG per diagram
uv run <this-skill-folder>/scripts/render_diagrams.py notes.md --output /tmp/pele
```

For the inputs, the theme option, and the answer fields, run the script with `--help`. Fix each error at the `file:line:column` that the script names. Then run the script again.

To inspect an SVG, take a screenshot of it in a Chromium browser (`chromium --version`), at the `width` and `height` that the answer gives. `rsvg-convert` and ImageMagick ignore pele's CSS variables and draw every shape black.

```bash
chromium --headless --screenshot=/tmp/pele/diagram.png --window-size=<width>,<height> file:///tmp/pele/diagram.svg
```

On macOS, use `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"` in place of `chromium`. Read the screenshot. Check the labels, arrowheads, legend, contrast, and takeaway. An `ok` answer proves that the diagram renders with that pele version, not with Mermaid or another host's renderer.

## Theme

[assets/theme.css](assets/theme.css) sets a black canvas, white text, and Catppuccin Frappe accents as pele variables. The script embeds this theme in each SVG. The embedded theme applies to every pele diagram on an HTML page. Before you put an SVG inline in a page, render it with `--no-theme`. In an app, add the theme to the page's CSS. [Theming](references/source/theming.md) lists every variable and class name.

## Pele in an app

- **Rendering, mounting, errors, and bundle size**: read [API](references/source/api.md)
- **Diagrams from untrusted authors**: before you insert their SVG or an error message, read [Security](references/source/security.md)
- **Fonts**: pele measures labels before it draws them. Pass the page's font as [Fonts](references/source/theming.md#fonts) describes
- **Pele compared with Mermaid.js**: read the [home page](references/source/index.md) for the bundle size and the render time
