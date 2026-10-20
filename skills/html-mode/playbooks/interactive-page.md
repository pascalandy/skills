---
description: "Build pages readers move through, such as guided reading pages from documents or journeys with maps that follow reading."
---

# Interactive page

Use the level from `SKILL.md`.

1. Check the brief for device, browser, window size, motion setting, brand assets, and source fidelity. At Esquisse, state missing context as assumptions. At Livrable, ask at most four questions about missing context, including the QA count. Finish when each point has an answer or assumption.
2. Read `references/quality-bar.md`, then "Pages for readers" in `references/design.md`. Set tokens in `:root` before components. Finish when the logo and colours match the source.
3. Build static content in reading order, then responsive layout, then interaction. For scroll-linked behaviour, read matching rows in `references/pitfalls.md`. Derive one reading position from `scrollY` and layout. If jumps need state, keep one active-jump record for all relevant events. Finish when every section, control, and state exists.
4. Run `check_page.py` as `SKILL.md` step 5 says. Inspect screenshots, fix findings, and rerun. Finish when `check_page.py` answers `{"ok":true}`, or report unavailable checks.
5. Within session permissions, run the level's QA rounds per `references/qa-loop.md`. Finish when final fixes are verified and dismissals recorded in `QA.md`, or report blocked rounds.

Return page path, level, assumptions, `check_page.py` answer, rounds run, journal, and any verified publication URL.
