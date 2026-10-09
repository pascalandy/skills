---
description: "Build a page readers move through, such as a document turned into a guided reading page, or a journey with a map that follows the reading."
---

# Interactive page

Work at the level `SKILL.md` sets: Esquisse unless the user asked for a Livrable.

1. Gather the reviewer's context: their device, browser and window size, their motion setting, the brand assets, how faithful the text must stay to its source, and at Livrable the number of QA rounds. At Esquisse, ask nothing and list your assumptions for the handoff. At Livrable, ask one round of at most four questions. Finish when each point has an answer or a stated assumption.
2. Read `references/quality-bar.md`, then "Pages for readers" in `references/design.md`. Take the logo and colours from the source, and set the tokens before any component. Finish when the tokens exist in `:root`.
3. Build the content first, as static HTML in reading order, then the layout across the screens, then the interaction. Before any behaviour that follows the scroll, read `references/pitfalls.md`, and model one reading position from `scrollY` and the layout, with one record of the active jump that scroll, wheel, keys, resize, visibility and history all update. Finish when every section, control and state exists.
4. Confirm `uv --version`, and install `uv` from https://docs.astral.sh/uv/getting-started/installation/ when it is missing. From this skill's directory, run `uv run scripts/check_page.py <absolute page path>`; its dependencies install on the first run, and `--help` lists the screens and the browser setup. Look at its screenshots and fix each finding in its own commit. Finish when it answers `{"ok":true}`.
5. Run the level's QA rounds as `references/qa-loop.md` describes. Finish when the last round's findings are fixed or dismissed in `QA.md`.
6. At the end of a Livrable, write a learning as `learnings/README.md` describes.

Return the page path, the level, the assumptions, the `check_page.py` answer, the rounds run with their journal, and the published URL when publication verified it.
