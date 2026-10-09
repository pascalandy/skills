---
description: "Build a page readers move through, such as a document turned into a guided reading page, or a journey with a map that follows the reading."
---

# Interactive page

Work at the level `SKILL.md` sets: Esquisse unless the user asked for a Livrable.

1. Use the brief for device, browser, window size, motion setting, brand assets and source fidelity. At Esquisse, list missing context as assumptions. At Livrable, ask only about missing context, at most four questions, including the QA count. Finish when each point has an answer or stated assumption.
2. Read `references/quality-bar.md`, then "Pages for readers" in `references/design.md`. Take the logo and colours from the source, and set the tokens before any component. Finish when the tokens exist in `:root`.
3. Build static content in reading order, then responsive layout, then interaction. For scroll-linked behaviour, read matching rows in `references/pitfalls.md`. Derive one reading position from `scrollY` and layout. If jumps need state, keep one active-jump record for all relevant events. Finish when every section, control and state exists.
4. Confirm `uv --version`; install missing `uv` from https://docs.astral.sh/uv/getting-started/installation/ within session permissions. From this skill's directory, run `uv run scripts/check_page.py <absolute page path>`; dependencies install on first run, and `--help` lists screens and browser setup. Inspect screenshots, fix findings, rerun. Finish when it answers `{"ok":true}`, or report unavailable checks.
5. Run the level's QA rounds as `references/qa-loop.md` describes, within session permissions. Finish when final fixes are verified and dismissals recorded in `QA.md`, or report the blocked QA rounds.
6. At the end of a Livrable, write a learning as `learnings/README.md` describes.

Return the page path, the level, the assumptions, the `check_page.py` answer, the rounds run with their journal, and the published URL when publication verified it.
