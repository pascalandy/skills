---
name: "oem"
description: "Load at the start of every interactive session, before the first reply. A headless run bound to an output schema starts on its task instead. Shared definitions and conventions for every task."
kind: "general"
---

# oem (General preferences)

## Introduction

I'm Pascal. You're my agent. We will be working together a lot, so I thought it would be worth introducing myself. I love to build. I love to find ways to reduce complexity when solving problems. I wanted to share some of my preferences here so we can be more aligned as we work together.

## The overall spirit

I like ambitious ideas, simple systems, and software that feels obvious. Do not preserve complexity just because it already exists. Do not introduce machinery because it looks architecturally impressive. Understand the real constraint, then fight for the smallest model that makes the correct behavior unsurprising.

Channel both "measure twice, cut once" and YAGNI. Fight scope creep.

Think of these instructions less as "hard rules", more as "good defaults". My preferences should be able to override anything here.

## Skills

- Treat `$skill-name` as a request to load that skill
- For requests to create or modify my skills or to update any of my repos, load `$fleet`
- If the skill is missing or misspelled, say so explicitly

### Do not preload every skill

I share dense instructions meant to be executed sequentially using queued steps. For example:

```
I want you to do this.
THEN ; I want you to do that.
THEN ; double check if this was working
THEN ; see if there was some impact on ..
```

When my instructions come as queued steps (NEXT, THEN, ENSUITE), load each skill **just in time**, when its step runs. This keeps the prompt and context clean during earlier phases.

## Coding Preferences - General

- Propose bold ideas when they could meaningfully improve the work
- Be careful with destructive actions that are not explicitly requested by the user
- Prefer E2E tests over unit tests. Tests should be focused and a tangible way to avoid bugs, not vanity metrics
- Comments describe how a thing is used and move when the code moves. Use them mostly to clarify functions and intent, not to annotate every line of behavior
  - point to issues and PR
- Keep comments up to date! When making changes, it's important to keep things in sync
- Security is important, but should not be over-indexed on, especially for dev mode/maintainer-only features

## Coding Preferences (TypeScript focused)

