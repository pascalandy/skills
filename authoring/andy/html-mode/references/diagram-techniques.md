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
| How much or how often? | Quantitative chart; read [charts and data](charts-and-data.md) |

Use coordinated views when one picture would overload several questions. Choose HTML/CSS for reflowing labels and aligned regions, SVG for crisp relationships and annotations, Canvas for dense or frequently changing graphics, and WebGL only when spatial scale or three-dimensional content earns it. Semantic HTML controls can surround any drawing medium.

## Legibility

Establish hierarchy through position, grouping, containment, scale, and whitespace. Keep labels readable at the default view. Route connectors around nodes and labels, with unmistakable direction and distinct edge meanings. Boundaries express actual ownership, trust, deployment, or responsibility.

Use the audience's concepts. Implementation names belong when the question concerns code structure. Preserve an overview while revealing detail. Provide accessible text alternatives for drawn content and legends only for notation that needs explanation.

## Interaction

Keep node positions stable when readers compare states. A sequence exposes causality with durable labels and a visible current step. For a controlled sequence, provide play, pause, restart, stepping, or path choice as appropriate; the system remains understandable while stopped. Reduced motion uses immediate or step-based changes.

Selection must be visible. Detail panels are dismissible and reopen from their associated control; check that they do not cover critical content. Important details remain reachable by keyboard.

## Pan and zoom

Use pan and zoom only when the information space materially exceeds the viewport. For SVG, transform one containing group and keep coordinate math consistent. Preserve the point under the cursor when zooming, suppress click activation after dragging, and provide drag feedback, a visible zoom level, useful scale limits, and reset.

Verify default fit, zoom limits, reset, drag-versus-click behavior, and keyboard alternatives. At narrow widths, use an intentional contained region or alternate view rather than shrinking labels into illegibility.
