# A guided reading page built from a client's PDF

## The use case

A client's five-stage onboarding PDF became one standalone page for that client's customers:

- the text verbatim
- a journey map beside the text, with a marker following the reading
- a ticket title for each stage
- a glossary of inline definitions
- light and dark themes, published privately

## What it took

- 14 QA rounds over about 12 hours, 103 findings: 4 dismissed, 1 left to the reviewer
- One QA thread covered every axis. Each round took 40 to 60 minutes
- Smoothness never failed, with no frame over 25 ms. Findings concerned design, accessibility, and robustness
- Commits were per change before the loop, then per round, hiding each fix's history

## Root causes

1. Reduce motion hid two rounds of motion design from the reviewer
2. No initial quality bar. Spacing, durations, type scale, focus, 12px text, and 44px targets surfaced one round at a time
3. Each scroll fix added a state that failed in the next round
4. No checks ran before QA rounds, so each repeated work a machine could do
5. Safari never ran, although the reviewer uses Apple devices
6. Type initially replaced the logo. Tracing the source logo took a round

## Where each lesson went

| Lesson | Home |
| --- | --- |
| Ask first about device, browser, window, and motion setting | `playbooks/interactive-page.md`, intake; `references/pitfalls.md`, the reviewer |
| Start with a quality bar | `references/quality-bar.md` |
| Run machine checks before a QA round | `scripts/check_page.py`; `references/qa-loop.md`, A's round |
| Model one reading position and one active jump | `references/pitfalls.md`, scroll-synced indicator; `playbooks/interactive-page.md`, build order |
| Test Safari | `check_page.py --browser webkit`; `references/qa-loop.md`, axes |
| Take the brand from the source | `references/design.md`, pages for readers |
| Split QA by axis into threads on one pushed commit | `references/qa-loop.md` |
| Commit each change | `references/qa-loop.md`, A's round |
| Scale QA to the level, and never name the client | `SKILL.md` |
