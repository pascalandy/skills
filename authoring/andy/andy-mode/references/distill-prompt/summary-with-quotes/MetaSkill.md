---
name: summary-with-quotes
description: Structured outline with section summaries and verbatim illustrative quotes from the source. USE WHEN the user wants a quote-centric breakdown, a sectioned outline that surfaces the best lines, or an Obsidian-ready note that highlights speaker voice.
---

# summary-with-quotes

> Sectioned outline that pairs each topic with the two or three best verbatim quotes from the source.

## When to Use

Pick this prompt when the user wants:

- A structured outline with the best quotes preserved verbatim
- Section summaries alongside illustrative blockquotes
- Timestamped sections (where timestamps are available in the source)
- Obsidian-ready notes that keep the speaker's voice front-and-center

Do **not** use this when the user just wants a quick TL;DR -- use `short-summary`. Do **not** use it when the user wants exhaustive follow-along teaching notes -- use `follow-along-note`.

## What the Prompt Produces

- H2 title
- H3 sections with titles and timestamps (where available)
- One or two paragraphs summarizing each section
- Two or three verbatim blockquotes per section
- Links section (Obsidian double-bracket notation, always includes `[[AI Summary]]`)
- Meta section with duration, main topic, insight count

Output is plain markdown, never wrapped in a code block.

## Input Assumptions

- Long-form content with distinct topic shifts (talks, interviews, podcasts, essays)
- Timestamps in the source are optional -- omitted when absent

## Prompt File

`prompt.md` contains the full prompt text, ready to be selected through `distill --prompt summary_with_quotes`.
