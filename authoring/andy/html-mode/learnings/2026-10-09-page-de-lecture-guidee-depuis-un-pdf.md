# A guided reading page built from a client's PDF

## The use case

A client's PDF described a five-stage onboarding journey. It became one standalone page for the client's own customers:

- the text verbatim
- a map of the journey beside the text, with a marker that follows the reading
- a ticket as the title of each stage
- a glossary with inline definitions
- light and dark themes, published privately

## What it took

- 14 QA rounds over about 12 hours, 103 findings: 4 dismissed, 1 left to the reviewer
- One QA thread covered every axis at once, and each round took 40 to 60 minutes
- Smoothness never failed: no frame over 25 ms in any round. The findings were design, accessibility and robustness
- Commits went change by change before the loop, then one per round, which hid the history of each fix

## Root causes

1. The reviewer's machine had Reduce motion on, so two rounds of motion design went unseen
2. The page started without a quality bar. Spacing, durations, the type scale, focus, 12px text and 44px targets surfaced one round at a time
3. The scroll machinery grew patch by patch, and each fix added a state that the next round broke
4. Nothing checked the page before a QA round, so every round paid for checks a machine could run
5. Safari never ran, although the reviewer reads on Apple devices
6. Type first stood in for the logo, and a round was spent replacing it with a trace of the source

## Where each lesson went

| Lesson | Home |
| --- | --- |
| Ask about the reviewer's device, browser, window and motion setting first | `playbooks/interactive-page.md`, intake; `references/pitfalls.md`, the reviewer |
| Start from a bar | `references/quality-bar.md` |
| Run machine checks before a QA round | `scripts/check_page.py`; `references/qa-loop.md`, A's round |
| Model one reading position and one active jump | `references/pitfalls.md`, scroll-synced indicator; `playbooks/interactive-page.md`, build order |
| Test Safari | `check_page.py --browser webkit`; `references/qa-loop.md`, axes |
| Take the brand from the source | `references/design.md`, pages for readers |
| Split QA by axis, in threads, on one pushed commit | `references/qa-loop.md` |
| Commit each change | `references/qa-loop.md`, A's round |
| Scale QA to the level, and never name the client | `SKILL.md` |
