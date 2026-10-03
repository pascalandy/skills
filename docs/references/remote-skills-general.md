---
name: remote-skills-general
description: Use andy's general skills remotely
---

<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->

URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md

A mode's routes run through that mode's SKILL.md.

## Modes

- `andy-mode`: Use only when explicitly invoked as `andy-mode`, followed by `;` and a route name, where `andy` may be any voice-to-text spelling that sounds like it, such as `nd`, `indie`, or `endymode`.
  - cass
  - distill
  - distill-prompt
  - docs
  - docs-cleaner
  - glossary
  - idea
  - illustration
  - meta-skill-creator
  - ontology
  - qa
  - qmd
  - retro-global
  - retro-skill-usage
  - simple-editor
  - sparring
  - storytelling
  - think
  - trello
  - wiki-map
  - write-with-clarity
- `corey-mode`: Use only when a request contains the word marketing, or invokes corey-mode, to run Corey Haines' marketing playbooks.
  - ab-testing
  - ad-creative
  - ads
  - ai-seo
  - analytics
  - aso
  - attribution
  - churn-prevention
  - co-marketing
  - cold-email
  - community-marketing
  - competitor-profiling
  - competitors
  - content-strategy
  - copy-editing
  - copywriting
  - cro
  - customer-research
  - directory-submissions
  - emails
  - events
  - free-tools
  - image
  - influencer-marketing
  - launch
  - lead-magnets
  - marketing-council
  - marketing-ideas
  - marketing-loops
  - marketing-plan
  - marketing-psychology
  - offers
  - onboarding
  - paywalls
  - popups
  - pricing
  - product-marketing
  - programmatic-seo
  - prospecting
  - public-relations
  - referrals
  - revops
  - sales-enablement
  - schema
  - seo-audit
  - signup
  - site-architecture
  - sms
  - social
  - video
- `html-mode`: Use when the user requests a standalone HTML artifact or HTML presentation, including shorthand such as 'plan; html'. Do not use for ordinary application code changes.
  - artifact
  - diagram
  - plan
  - prototype
  - slides
  - wireframe

## Skills

- `2nd-pass`: Use when the user asks for a `2pass` or a second pass, fresh-eyes review, final cleanliness check, or pre-delivery audit of work and related artifacts.
- `concise`: Use when the user requests to be more concise.
- `grilling`: Use when the user wants to stress-test a plan, decision, or idea through an interview or says `grill me`.
- `handoff`: Use when the user asks to prepare a handoff for another agent.
- `html-publish`: Use when publishing, updating, inspecting, or recovering a standalone HTML artifact through the configured html-publish service with a durable receipt. Use html-mode for artifact design and browser review.
- `image-creator`: Use when generating or editing raster images from the terminal with OpenAI GPT Image models through a Codex plan or, when explicitly requested, OpenRouter.
- `mermaid`: Use when choosing, creating, editing, or validating Mermaid diagrams to explain concepts, systems, processes, or data.
- `oem`: Load at the start of every session, before the first reply. Shared definitions and conventions for every task.
- `plan`: Use only when explicitly invoked as `plan`.
- `research`: Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
- `tavily`: Use only when explicitly invoked as `tavily`.
- `transcript`: Use when the user invokes `transcript` or asks to transcribe a YouTube video or Zoom recording.
- `unslop`: Use when communicating directly with the user or writing and editing documents.
- `writing-for-agents`: Use when creating, editing, or reviewing a skill, AGENTS.md, CLAUDE.md, or another document agents read.
- `writing-great-skills`: Use when creating, modifying, evaluating a skill.
