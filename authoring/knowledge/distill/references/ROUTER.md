---
name: distill-router
description: Routes distill requests to the right input sub-skill based on what the user is feeding in. USE WHEN distill a local file, summarize this file, notes from article.md, process a markdown file, read this text file, distill this URL, summarize a web page, fetch and distill, distill this video, summarize a YouTube URL, podcast audio.
---

# distill Router

## Routing Table

| Request Pattern | Route To |
|---|---|
| distill `<local-text-file>`, summarize this text file, notes from article.md, process a markdown file | `from-file/MetaSkill.md` |
| distill this URL, summarize a web page, fetch and distill | **Out of scope in v1.** Deferred to a future `from-url/MetaSkill.md`. |
| summarize a YouTube URL or Zoom recording | **Out of scope.** Use `$transcript`. `from-media/MetaSkill.md` is future work. |
| distill a video file or podcast audio | **Out of scope.** `transcript` accepts YouTube and Zoom inputs only. |

## Default

If the input is a path to a local text file, route to `from-file/MetaSkill.md`.

## Why a Router for One Sub-Skill?

`distill` is intentionally a meta-skill even though v1 ships with a single input path (`from-file`). Future expansion (`from-url`, `from-media`) will add rows here without requiring callers to change how they invoke it.
