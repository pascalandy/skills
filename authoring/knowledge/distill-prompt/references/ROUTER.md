---
name: distill-prompt-router
description: Routes requests to the right distill prompt sub-skill based on the kind of output the user wants. USE WHEN follow along, follow-along note, detailed notes, comprehensive notes, learning notes, full notes, study notes, companion notes, short summary, tl;dr, quick overview, high-level summary, skim, 30 second summary, is this worth reading, is this worth watching, summary with quotes, include quotes, quote-based outline, verbatim quotes, timestamped sections, best quotes, extract wisdom, analyze video, analyze podcast, extract insights, what's interesting, key takeaways, what did I miss, content analysis, insight report, list prompts, what prompts exist, which distill prompts, available styles.
---

# distill-prompt Router

## Routing Table

| Request Pattern | Route To |
|---|---|
| follow along, follow-along note, detailed notes, comprehensive notes, learning notes, full notes, study notes, companion notes | `follow-along-note/MetaSkill.md` |
| short summary, tl;dr, quick overview, high-level summary, skim, 30 second summary, is this worth reading, is this worth watching | `short-summary/MetaSkill.md` |
| summary with quotes, include quotes, quote-based outline, verbatim quotes, timestamped sections, best quotes | `summary-with-quotes/MetaSkill.md` |
| extract wisdom, analyze video, analyze podcast, extract insights, what's interesting, key takeaways, what did I miss, content analysis, insight report | `extract-wisdom/MetaSkill.md` |
| list prompts, what prompts exist, which distill prompts, available styles | List all sub-folders under `references/` |

## Default

If no pattern matches clearly, default to `follow-along-note/MetaSkill.md`. It is the most general-purpose and preserves the most detail.

## Consumer Note

This router tells an agent which prompt to pick. The `distill` tool does not read this router itself -- it receives a prompt file path chosen by the agent.
