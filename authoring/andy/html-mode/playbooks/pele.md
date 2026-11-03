---
description: "Draw a diagram in Mermaid syntax with pele and show it in an HTML page."
---

# Pele

1. Load `pele` and follow its "Draw a diagram" steps. Finish when its render script answers `{"ok":true,...}` and the screenshot shows the takeaway.
2. Render the final SVG with `--no-theme` and put it inline in the page. Set pele's CSS variables from the page tokens; pele's theming page lists them. Finish when the diagram uses the page colors at both widths.
3. Run shared verification. Finish when labels, arrowheads, and contrast pass at both widths.

Return the diagram type, its Mermaid source, the pele version, and what the diagram cannot establish.
