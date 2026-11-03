---
description: "Choose the diagram that best shows how components, events, states, or concepts relate, then draw it in an HTML page."
---

# Diagram

1. Name the reader's question and the takeaway. Pick the tool in the table below. Finish when one tool fits the question.

   | The diagram needs | Follow |
   | --- | --- |
   | A static diagram in Mermaid syntax, the default | `playbooks/pele.md` |
   | Mermaid source that GitHub or Obsidian also renders | `playbooks/mermaid.md` |
   | Lanes as straight vertical columns | `playbooks/graphviz.md` |
   | Proof that state rules hold, with the paths that break them | `playbooks/statechart.md` |
   | Clickable nodes, a custom visual metaphor, or pan and zoom | [Hand-drawn](#hand-drawn) |

2. When the request explores, render two or three options on one page. Each option reveals a different fact about the subject, with one line on what it shows. Wait for the user's choice. Otherwise, keep the best option. Finish when one option is chosen.
3. Follow the chosen option's route. Finish when that route's handoff is ready.

## Hand-drawn

1. For notation and rendering, read `references/diagram-techniques.md`. Decide what stays visible together and what appears on demand. Finish when one visual grammar explains the main relationship.
2. Build the smallest model that preserves meaning. Add sequencing, filtering, path tracing, or pan and zoom only for a real follow-up question. Keep labels, relationships, and notation primary. Finish when the default view explains the system without interaction.
3. Run shared verification and applicable technique checks. Inspect label collisions, clipped nodes, connector routing, sequence endpoints, keyboard access, and every interactive state. Finish when relationships are legible at both widths and each simplification is stated.

Return the diagram form, main simplifications, and assumptions.
