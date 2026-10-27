# Diagram techniques

## Grammar and medium

| Viewer question | Grammar |
| --- | --- |
| What exists and how is it connected? | Topology or system map |
| What happens over time? | Sequence, timeline, or request trace |
| What decisions or transformations occur? | Process |
| How can something change? | State |
| What contains or owns what? | Hierarchy or boundary map |
| How do alternatives compare? | Matrix or aligned comparison |
| How much or how often? | Quantitative chart; read `references/charts-and-data.md` |

If one picture has too many questions, use coordinated views. Use HTML/CSS for reflowing labels and aligned regions. Use SVG for crisp relationships and annotations, Canvas for dense or frequently changing graphics. Use WebGL only when spatial scale or three-dimensional content justifies it. Any drawing medium can have semantic HTML controls.

## Legibility

Show hierarchy through position, grouping, containment, scale, and whitespace. Keep default-view labels readable. Route connectors around nodes and labels. Make direction clear and edge meanings distinct. Use boundaries for actual ownership, trust, deployment, or responsibility.

Use the audience's concepts. Use implementation names for code-structure questions. Keep an overview as detail appears. Provide accessible text alternatives for drawings. Add legends only for notation needing explanation.

## Interaction

When readers compare states, keep node positions stable. Show sequence causality with persistent labels and a visible current step. For controlled sequences, provide play, pause, restart, stepping, or path choice as needed. Keep stopped sequences understandable. For reduced motion, use immediate or step-based changes.

Show selection. Let readers dismiss detail panels and reopen them from their controls. Check that panels do not cover critical content. Keep important details reachable by keyboard.

## Pan and zoom

Use pan and zoom only when content substantially exceeds the viewport. For SVG, transform one containing group with consistent coordinate math. When zooming, preserve the point under the cursor. After dragging, suppress click activation. Provide drag feedback, visible zoom level, useful scale limits, and reset.

Verify default fit, zoom limits, reset, drag-versus-click behavior, and keyboard alternatives. At narrow widths, use a contained region or alternate view. Keep labels legible.
