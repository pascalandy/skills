---
description: "Draw a Mermaid diagram whose source must also render on GitHub or Obsidian, and show it in an HTML page."
---

# Mermaid

1. Load `mermaid` and follow its workflow, with its render command. Finish when `mmdc` renders the source and the image shows the takeaway.
2. Put the SVG inline in the page. When the page holds more than one Mermaid SVG, render each with its own `--svgId`, so their styles do not clash. Finish when the diagram colors match the page tokens at both widths.
3. Run shared verification. Finish when labels, arrows, and contrast pass at both widths.

Return the diagram type, its Mermaid source, and the Mermaid version you rendered with.
