# Quality bar

Read when building or reviewing a page for readers. Items marked _(checked)_ are sampled by `scripts/check_page.py`. Inspect screenshots and use QA for remaining states and limits below. Apply feature-specific items only when that feature exists.

The font-size and contrast checks omit form-field values and placeholders, which QA checks.

Run `uv run scripts/check_page.py --help` for the screens it covers: phones, tablets in both orientations, a laptop and a desktop.

## Layout and reading

- No sideways scroll on any screen _(checked)_, and no text cut off _(checked)_
- Aim for 45 to 75 characters per line where width permits, about `40rem` at 17px. On narrow screens, fit text without sideways scroll
- A tall tablet screen is filled by the composition, not a small block in its middle
- The page ends with its last content: no dead scroll and no blank tail

## Type

- Text on a phone is 12px or larger _(checked for CSS font sizes and SVG scaling; QA checks HTML transforms)_. Form fields use 16px so iOS does not zoom
- Sizes in `rem`, so the browser's text size setting applies; container query thresholds in `rem` too
- One scale: at most 8 sizes and 4 weights, line height 1.6 for text and 1.15 for titles
- Headings `text-wrap: balance`, paragraphs `text-wrap: pretty`
- French typography: non-breaking spaces before `:` `;` `!` `?`, inside `« »`, between a number and its unit, and within a brand name where needed
- A long word fits its box at every width, without breaking mid-word

## Colour and themes

- Text contrast 4.5:1, or 3:1 from 24px or 18.66px bold _(checked, except SVG text and text over an image)_; graphics and focus rings 3:1
- Colours written once as `light-dark()` tokens in `:root`, and still present in browsers without `light-dark()`
- Dark mode is a designed palette: warm near-black surfaces, off-white text, accents lifted for contrast. A saturated block that reads well in light can glare in dark; give it a deeper shade
- The theme switch changes every colour at once
- Two `theme-color` metas, one per `prefers-color-scheme`, both set to the chosen theme by the switch
- Printing is light, whatever the theme
- Under `forced-colors: active`, state colours map to `Highlight`, `CanvasText` and `GrayText`

## Controls and touch

- Hit areas of 44px on touch screens, except controls inside running text _(checked by sampled hit testing, including labels, padding and pseudo-elements)_
- Nothing covers a control _(checked at sampled target centres on touch screens; QA checks other states)_
- Hover styles inside `@media (hover: hover)`; what hover reveals also shows on focus and on tap
- `touch-action: manipulation` on buttons tapped in quick succession
- An inline control wraps with its sentence and stays inside its box

## Keyboard and screen readers

- Visible focus on every stop, never hidden under a sticky bar _(checked for up to 60 stops on one screen per scheme; QA covers the rest)_
- `aria-current="step"` on the current step of a journey, `aria-expanded` on what opens and closes
- One announcement per change: focus moves to the new heading, or `aria-live` speaks, not both
- Every section has a heading, every icon button a name, foreign text its `lang`
- Copied text keeps its word spacing, and decorative glyphs stay out of it

## Motion

- Under `prefers-reduced-motion: reduce`, the page shows its finished state and nothing keeps moving _(checked)_
- No continuous drawing at rest _(checked for animation-frame callbacks and infinite CSS animations; QA checks timers, canvas and video)_; sampled scroll frames stay under 50ms _(checked)_
- Native `scrollTo({ behavior: 'smooth' })` for jumps; a custom glide feels wrong to readers used to their browser

## Loading and head

- Self-contained: no request to another host _(checked)_, fonts and images inline
- The page stays hidden until its font loads, 400ms at most: no font swap and no layout shift
- `<meta name="viewport" content="width=device-width, initial-scale=1">` without `viewport-fit=cover`, `color-scheme`, a title, a description, `og:` tags and an icon
- Without JavaScript, a `<noscript>` block shows the title, a line and a link

## Robustness

- Zoom, rotation and window resizes keep the line being read in place
- A deep link lands on its target; Back and Forward restore the position; a page restored from the back-forward cache keeps its state
- A tab hidden during an animation resumes without a visible jump
- Printing from mid-page prints the whole page and returns to the same place
