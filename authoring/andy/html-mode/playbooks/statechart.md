---
description: "Draw a statechart that TLC checks, and show it in an HTML page with the rules that break."
---

# Statechart

1. Load `statechart` and follow it until you have `chart.mmd` and its report. Finish when the report lists each rule as holding, breaking, or not checked.
2. Render `chart.mmd` with `pele` and `--no-theme`, put the SVG inline in the page, and set pele's CSS variables from the page tokens. Next to the chart, show each rule that breaks, the reader's sentence for it, and its path. Finish when each breaking state in the chart matches a rule shown beside it.
3. Run shared verification. Finish when states, arrows, and marks stay legible at both widths.

Return the chart, its Mermaid source, the steps the chart hides, what the model leaves out, and the command that makes the files again.
