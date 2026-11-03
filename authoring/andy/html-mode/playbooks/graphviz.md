---
description: "Draw a Graphviz lane diagram and show it in an HTML page."
---

# Graphviz

1. Load `graphviz` and follow it until its PNG passes the skill's Check. Finish when each lane is straight, no edge crosses a label, and branches keep the source order.
2. Set `bgcolor=transparent` on the graph, render with `dot -Tsvg`, and put the SVG inline in the page. Color the `.node` and `.edge` shapes and text with CSS from the page tokens. Finish when the diagram uses the page colors at both widths.
3. Run shared verification. Finish when labels and lanes stay legible at both widths.

Return the `dot` source and the result of the skill's Check.