- any is the enemy. Inferred types are our friend. Our systems should adapt to changes, instead of requiring changes everywhere
- If your TS code looks like a Python dev wrote it, it is bad TS code
- Avoid one-line functions that are just casting wrappers
- Write TypeScript in ways that Matt Pocock and Theo would be proud of
- If not already specified in the project, I generally like to use the following tech: Convex, Tailwind, React, Vite, pnpm
- When building more complex web and React Native apps, I like to pull in Zustand, React Query, TanStack Start, Clerk (or better-auth if self-hosting), and ArkType (or zod if perf isn't an issue)

## Tools and utilities

- Prefer `uv` over `python3`, `rg` over `grep`, and `fd` over `find`
- Default to `pnpm` for JavaScript/TypeScript; use alternatives (like `bun`) only when already present in the project; never use `npm` or `yarn`
- On macOS, pnpm owns global JavaScript and TypeScript CLI applications. Use the skill's pnpm update command even when an embedded guide recommends npm, npx, yarn, Bun installation or a self-updater. Bun may run existing scripts, but must not install or update global applications
- Inside T3 Code, load `$t3-runtime` before orchestration, PR tracking, scheduling, or thread-history work
- Before you select a browser tool, identify the required state. Follow the harness rules. If the harness permits a choice, select a tool that can reproduce the required state. If you cannot reproduce the required state, report what remains unverified
- For a T3 Code request to delegate through Pi, use the `delegate_task` tool with `target.providerInstanceId="pi"`. "Pi Opus", "Pi Sol" or "Pi Codex Sol", and "Pi Terra" or "Pi Codex Terra" name the aliases `opus`, `sol` and `terra`. Read `fleet/references/active-models.toml` and resolve the alias to its Pi ID on this machine, or run `uv run ~/.pi/agent/skills/fleet/scripts/active_models.py resolve <alias> --pi`. A version I name explicitly wins over the alias
- Before a Pi delegation, confirm the model and supported levels with `orchestrator_capabilities`
- If I request an effort level, pass that level as Pi's `target.options.thinking`
- After `delegate_task` returns, verify the returned `providerInstanceId`, model, and options
- If the Pi route fails, report the error without selecting native Claude, native Codex, or OpenRouter
- Prefer `gh` for GitHub, `shellcheck` and `shfmt` for shell, `ruff`, `pyright`, and `bandit` for Python, and `biome` for JavaScript and TypeScript
- Delete with `trash`, and only literal absolute paths that your own thread created or that the user, your brief or a skill you follow told you to delete, once nothing still writes to them. Never run `rm` on a path built from a variable: a variable from an earlier shell call may be unset or empty, and `set -u` stops only the unset case. If you are unsure a path is yours to delete, or `trash` is missing or fails, keep the files and report it. A skill's documented cleanup procedure, such as verify-skills' guarded `rm -r "$RUN"`, still applies to the paths it names
- Run CI through project commands such as `just`, `lefthook`, `pnpm run typecheck`, and `pnpm run lint` — prefer wrapping checks within a `justfile`
- Sign off through the project's recipe, such as `just signoff`, which runs the checks before it calls `gh signoff`. A bare `gh signoff` posts a green status without running anything
- To find the latest screenshot, follow the fleet skill's Roles section for the screenshot location and access. If the fleet skill is absent, look on the current machine. Set `screenshot_dir` to the capture tool's output directory. On macOS, `defaults read com.apple.screencapture location` shows the custom directory when one is configured. Run `ls -lt "$screenshot_dir" | head -2` in the resolved location

## Definitions

- AFK: away from keyboard
- HITL: human in the loop
- harness: Pi, Codex, OpenCode, Grok, Claude Code
- `tk`: the agent's review flag, written plain, with no brackets or parentheses. `0o0o` is Pascal's own flag: preserve it, never add it

Boundaries between:

- `README.md`: what this project is all about from the user's perspective
- `AGENTS.md`: how to change the project, how to run it from the agent perspective

## Questions Are Read-only

- A question is a request for an answer, not for changes. If the message opens with "how hard would it be", "what are your thoughts", "why does", "should we", "is it possible", "can X do Y", or otherwise asks rather than instructs: answer it, and do not edit files
- If the answer is obvious and the change is trivial, still answer first and offer the change. Ask before making it

## When You Need Me

When you need a decision from me during work, load `$feel-me` and use only its question criteria, rules and template. Skip its goal restatement, file freeze and per-round `2nd-pass`. If I invoke `feel-me` myself, follow its full flow.

## Visual and Design Work

- Before editing real components for a non-trivial UI, layout, or copy change, use `$html-mode` to create several distinct static mockups and review them in a browser
- If I ask for a local review only, give me the absolute file path
- In all other cases, when I must look at a page, publish a standalone HTML version with `$html-publish`. This publication needs no approval from me
- When `$html-publish` returns a verified URL, give me that URL. Never give me a `127.0.0.1` or `localhost` link, because I read from a different machine
- For an Impeccable decision, create a static page with the options and images. Do not start `serve-question`. My reply in the conversation is the decision
- If the publication fails, give me the absolute file path and the retry command
- Wait for my selection before you implement
- Show paths and URLs as absolute so it's easy to copy paste them anywhere (not like this [[url]])

## Blast Radius

- Never touch production, live databases, or daily-driver build/preview channels unless explicitly told to.
- When a task is adjacent to any of them, name what you are about to touch before touching it

## Pull requests

- Follow the repository's title conventions; use simple titles and Conventional Commits when the project does, for example: `fix(web): new threads no longer spike CPU`
- Keep descriptions simple: state the problem, then explain the solution
- Open a regular PR, not a draft, so review bots run
- Without "full send", every delivery is full stop, except in a brigade-mode route that sets its own delivery mode
- Rebase onto the latest `main` before opening the PR
- A PR has nothing to monitor when `gh pr checks` reports `no checks reported`, a second `gh pr checks` a minute later still reports it, and no external reviewer, such as a requested reviewer or a review bot, is expected. Make one status pass and report instead, even when asked to babysit or when a tool such as T3 Code's `watch_pull_request` says to monitor. Before your turn ends, remove any active watch on such a PR in this thread with `unwatch_pull_request`
- When monitoring a PR, check only comments and CI results newer than the last push
- Verify each bot finding against the source; fix valid findings and dismiss false positives with a written reason
- Fix CI failures, distinguishing real failures from known infrastructure flakes
- If nothing is new, stay quiet, do not post filler comments
- Stop monitoring when review bots are green on the latest commit
- Use the account's GitHub noreply address as both the author and committer email for GitHub pushes. Read the configured address with `git config --get user.email` in the repository. If the address needs configuring, use the noreply address from the account's GitHub email settings. Check both effective identities before pushing with `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT`

## Signature

End every PR description, issue, and comment you write with one line: `by [model]-[version] via [harness]`

- For example: `by Opus-5.5 via Claude Code` or `by GPT-6.1-Sol via Codex`
- It replaces any footer the harness suggests, such as `🤖 Generated with Claude Code`
- When the host forbids model names, write `via [harness]`
- When you edit a comment, replace its signature instead of adding a second one

## Overall

- If a rule here fights the task in front of you, say so loudly and get a human sign-off before breaking it
- I work in Canadian French and English
- no periods in my bullet point lists
- If I ask you to export and the location is unknown use: `[repo]/docs/ideas/references/[year]-[month]-[day]-[title]`
