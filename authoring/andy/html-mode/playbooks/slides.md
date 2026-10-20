---
description: "Build an HTML slide deck with reveal.js that tells one story a screen at a time."
---

# Slides

For non-HTML presentations, use their workflows.

Current reveal.js pin: `6.0.2`.

1. Define audience, presenting context, takeaway, and story arc. Give each slide one job and one dominant idea. Decide which details stay visible together and which need fragments. Finish when the sequence tells the story, not a document split into screens.
2. Copy [the slides template](../assets/slides-template.html) as the output file. Replace sample content, document title, language, and deck label. Keep the exact reveal.js pin, core styles, visible controls, progress, slide numbers, and hashes. Keep keyboard and touch navigation, mobile scroll view, and reduced-motion configuration. The reveal.js CDN dependency is authorized. Finish when one `.html` file opens without a build step and every slide has a stable ID.
3. Fit the deck to the room and reader. Keep essential meaning available without hover. Contain code and wide content. Use fragments only for explanation order. Apply the shared theme, accessibility, and motion contract from `SKILL.md`. Finish when the fixed stage works on desktop and automatic scroll view is readable at narrow widths.
4. Load optional plugins only when requested content uses them. Use the core reveal.js pin for every plugin. Finish when the initialization array matches the plugins used by the file's content.
5. In a browser, run the checks below and shared verification on the file. Fix failures. Finish when navigation, boundaries, progress, direct links, fragments, responsive reading, and enabled plugins work without console or network errors.

## Optional plugins

For syntax-highlighted code, add `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/highlight/monokai.css` and `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/highlight.js`. Register `RevealHighlight`. Use `data-line-numbers` only when steps through specific lines improve the explanation.

For speaker notes, add `https://cdn.jsdelivr.net/npm/reveal.js@6.0.2/dist/plugin/notes.js` and register `RevealNotes`. Put notes in `<aside class="notes">`. For local speaker view, serve the output directory through a local web server. Open its HTTP URL and press `S`. Promise speaker view only after testing that environment.

For progressive content, apply `class="fragment"`. No plugin is needed. Keep DOM order meaningful with all fragments visible.

## Verification

- Confirm the exact CDN files load and all reveal.js core and plugin URLs use `6.0.2`
- Use visible controls and keyboard from first slide to last and back. Confirm navigation stops at both boundaries
- Confirm the progress bar and `current/total` slide number update
- Open a stable `#/slide-id` URL directly and reload it
- Step forward and backward through every fragment sequence before leaving its slide
- Inspect wide desktop and narrow mobile widths. Confirm narrow screens activate readable scroll view without horizontal page overflow
- Tab through links and controls. Inspect visible focus. For transitions or auto-animation, emulate reduced motion
- If code highlighting or notes are enabled, test the plugin and its required environment

Return absolute deck path, slide count, loaded plugins, and unverified browser behavior.
