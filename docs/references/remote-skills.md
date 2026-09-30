---
name: remote-skills
description: Use andy's skills remotely
---

<!-- Generated from skills/*/SKILL.md by `just remote-skills`; do not edit -->

URL: https://raw.githubusercontent.com/pascalandy/skills/main/skills/[$skill]/SKILL.md

## General

| Skill | Description |
|---|---|
| 2nd-pass | Use when the user asks for a `2pass` or a second pass, fresh-eyes review, final cleanliness check, or pre-delivery audit of work and related artifacts. |
| bro | Use only when explicitly invoked as `bro`. |
| concise | Use when the user requests to be more concise. |
| distill | Use only when explicitly invoked as `distill`. |
| distill-prompt | Use only when explicitly invoked as `distill-prompt`. |
| grilling | Use when the user wants to stress-test a plan, decision, or idea through an interview or says `grill me`. |
| handoff | Use when the user asks to prepare a handoff for another agent. |
| html-mode | Use when the user requests a standalone HTML artifact or HTML presentation, including shorthand such as 'plan; html'. Do not use for ordinary application code changes. |
| html-publish | Use when publishing, updating, inspecting, or recovering a standalone HTML artifact through the configured html-publish service with a durable receipt. Use html-mode for artifact design and browser review. |
| illustration | Use only when explicitly invoked as `illustration`. |
| image-creator | Use when generating or editing raster images from the terminal with OpenAI GPT Image models through a Codex plan or, when explicitly requested, OpenRouter. |
| mermaid | Use when choosing, creating, editing, or validating Mermaid diagrams to explain concepts, systems, processes, or data. |
| meta-sc | Use only when explicitly invoked as `$meta-sc` to create or refactor a skill with several internal branches behind one entry point. |
| ontology-map | Use only when explicitly invoked as `ontology-map`. |
| pa-brainstorm | Use when the user wants to brainstorm an idea, feature, design, product decision, workflow change, or improvement. |
| pa-doc-update | Use only when explicitly invoked as `pa-doc-update`. |
| pa-glossary | Use only when explicitly invoked as `pa-glossary`. |
| pa-idea | Use only when explicitly invoked as `pa-idea`. |
| pa-postmortem | Use only when explicitly invoked as `pa-postmortem` after completed work or an incident. |
| pa-premortem | Use only when explicitly invoked as `pa-premortem`. |
| pa-scope | Use only when explicitly invoked as `pa-scope`. |
| pa-vision | Use only when explicitly invoked as `pa-vision` before planning. |
| qmd | Use only when explicitly invoked as `qmd` to search, retrieve, diagnose, maintain, or configure local QMD collections. |
| research | Use when the user wants a topic researched, docs or API facts gathered, or reading legwork delegated to a background agent. |
| simple-editor | Use only when explicitly invoked as `simple-editor`. |
| sparring | Use only when explicitly invoked as `sparring`. |
| storytelling | Use only when explicitly invoked as `storytelling`. |
| tavily | Use when the user explicitly requests Tavily, or for basic or current external web search and URL discovery. Do not select automatically for advanced research, extraction, schema-constrained output, or cited synthesis. |
| think | Use only when explicitly invoked as `$think` to improve the model of a situation before judging, deciding, or acting. |
| transcript | Use when the user invokes `transcript` or asks to transcribe a YouTube video or Zoom recording. |
| trello | Use only when explicitly invoked as `trello`. |
| unslop | Use when communicating directly with the user or writing and editing documents. |
| wiki-map | Use only when explicitly invoked as `wiki-map`. |
| writer-sk | Use only when explicitly invoked as `writer-sk`. |
| writing-for-agents | Writing documents for agents. Use when creating or editing skills, or modifying AGENTS.md or CLAUDE.md. |
| writing-great-skills | Use when creating, modifying, evaluating a skill. |

## Dev

| Skill | Description |
|---|---|
| architect | Use when the user invokes `architect` or requests software architecture design. |
| arena | Use when the user invokes `arena`, or when competing designs or implementations should be compared before choosing an approach for a non-trivial artifact. |
| automate-me | Use when the user wants their recurring working preferences captured or updated in a personal `-mode` skill. Do not use for a single task-specific workflow. |
| blast-radius | Use for 'blast radius of X', 'what could this break', or reviewing a small diff you don't trust. |
| cass | Use only when explicitly invoked as `cass` to search local coding-agent history |
| coding-eng-laws | Use when analyzing code, architecture, team, or planning decisions using software engineering laws and principles, or when `coding-eng-laws` is mentioned. |
| coding-language | Use when writing, debugging, linting, or reviewing Bash, Python, TypeScript, JavaScript-with-types, or Starlette/ASGI code. |
| coding-standard | Use when designing, implementing, or reviewing an agent-friendly CLI, including commands, flags, help text, output, errors, and safety behavior. |
| commit | Use when creating atomic git commits, staging logical changes, splitting commits, or formatting commit messages. |
| create-verification-skill | Use only when explicitly invoked as `create-verification-skill`. |
| figure-it-out | Use when the user invokes `figure-it-out`, for a large migration or cross-cutting effort, for work a human will review after stepping away, or when no narrower playbook fits. |
| gh-stack | Manages stacked PRs and splits multi-part work into reviewable branches with gh-stack. Use for stack creation, viewing, edits, push, submit, sync, rebase, merge, or checkout; when asked to split or isolate work for review; whenever a user mentions a stack, branch layers, dependent PRs, or gh stack; or when a stack is checked out. |
| git-local | Use when a task requires inspecting or working across an external GitHub repository's code and cloning it into the local cache is more effective than browsing source files online or making repeated GitHub API queries. |
| grill-for-unknowns | Use when a complex implementation plan has material unknowns that require evidence from source or authoritative documentation before implementation. Do not use for ordinary idea stress tests or work with settled acceptance criteria. |
| headless | Use when running `codex exec`, Claude Code, OpenCode, or Pi headlessly or non-interactively, including a scripted review by one of them. |
| how | Use for questions about how code works, code walkthroughs before changes, or questions about placement, ownership, and layering. Use `why` for design motivation. |
| interrogate | Use when the user asks for an adversarial or multi-model review, wants code or a plan stress-tested, or asks to uncover blind spots. |
| label-for-issues | Use when triaging GitHub issues, managing issue labels or decision comments, creating issues or PRs, or starting work on an issue. |
| maintain-verification-skill | Use when the user invokes `maintain-verification-skill` or asks to audit a project's existing verification skill. |
| make-bot-ui | Use when building a custom UI that starts agent tasks through a webhook or local runner. |
| matt-mode | Use when the user invokes matt-mode to clarify requirements, discuss design, map decisions, or prepare implementation through specs and tickets. |
| no-comments | Use only when explicitly invoked as `no-comments`, including `No comments` as an instruction. |
| pa-code-review | Use only when explicitly invoked as `pa-code-review` after implementation and before user-facing QA. |
| pa-doc-cleaner | Use only when explicitly invoked as `pa-doc-cleaner` for maintenance of existing documentation. For documenting a new change or decision, use `pa-doc-update`. |
| pa-qa | Use only when explicitly invoked as `pa-qa` for post-implementation validation or a reported user-facing problem. |
| pa-retro | Use only when explicitly invoked as `pa-retro`. |
| pi-workflow | Use when the user mentions `turk` or requests subagent execution workflows in Pi. |
| poteto-mode | Use only when explicitly invoked as `poteto` or `poteto-mode`. |
| principle-attack-the-premise | Apply when two or more fixes that share one premise have failed the same gate. Take a census of which actors hold the imbalance before the next fix, then question the premise instead of writing another fix that assumes it. |
| principle-boundary-discipline | Apply when wiring validation, error handling, or framework adapters. Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions. |
| principle-build-the-lever | Apply to any non-trivial work, not just bulk work: edits, migrations, analyses, checks. Build the tool that does it or proves it (codemod, script, generator, or a skill your subagents follow) instead of working by hand. The tool is the artifact a reviewer can rerun. |
| principle-encode-lessons-in-structure | Apply when you catch yourself writing the same instruction a second time, or notice a recurring correction. Encode the rule as a lint, metadata flag, runtime check, or script instead of more text. |
| principle-exhaust-the-design-space | Apply when facing a novel UI interaction or architectural decision with no precedent in the codebase. Build 2-3 competing prototypes and compare side by side before committing. |
| principle-experience-first | Apply when product, UX, or feature-scope tradeoffs come up. Choose user delight over implementation convenience; ship fewer polished features over more rough ones. |
| principle-fix-root-causes | Apply when debugging. Trace each symptom to its root cause and fix it there; reproduce first, ask why until you reach it, resist nil-check guards that silence crashes. |
| principle-foundational-thinking | Apply before writing logic: choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share. Get the data structures right so downstream code becomes obvious. |
| principle-guard-the-context-window | Apply when context is filling up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents; keep summaries in the main thread, not raw payloads. |
| principle-laziness-protocol | Apply when refactoring, evaluating diff size, or tempted to add abstractions, layers, or signal threading. Bias toward deletion and the smallest change that solves the problem. |
| principle-make-operations-idempotent | Apply when designing commands, lifecycle steps, or processing loops that run amid crashes, restarts, and retries. Converge to the same end state regardless of partial prior runs. |
| principle-migrate-callers-then-delete-legacy-apis | Apply when introducing a new internal API while old callers still exist. Migrate callers and delete the old API in the same wave instead of preserving compatibility layers. |
| principle-minimize-reader-load | Apply when reviewing or shaping code that's hard to trace. Count layers between question and answer, and hidden state in the reader's head; collapse one-caller wrappers and shrink mutable scope. |
| principle-model-the-domain | Apply when writing stateful logic, or when code branches a lot or repeats a shape assumption across files. Encode the domain in a structure instead of scattered conditionals. |
| principle-never-block-on-the-human | Apply when tempted to ask 'should I do X?' on reversible work. Proceed, present the result, let the human course-correct after the fact; reserve confirmation for irreversible actions. |
| principle-outcome-oriented-execution | Apply during planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture; don't preserve smooth intermediate states with throwaway compatibility code. |
| principle-prove-it-works | Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.' |
| principle-redesign-from-first-principles | Apply when integrating a new requirement into an existing design. Redesign as if the requirement had been a foundational assumption from day one, instead of bolting it on. |
| principle-separate-before-serializing-shared-state | Apply when concurrent actors might write to the same file, branch, key, or state object. Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant. |
| principle-sequence-verifiable-units | Apply to multi-step work (sweeps, migrations, runs of similar edits) and to how you stack commits and PRs. Break work into small units that each end in a verifiable state, check each before the next, and order delivery so the sequence proves itself to a reviewer. |
| principle-subtract-before-you-add | Apply when sequencing an addition, refactor, or rewrite. Remove dead code, redundant validators, and stub references first, then build on the simpler base. |
| principle-test-behavior-not-implementation | Apply when you write, change, or keep a test. Call the code the way its users do and assert the result they observe against a literal expected value. If the test would still pass when every imported function returns undefined, rewrite the assertion or delete the test. |
| principle-type-system-discipline | Apply when designing types, reviewing a function signature, or writing code in any statically-typed language. Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, refuse to lie to the compiler, exhaust variants, derive from authoritative schemas. |
| profile-routing-matrix | Use when the user invokes profile-routing-matrix or asks to delegate work, including 'delegate' or 'délègue'. Routes subagents by role, model, and reasoning level. |
| recall | Use only when explicitly invoked as `recall`. |
| reflect | Use only when explicitly invoked as `reflect`. |
| retro | Review a coding session for evidence-backed improvements to agent navigation, instructions, checks, or tools. |
| setup-pstack | Use for /setup-pstack, configure pstack models, or changing pstack's model choices. |
| show-me-your-work | Use when the user invokes `show-me-your-work`, for long-running, autonomous, or multi-phase work, or for work a human will review after stepping away. |
| swarm | Use for /swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration. |
| tdd | Use only when explicitly invoked as `tdd`. |
| teach | Use when the user asks to be taught, requests a guided technical explanation, or wants one account combining how something works with why it was designed that way. |
| technical-writing | Use for /technical-writing or when writing or reviewing docs, RFCs, readmes, PR descriptions, or commit messages. |
| test-audit | Invoke whenever writing, changing, reviewing, or sweeping tests. Authoring gate for new tests plus audit workflow for low-value, implementation-coupled, or duplicative tests and the test-only production seams they demand. |
| thermo-nuclear-code-quality-review | Run an extremely strict maintainability review for abstraction quality, giant files, and spaghetti-condition growth. Use for a thermo-nuclear code quality review, thermonuclear review, deep code quality audit, or especially harsh maintainability review. |
| typesafe-ai | Build AI-powered software with TypeSafe: small units of AI intelligence you can use like programming primitives. Its System One models, including Jev, turn natural language and application state into typed judgments and probabilities that code can combine. Use when a feature needs programmable common sense, when brainstorming what AI could make possible in an app, or when an LLM prompt-and-parse step could become a structured decision. Applications include routing, ranking, extraction, verification, and interactive experiences; these are starting points, not the limits. Read live docs and cookbooks to find useful patterns and discover new combinations. |
| typescript-best-practices | Use when TypeScript work centers on type safety, domain modeling, narrowing, casts, or runtime boundaries. Use `coding-language` for general TypeScript implementation and tooling. |
| verify-transcript | Use when validating transcript CLI behavior or locating its verification features. Use for paid YouTube end-to-end checks only when explicitly authorized. |
| verify-video-archive | Use when validating the macOS or Linux archive workflow reached by `just convert-video`, including real media, prerequisites, terminal progress, source safety, locking, and recovery. |
| why | Use for questions about design rationale, the history of regressions or incidents, or the evidence behind thresholds and tradeoffs. Use `how` for runtime behavior. Do not use for plain commit or date lookups. |
