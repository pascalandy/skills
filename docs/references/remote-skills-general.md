---
name: remote-skills-general
description: Use andy's general skills remotely
---

<!-- Generated from skills/*/SKILL.md and skills/*/playbooks/* by `just remote-skills`; do not edit -->

URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md

A mode's routes run through that mode's SKILL.md.

## Modes

- `andy-mode`: Use only when explicitly invoked as `andy-mode`, followed by `;` and a route name, where `andy` may be any voice-to-text spelling that sounds like it, such as `nd`, `indie`, or `endymode`.
  - `cass`: Search past coding-agent sessions with CASS, a CLI that indexes local agent transcripts.
  - `distill`: Apply a named distill prompt to a local text file and save the result in a timestamped folder beside it.
  - `distill-prompt`: List, choose, or add a reusable prompt for distilling long-form text, ready for the `distill` route.
  - `docs`: Document a change, decision, or artifact that already exists, as one bounded documentation job.
  - `docs-cleaner`: Clean up existing documentation by fixing drift, duplicates, frontmatter, and structure.
  - `glossary`: Create or revise a canonical glossary of a project's or domain's vocabulary.
  - `idea`: Write down a rough idea in its author's voice and export it.
  - `illustration`: Design and generate a 16:9 hand-drawn illustration that turns one key idea of a text into a scene.
  - `meta-skill-creator`: Create or refactor a skill that routes one entry point to several internal branches.
  - `ontology`: Generate a fixed five-file ontology of concepts, systems, questions, and connections from a folder of text.
  - `qa`: Validate a finished change against its accepted behavior, or turn a reported problem into durable QA findings.
  - `qmd`: Search, retrieve from, or maintain collections in QMD, a local search engine for Markdown files.
  - `retro-global`: Review a coding session for changes to the agent's environment, such as checks, steering files, or tools, that would help the next run.
  - `retro-skill-usage`: Find where a skill loaded in a session was wrong or confusing enough to cost a detour, and propose one-line fixes.
  - `simple-editor`: Clean up personal journal notes while keeping the author's raw voice.
  - `sparring`: Challenge an opinion or argument as a blunt sparring partner who tests assumptions instead of agreeing.
  - `storytelling`: Discover, write, diagnose, adapt, or explain a narrative so it moves its audience.
  - `think`: Pick the smallest reasoning method that resolves the uncertainty blocking a judgment, decision, or action.
  - `trello`: Manage Trello boards, lists, and cards through the Trello REST API.
  - `wiki-map`: Build or maintain a Markdown knowledge base with provenance, indexes, and cross-references.
  - `write-with-clarity`: Edit prose for clarity and concision, following Strunk's rules and removing AI writing patterns.
- `corey-mode`: Use only when a request contains the word marketing, or invokes corey-mode, to run Corey Haines' marketing playbooks.
  - `ab-testing`: When the user wants to plan, design, or implement an A/B test or experiment, or build a growth experimentation program.
  - `ad-creative`: When the user wants to generate, iterate, or scale ad creative — headlines, descriptions, primary text, or full ad variations — for any paid advertising platform.
  - `ads`: When the user wants help with paid advertising campaigns on Google Ads, Meta (Facebook/Instagram), LinkedIn, Twitter/X, or other ad platforms.
  - `ai-seo`: When the user wants to optimize content for AI search engines, get cited by LLMs, or appear in AI-generated answers.
  - `analytics`: When the user wants to set up, improve, or audit analytics tracking and measurement.
  - `aso`: When the user wants to audit or optimize an App Store or Google Play listing.
  - `attribution`: When the user wants to figure out which marketing actually drives conversions and revenue, choose or interpret an attribution model, or reconcile conflicting numbers across tools.
  - `churn-prevention`: When the user wants to reduce churn, build cancellation flows, set up save offers, recover failed payments, or implement retention strategies.
  - `co-marketing`: When the user wants to find co-marketing partners, plan joint campaigns, or brainstorm partnership opportunities.
  - `cold-email`: Write B2B cold emails and follow-up sequences that get replies.
  - `community-marketing`: Build and leverage online communities to drive product growth and brand loyalty.
  - `competitor-profiling`: When the user wants to research, profile, or analyze competitors from their URLs.
  - `competitors`: When the user wants to create competitor comparison or alternative pages for SEO and sales enablement.
  - `content-strategy`: When the user wants to plan a content strategy, decide what content to create, or figure out what topics to cover.
  - `copy-editing`: When the user wants to edit, review, or improve existing marketing copy, or refresh outdated content.
  - `copywriting`: When the user wants to write, rewrite, or improve marketing copy for any page — including homepage, landing pages, pricing pages, feature pages, about pages, or product pages.
  - `cro`: When the user wants to optimize, improve, or increase conversions on any marketing page or form — including homepage, landing pages, pricing pages, feature pages, lead capture forms, or contact forms.
  - `customer-research`: When the user wants to conduct, analyze, or synthesize customer research.
  - `directory-submissions`: When the user wants to submit their product to startup, SaaS, AI, agent, MCP, no-code, or review directories for backlinks, domain rating, and discovery.
  - `emails`: When the user wants to create or optimize an email sequence, drip campaign, automated email flow, or lifecycle email program.
  - `events`: When the user wants to plan, run, sponsor, speak at, or get pipeline from events — webinars, conferences, trade shows, meetups, dinners, workshops, virtual summits, or user conferences.
  - `free-tools`: When the user wants to plan, evaluate, or build a free tool for marketing purposes — lead generation, SEO value, or brand awareness.
  - `image`: When the user wants to create, generate, edit, or optimize images for marketing — blog heroes, social graphics, product mockups, profile banners, listing visuals, or brand assets.
  - `influencer-marketing`: When the user wants to run influencer, creator, or ambassador partnerships to promote their product — finding and vetting partners, structuring deals, briefing creators, disclosure compliance, and measuring ROI.
  - `launch`: When the user wants to plan a product launch, feature announcement, or release strategy.
  - `lead-magnets`: When the user wants to create, plan, or optimize a lead magnet for email capture or lead generation.
  - `marketing-council`: When the user wants multiple expert perspectives on a marketing question — a simulated board of advisors staffed by legendary marketers (Seth Godin, David Ogilvy, Eugene Schwartz, April Dunford, Rory Sutherland, Alex Hormozi, Byron Sharp, and more).
  - `marketing-ideas`: When the user needs marketing ideas, inspiration, or strategies for their SaaS or software product.
  - `marketing-loops`: When the user wants to set up a recurring, self-running marketing workflow — a repeatable loop an AI agent runs on a cadence (weekly, daily, on a trigger) rather than a one-off task.
  - `marketing-plan`: When the user needs a comprehensive marketing plan for a client, a company they advise, or their own product.
  - `marketing-psychology`: When the user wants to apply psychological principles, mental models, or behavioral science to marketing.
  - `offers`: When the user wants to design, construct, or improve an offer — the thing they actually sell — including value framing, bonus stacking, guarantee design, scarcity/urgency, naming, and payment structure.
  - `onboarding`: When the user wants to optimize post-signup onboarding, user activation, first-run experience, or time-to-value.
  - `paywalls`: When the user wants to create or optimize in-app paywalls, upgrade screens, upsell modals, or feature gates.
  - `popups`: When the user wants to create or optimize popups, modals, overlays, slide-ins, or banners for conversion purposes.
  - `pricing`: When the user wants help with pricing decisions, packaging, or monetization strategy.
  - `product-marketing`: When the user wants to create or update their product marketing context document.
  - `programmatic-seo`: When the user wants to create SEO-driven pages at scale using templates and data.
  - `prospecting`: When the user wants to find, qualify, and build a list of prospects to reach out to — across B2B SaaS, general B2B, or local small businesses.
  - `public-relations`: When the user wants help with public relations, earned media, press coverage, journalist outreach, or media strategy (not pull requests).
  - `referrals`: When the user wants to create, optimize, or analyze a referral program, affiliate program, or word-of-mouth strategy.
  - `revops`: When the user wants help with revenue operations, lead lifecycle management, or marketing-to-sales handoff processes.
  - `sales-enablement`: When the user wants to create sales collateral, pitch decks, one-pagers, objection handling docs, or demo scripts.
  - `schema`: When the user wants to add, fix, or optimize schema markup and structured data on their site.
  - `seo-audit`: When the user wants to audit, review, or diagnose SEO issues on their site.
  - `signup`: When the user wants to optimize signup, registration, account creation, or trial activation flows.
  - `site-architecture`: When the user wants to plan, map, or restructure their website's page hierarchy, navigation, URL structure, or internal linking.
  - `sms`: When the user wants to plan, build, or optimize SMS or MMS marketing — including welcome flows, abandoned cart texts, post-purchase, win-back, promotional sends, or transactional/auth SMS.
  - `social`: When the user wants help creating, scheduling, or optimizing social media content for LinkedIn, Twitter/X, Instagram, TikTok, Facebook, or other platforms, or wants to do social listening and engagement triage.
  - `video`: When the user wants to create, generate, or produce video content using AI tools or programmatic frameworks.
- `html-mode`: Use when the user requests a standalone HTML artifact or HTML presentation, including shorthand such as 'plan; html'. Do not use for ordinary application code changes.
  - `artifact`: Build a standalone HTML report, explainer, landing page, tool, or data story that no narrower playbook owns.
  - `diagram`: Draw an HTML diagram that shows how components, events, states, or concepts relate.
  - `plan`: Turn a work plan into an HTML document that shows its commitments, order, owners, dependencies, and risks.
  - `prototype`: Build a polished HTML mockup or a working prototype of a bounded product flow.
  - `slides`: Build an HTML slide deck with reveal.js that tells one story a screen at a time.
  - `wireframe`: Sketch low-fidelity HTML wireframes that test content, navigation, and layout before visual design.

## Skills

- `2nd-pass`: Use when the user asks for a `2pass` or a second pass, fresh-eyes review, final cleanliness check, or pre-delivery audit of work and related artifacts.
- `concise`: Use when the user requests to be more concise.
- `consensus`: Use only when explicitly invoked as `consensus`.
- `grilling`: Use when the user wants to stress-test a plan, decision, or idea through an interview or says `grill me`.
- `handoff`: Use when the user asks to prepare a handoff for another agent.
- `html-publish`: Use when publishing, updating, inspecting, or recovering a standalone HTML artifact through the configured html-publish service with a durable receipt. Use html-mode for artifact design and browser review.
- `image-creator`: Use when generating or editing raster images from the terminal with OpenAI GPT Image models through a Codex plan or, when explicitly requested, OpenRouter.
- `mermaid`: Use when choosing, creating, editing, or validating Mermaid diagrams to explain concepts, systems, processes, or data.
- `oem`: Load at the start of every session, before the first reply. Shared definitions and conventions for every task.
- `research`: Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent.
- `tavily`: Use only when explicitly invoked as `tavily`.
- `transcript`: Use when the user invokes `transcript` or asks to transcribe a YouTube video or Zoom recording.
- `unslop`: Use when communicating directly with the user or writing and editing documents.
- `writing-for-agents`: Use when creating, editing, or reviewing a skill, AGENTS.md, CLAUDE.md, or another document agents read.
- `writing-great-skills`: Use when creating, modifying, evaluating a skill.
