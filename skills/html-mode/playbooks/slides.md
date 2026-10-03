---
description: "Build an HTML slide deck with reveal.js that tells one story a screen at a time."
---

# Slides

Use this playbook only for presentations delivered as HTML. PowerPoint, Google Slides, and other presentation formats keep their own workflows.

Current reveal.js pin: `6.0.2`.

1. Define the audience, presenting context, takeaway, and story arc. Give each slide one job and one dominant idea. Decide which details must stay visible together and which earn a fragment. Finish when the deck has a deliberate sequence rather than a document split into screens.
2. Copy [the slides template](../assets/slides-template.html) as the output file. Replace its sample content, document title, language, and deck label. Keep the exact reveal.js pin, core styles, visible controls, progress, slide numbers, hashes, keyboard and touch navigation, mobile scroll view, and reduced-motion configuration. A reveal.js CDN dependency is already authorized for this playbook; do not ask again. Finish when one `.html` file opens directly without a build step and every slide has a stable ID.
3. Shape the deck for the room and the reader. Keep essential meaning available without hover, contain code and wide content, use fragments only to control explanation order, and preserve the shared theme, accessibility, and motion contract from `SKILL.md`. Finish when the fixed stage works on desktop and the automatic scroll view remains readable at narrow widths.
4. Load optional plugins only when the requested content uses them. Keep every plugin on the same reveal.js pin as core. Finish when the initialization array contains exactly the plugins supported by content in the file.
5. Open the real file in a browser and run the verification below in addition to the shared checks. Fix observed failures. Finish when navigation, boundaries, progress, direct links, fragments, responsive reading, and any enabled plugin work without console or network errors.

## Optional plugins

For syntax-highlighted code, add both `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/highlight/monokai.css` and `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/highlight.js`, then register `RevealHighlight`. Use `data-line-numbers` only when stepping through specific lines improves the explanation.

For speaker notes, add `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/notes.js`, register `RevealNotes`, and put notes in `<aside class="notes">`. The speaker window requires a local web server for local use; opening the file directly is not enough. Serve the output directory, open its HTTP URL, and press `S`. Do not promise speaker view unless that environment was tested.

Fragments need no plugin. Apply `class="fragment"` to content that should appear progressively and keep the DOM order meaningful when every fragment is visible.

## Verification

- Confirm the exact CDN files load and all reveal.js core and plugin URLs use `6.0.2`
- Use the visible controls and keyboard to move from the first slide to the last and back; confirm navigation stops at both boundaries
- Confirm the progress bar and `current/total` slide number update
- Open a stable `#/slide-id` URL directly and reload it
- Step forward and backward through every fragment sequence before leaving its slide
- Inspect wide desktop and narrow mobile widths; confirm narrow screens activate a readable scroll view without page-level horizontal overflow
- Tab through links and controls, inspect visible focus, and emulate reduced motion when transitions or auto-animation exist
- When code highlighting or notes are enabled, test the plugin behavior and its documented environment

Return the deck's absolute path, slide count, optional plugins loaded, and any browser behavior that could not be verified.
