# Quality bar

Read when building or reviewing a page a reader will use. Items marked _(checked)_ fail `scripts/check_page.py`; the others are checked by eye on its screenshots and by the QA loop.

Run `uv run scripts/check_page.py --help` for the screens it covers: phones, tablets in both orientations, a laptop and a desktop.

## Layout and reading

- No sideways scroll on any screen _(checked)_, and no text cut off _(checked)_
- Running text keeps 45 to 75 characters per line, about `40rem` at 17px, on every width, including the band where a side panel first appears
- A tall tablet screen is filled by the composition, not a small block in its middle
- The page ends with its last content: no dead scroll and no blank tail

## Type

- Text on a phone is 12px or larger _(checked)_, form fields 16px so iOS does not zoom
- Sizes in `rem`, so the browser's text size setting applies; container query thresholds in `rem` too
- One scale: at most 8 sizes and 4 weights, line height 1.6 for text and 1.15 for titles
- Headings `text-wrap: balance`, paragraphs `text-wrap: pretty`
- French typography: a non-breaking space before `:` `;` `!` `?`, inside `« »`, between a number and its unit, and inside a brand name
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

- Hit areas of 44px on touch screens, except links inside running text _(checked by hit testing, so padding and pseudo-elements count)_
- Nothing covers a control _(checked)_
- Hover styles inside `@media (hover: hover)`; what hover reveals also shows on focus and on tap
- `touch-action: manipulation` on buttons tapped in quick succession
- An inline control wraps with its sentence and stays inside its box

## Keyboard and screen readers

- Visible focus on every stop _(checked)_, never hidden under a sticky bar
- `aria-current="step"` on the current step of a journey, `aria-expanded` on what opens and closes
- One announcement per change: focus moves to the new heading, or `aria-live` speaks, not both
- Every section has a heading, every icon button a name, foreign text its `lang`
- Copied text keeps its word spacing, and decorative glyphs stay out of it

## Motion

- Under `prefers-reduced-motion: reduce`, the page shows its finished state and nothing keeps moving _(checked)_
- Nothing draws at rest _(checked)_; scroll frames stay under 50ms _(checked)_
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
