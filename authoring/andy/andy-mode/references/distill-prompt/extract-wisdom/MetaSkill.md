---
name: extract-wisdom
description: Content-adaptive wisdom extraction that builds dynamic sections from what the content actually contains, not static templates. USE WHEN the user wants an insight report from a video, podcast, interview, article, or long-form transcript and says "extract wisdom", "what's interesting", "key takeaways", "what did I miss", or "analyze this".
---

# extract-wisdom

> Dynamic, content-adaptive wisdom extraction. Sections are built around the actual wisdom domains in the content (not fixed IDEAS/QUOTES/HABITS headers), and tone stays conversational.

## When to Use

Pick this prompt when the user wants:

- An insight report from a video, podcast, interview, article, or talk
- Sections that adapt to the content (e.g. "Money Philosophy", "Threat Model Insights") instead of generic categories
- The spiciest, most tweetable moments captured, not a documentation-style summary
- Optional depth control: instant / fast / basic / full / comprehensive

Do **not** use this when the user wants comprehensive follow-along notes (use `follow-along-note`), a skim-level TL;DR (use `short-summary`), or a quote-first outline (use `summary-with-quotes`).

## What the Prompt Produces

- H1 title + one-line description
- 1 to 15 dynamic sections named like magazine headlines, with 3-15 bullets each
- Always includes "Quotes That Hit Different" if the source has quotable moments
- Always includes "First-Time Revelations" if the source has genuinely new ideas
- Closing sections vary by depth level:
  - **Full** (default): One-Sentence Takeaway + If You Only Have 2 Minutes + References & Rabbit Holes
  - **Comprehensive**: all of the above + Themes & Connections
  - **Basic**: One-Sentence Takeaway only
  - **Fast / Instant**: no closing sections

Output is plain markdown, never wrapped in a code block.

## Depth Levels

Pass a depth keyword in the request. Default is **Full** if none specified.

| Keyword | Depth | Sections | Bullets per Section |
|---|---|---|---|
| `instant`, `one section` | Instant | 1 | 8 |
| `fast`, `quick`, `skim` | Fast | 3 | 3 |
| `basic`, `overview` | Basic | 3 | 5 |
| (default) | Full | 5-12 | 3-15 |
| `comprehensive`, `deep`, `everything` | Comprehensive | 10-15 | 8-15 |

## Input Assumptions

- Any long-form content: YouTube transcript, article, interview, podcast, essay, talk, pasted text
- Source may be imperfect; the prompt keeps conversational tone rules and flags weak sections rather than padding them

## Prompt File

`prompt.md` contains the full prompt text, ready to be selected through `distill --prompt extract_wisdom`.
