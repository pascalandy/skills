---
name: short-summary
description: Concise 2-3 sentence overview with 5-7 key bullet points and target-audience line. USE WHEN the user wants a TL;DR, a quick overview to decide if content is worth a full read or watch, or a high-level skim capped around 200 words.
---

# short-summary

> Quick high-level summary. Answers "what is this about and should I spend more time on it?"

## When to Use

Pick this prompt when the user wants:

- A TL;DR or quick overview
- To decide if content is worth reading or watching in full
- A 30-second skim that hits the main topics
- A summary capped around 200 words

Do **not** use this when the user wants detailed notes or quote-based analysis -- use `follow-along-note` or `summary-with-quotes`.

## What the Prompt Produces

- H2 title
- Overview paragraph (2-3 sentences)
- 5-7 bullet points of main topics
- "Who should watch / read" line identifying the target audience
- Links section (Obsidian double-bracket notation, always includes `[[AI Summary]]`)
- Under 200 words total

Output is plain markdown, never wrapped in a code block.

## Input Assumptions

- Any long-form content (transcript, article, video, podcast, talk)
- Works equally well on short and long sources

## Prompt File

`prompt.md` contains the full prompt text, ready to be selected through `distill --prompt short_summary`.
