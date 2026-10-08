# Product Marketing Context

**Document version:** v2
**Last updated:** 2026-10-04

## Product Overview
**One-liner:** Skills that make the AI chat you already use follow proven methods, with one pasted sentence and nothing to install.
**What it does:** A public collection of skills: written playbooks an AI agent reads and follows. The reader pastes one sentence into ChatGPT, Claude, or another chat app that can open web pages. From then on, a request such as `marketing ; write a headline for my bakery` makes the agent open the matching playbook and follow its steps instead of improvising.
**Product category:** AI skills and workflows for chat assistants. People search for "ChatGPT prompts", "AI workflows", or "Claude skills"
**Product type:** Free, open-source collection on GitHub (MIT)
**Business model:** Free. No account, no install, no tracking

## Target Audience
**Target readers:** Professionals who use an AI chat every day and never open a terminal: business analysts, consultants, marketers, managers, solo founders, freelancers. They read English or Canadian French; the guide exists in both
**Primary use case:** Get consistent, high-quality results from an AI chat without writing a long prompt each time
**Jobs to be done:**
- Turn a vague request into a structured result: a plan, a marketing page, a cleaner text
- Stop re-explaining the same instructions in every chat
- Borrow proven methods without studying them first
**Use cases:**
- Agree before acting: `consensus`
- Write and tighten prose: `unslop`, `concise`, `andy-mode ; write-with-clarity`
- Do marketing work such as positioning, page copy, and emails: `corey-mode`
- Stress-test a plan or an idea: `grilling`, `andy-mode ; sparring`, `andy-mode ; think`
- Make a visual one-pager or a slide deck: `html-mode`

## Problems & Pain Points
**Core problem:** An AI chat answers whatever you type, so vague requests get generic answers. Good results take long prompts and the same back-and-forth every time.
**Why alternatives fall short:**
- Prompt libraries give one-off prompts to adapt each time, with no method or steps behind them
- Custom GPTs and Projects stay locked in one app, and someone has to build and maintain them
- Skill collections for developers need a terminal and a coding agent
**What it costs them:** Time lost in back-and-forth, uneven quality, and results they can't trust
**Emotional tension:** "The AI should be able to do this, but I don't know how to ask"

## Competitive Landscape
**Direct:** Other public skill collections, such as PStack for Cursor or Corey Haines' marketingskills. They are built for developers who install them in a coding agent
**Secondary:** Prompt libraries and custom GPTs. They hold single prompts with no method behind them
**Indirect:** Doing the work by hand, or hiring a consultant

## Differentiation
**Key differentiators:**
- Nothing to install: one sentence in any chat app that can open a web page
- Modes: one name opens a family of playbooks, such as `corey-mode` for marketing, `andy-mode` for thinking and writing tools, and `html-mode` for visual documents
- Methods from practitioners: a business analyst's corporate experience, plus credited playbooks from Corey Haines and others
- Open: every instruction is a plain text file anyone can read before using it
**How we do it differently:** The agent reads a written playbook and follows its steps instead of guessing from a prompt
**Why that's better:** Results are consistent, and the reader types less
**Why customers choose us:** It works today, in the app they already use

## Objections
| Objection | Response |
|-----------|----------|
| "I'm not technical" | You never open a terminal. You paste one sentence, then talk normally |
| "Is it safe? What does it read?" | Every skill is a plain text file on GitHub. Read it before you use it. Nothing gets installed |
| "Will it work in my app?" | It works in chat apps that can open a web page. The guide says what to do if yours can't |
| "Why not write a good prompt myself?" | A skill is a good prompt someone already tested, with steps and checks, and you never retype it |

**Anti-persona:** Someone who wants to avoid AI entirely. A developer who wants skills installed in a coding agent is served by the README's "For developers" section for now

## Switching Dynamics
**Push:** Tired of generic answers and of retyping instructions
**Pull:** One sentence, then named modes that do the work: almost magic
**Habit:** Typing free-form prompts, or relying on custom GPTs already built
**Anxiety:** "I'll break something", "this is for programmers"

## Customer Language
**How they describe the problem:**
- "the back-and-forth" (Pascal's words)
- "I spend more time explaining what I want than getting it" (draft, to validate with readers)
**How they describe us:**
- None yet
**Words to use:** skill, mode, playbook, paste, ask, steps, almost magic, back-and-forth, nothing to install
**Words to avoid:** terminal, CLI, repo, frontmatter, harness, compile, YAML. "Install" appears only in the developer section
**Glossary:**
| Term | Meaning |
|------|---------|
| Agent | The AI in your chat app |
| Skill | Written instructions the agent follows for one kind of task |
| Mode | A skill that opens a family of routes |
| Route | One task inside a mode, written after `;`, as in `corey-mode ; copywriting` |
| Playbook | The written steps of a route |

## Brand Voice
**Tone:** Warm, plain, confident, in Pascal's first person
**Style:** Short sentences, concrete examples, prompts to copy
**Personality:** Organized, practical, generous, curious, a little playful

## Proof Points
**Metrics:** 18 skills for non-developers out of 55, including 50 marketing playbooks in `corey-mode`
**Customers:** None yet
**Testimonials:** None yet
**Value themes:**
| Theme | Proof |
|-------|-------|
| Nothing to install | One sentence that points the agent to `docs/references/remote-skills-general.md` |
| Corporate experience | Pascal worked as a business analyst at Bell, National Bank, Desjardins, and BDC |
| Proven methods | Playbooks from Corey Haines, PStack, and Matt Pocock, adapted with credit |

## Goals
**Business goal:** Let anyone use Pascal's skills from a chat app, and show how much back-and-forth AI can remove
**Conversion action:** Paste the sentence and run a first skill, as in chapter 1 of the guide
**Current metrics:** Unknown

## Author
In Pascal's first person, as the README opens:

> I'm Pascal Andy, a business analyst. I've worked at Bell, National Bank, Desjardins, and BDC, so I know the corporate world and the traps worth avoiding. I like to organize things and to get leverage from technology, and skills are the natural next step. I spend my days thinking about how things work today so they work better tomorrow, and I spot the back-and-forth that an agent can take over. My goal is skills that feel almost like magic.

## Changelog
*Newest first. One line per revision: what changed and why.*
- v2 (2026-10-04) — Target audience: added Canadian French readers, served by docs/guide-fr-ca/.
- v1 (2026-10-04) — Initial context, drafted from the repository and Pascal's brief for the public guide.
