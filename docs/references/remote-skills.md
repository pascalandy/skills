---
name: remote-skills
description: Use andy's skills remotely
---

<!-- Generated from skills/*/SKILL.md and skills/*/playbooks/* by `just remote-skills`; do not edit -->

URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md

A mode's routes run through that mode's SKILL.md.

## General

### Modes

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

### Skills

- `2nd-pass`: Use when the user asks for a `2pass` or a second pass, fresh-eyes review, final cleanliness check, or pre-delivery audit of work and related artifacts.
- `brainstorm`: Use only when explicitly invoked as `brainstorm`.
- `concise`: Use when the user requests to be more concise.
- `consensus`: Use only when explicitly invoked as `consensus`.
- `frontend-design`: Guidance for distinctive, intentional visual design when building new UI or reshaping an existing one. Helps with aesthetic direction, typography, and making choices that don't read as templated defaults.
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

## Dev

### Modes

- `code-review-mode`: Use for a code review of a branch or code area, an architecture review, a test audit, or a thermonuclear review, and whenever writing or changing tests.
  - `architecture-review`: Review the module shape across a code area and propose refactors that turn shallow modules into deep ones.
  - `test-audit`: Audit tests, and production code that exists only for tests, keeping only tests that add real confidence.
  - `thermo-quality-review`: Run an unusually strict review of production code for structure, file size, branching, types, and layering.
- `matt-mode`: Use when the user invokes matt-mode to clarify requirements, discuss design, map decisions, or prepare implementation through specs and tickets.
  - `codebase-design`: Shared vocabulary for designing deep modules.
  - `domain-modeling`: Build and sharpen a project's domain model.
  - `grill-me`: A relentless interview to sharpen a plan or design.
  - `grill-with-docs`: A relentless interview to sharpen a plan or design, which also creates docs (ADR's and glossary) as we go.
  - `to-spec`: Turn the current conversation into a spec and publish it to the project issue tracker: no interview, just synthesis of what you've already discussed.
  - `to-tickets`: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker (edges as text in one file per ticket locally, or native blocking links on a real tracker).
  - `wayfinder`: Plan a huge chunk of work (more than one agent session can hold) as a shared map of decision tickets on your issue tracker, and resolve them one at a time until the way to the destination is clear.
- `poteto-mode`: Use only when explicitly invoked as `poteto` or `poteto-mode`.
  - `authoring-a-skill`: Write or edit a skill's SKILL.md and supporting files.
  - `autonomous-run`: Drive one long task to completion without stopping, until a stated exit condition holds.
  - `autopilot-full`: Run a queue of independent PRs to merged with full autonomy, one owner per PR and each merge verified first.
  - `autopilot-stack`: Build and verify a queue of changes autonomously, then hand over one reviewed stack for the operator to land.
  - `babysit`: Drive a PR or a stack to merge-ready by resolving conflicts, review threads, and CI.
  - `bug-fix`: Reproduce, root-cause, and fix a reported defect with runtime evidence.
  - `eval`: Test how a skill, structure, or prompt change affects agent behavior before promoting it.
  - `feature`: Build new or changed behavior, starting from a named data shape.
  - `hillclimb`: Improve one metric toward a target through measured hypotheses, a decision log, and one commit per accepted win.
  - `investigation`: Answer a read-only question about how code works, why it was built that way, or which option to pick, with cited evidence.
  - `multi-phase-plan`: Write the plan for work that spans several phases or stacked PRs, as a checklist an owner runs box by box.
  - `opening-a-pr`: Open a pull request at the end of any other playbook.
  - `orchestrate`: Coordinate a multi-day project of many stacked PRs and subagents from one standing coordinator.
  - `pause-safely`: Suspend in-flight work at a safe boundary, with a checkpoint another session can resume from.
  - `perf-issue`: Trace a measured slowness and improve it against a baseline.
  - `prototype`: Build a throwaway sketch to settle a design or behavior question by observing it.
  - `refactoring`: Restructure code without changing its behavior, such as a rename, extraction, or move.
  - `runtime-forensics`: Diagnose a runtime symptom such as a leak, idle CPU spin, or glitch from live instrumentation.
  - `session-pickup`: Resume or take over another agent's in-flight work from a transcript, a cloud-agent URL, or a pushed branch.
  - `shipping`: Independently verify each PR of a green stack, then land the verified run from the bottom.
  - `trace-forensics`: Diagnose a captured profiling artifact such as a CPU profile, trace, or heap snapshot.
  - `visual-parity`: Make two UI implementations match pixel for pixel, or migrate a styling system without visual change.
  - `worktree-cleanup`: Reclaim disk space by pruning merged or abandoned git worktrees and stale iOS simulators.

### Skills

- `architect`: Use when the user invokes `architect` or requests software architecture design.
- `automate-me`: Use when the user wants their recurring working preferences captured or updated in a personal `-mode` skill. Do not use for a single task-specific workflow.
- `blast-radius`: Use for 'blast radius of X', 'what could this break', or reviewing a small diff you don't trust.
- `coding-eng-laws`: Use when analyzing code, architecture, team, or planning decisions using software engineering laws and principles, or when `coding-eng-laws` is mentioned.
- `coding-language`: Use when writing, debugging, linting, or reviewing Bash, Python, TypeScript, JavaScript-with-types, or Starlette/ASGI code.
- `coding-standard`: Use when designing, implementing, or reviewing an agent-friendly CLI, including commands, flags, help text, output, errors, and safety behavior.
- `commit`: Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages.
- `create-verification-skill`: Use only when explicitly invoked as `create-verification-skill`.
- `epic-grooming`: Use only when explicitly invoked as `epic-grooming`, to rank open GitHub issues and group them into Epics.
- `execute`: Use only when explicitly invoked as `execute` or `implement`, or by a clear go-ahead to implement an agreed plan.
- `gh-stack`: Manages stacked PRs and splits multi-part work into reviewable branches with gh-stack. Use for stack creation, viewing, edits, push, submit, sync, rebase, merge, or checkout; when asked to split or isolate work for review; whenever a user mentions a stack, branch layers, dependent PRs, or gh stack; or when a stack is checked out.
- `git-local`: Use when a task requires inspecting or working across an external GitHub repository's code and cloning it into the local cache is more effective than browsing source files online or making repeated GitHub API queries.
- `grill-for-unknowns`: Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation. Do not use for ordinary idea stress tests or work with settled acceptance criteria.
- `headless`: Use when running `codex exec`, `codex exec review`, Claude Code, Grok, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. `headless` may arrive as any voice-to-text spelling that sounds like it, such as `endless` or `adless`.
- `how`: Use for questions about how code works, code walkthroughs before changes, or questions about placement, ownership, and layering. Use `why` for design motivation.
- `interrogate`: Use when the user asks for an adversarial or multi-model review, wants code or a plan stress-tested, or asks to uncover blind spots.
- `json-config-schema`: Use when creating, reviewing, changing, versioning, or validating the JSON Schema of a JSON config file.
- `label-for-issues`: Use when triaging GitHub issues, managing issue labels or decision comments, creating issues or PRs, or starting work on an issue.
- `maintain-verification-skill`: Use when the user invokes `maintain-verification-skill` or asks to audit a project's existing verification skill.
- `verify-skills`: Use when verifying `just compile-skills`, `just remote-skills`, `just install-skills`, or `just skills-discover` in the skills repository, such as after changing their scripts or adding, renaming, or moving a skill.
- `verify-transcript`: Use when validating transcript CLI behavior, locating its verification features, or running the paid YouTube end-to-end check.
- `verify-video-archive`: Use when validating the macOS or Linux archive workflow reached by `just convert-video`, including real media, prerequisites, terminal progress, source safety, locking, and recovery.

### Helpers

- `arena`: Use when the user invokes `arena`, or when competing designs or implementations should be compared before choosing an approach for a non-trivial artifact.
- `figure-it-out`: Use when the user invokes `figure-it-out`, for a large migration or cross-cutting effort, for work a human will review after stepping away, or when no narrower playbook fits.
- `make-bot-ui`: Use when building a custom UI that starts agent tasks through a webhook or local runner.
- `no-comments`: Use only when explicitly invoked as `no-comments`, including `No comments` as an instruction.
- `principle-prove-it-works`: Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'
- `recall`: Use only when explicitly invoked as `recall`.
- `reflect`: Use only when explicitly invoked as `reflect`.
- `show-me-your-work`: Use when the user invokes `show-me-your-work`, for long-running, autonomous, or multi-phase work, or for work a human will review after stepping away.
- `swarm`: Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration.
- `tdd`: Use only when explicitly invoked as `tdd`.
- `teach`: Use when the user asks to be taught, requests a guided technical explanation, or wants one account combining how something works with why it was designed that way.
- `technical-writing`: Use for /technical-writing or when writing or reviewing docs, RFCs, readmes, PR descriptions, or commit messages.
- `typescript-best-practices`: Use when TypeScript work centers on type safety, domain modeling, narrowing, casts, or runtime boundaries. Use `coding-language` for general TypeScript implementation and tooling.
- `why`: Use for questions about design rationale, the history of regressions or incidents, or the evidence behind thresholds and tradeoffs. Use `how` for runtime behavior. Do not use for plain commit or date lookups.
