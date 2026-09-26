---
name: follow-along-note
description: Detailed follow-along notes that preserve the structure, nuance, and teaching style of the source material. USE WHEN extracting comprehensive notes from transcripts, articles, lessons, talks, podcasts, essays, or any long-form content where faithful depth matters more than brevity.
---

# follow-along-note

> Comprehensive companion notes that preserve the original flow, depth, and examples of the source -- not a condensed summary.

## When to Use

Pick this prompt when the user wants:

- Detailed notes to revisit instead of the original content
- Teaching-quality notes that capture both ideas and supporting material
- The nuance, examples, quotes, and transitions preserved
- A faithful follow-along companion, not a TL;DR

Do **not** use this when the user explicitly wants a short summary or a decision-making skim -- use `short-summary` instead.

## What the Prompt Produces

- H2 title, H3 sections
- Overview paragraph
- "Main Idea" + "Supporting Material" pairs per section
- Memorable quotes as blockquotes
- Actionable advice and key terms extracted
- Final sections: Key Takeaways, Key Terms Introduced, Links (for Obsidian), Meta

Output is plain markdown, never wrapped in a code block.

## Input Assumptions

- Any long-form prose (transcript, article, lesson, essay, podcast transcription, documentation, talk)
- Source may be imperfect; the prompt includes rules for flagging unclear passages

## Prompt File

`prompt.md` contains the full prompt text, ready to be selected through `distill --prompt follow_along_note`.
