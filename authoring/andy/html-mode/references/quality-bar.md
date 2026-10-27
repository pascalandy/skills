# Quality bar

For pages readers use, apply items only when their features exist. `scripts/check_page.py` samples _(checked)_ items. Inspect screenshots. Use QA for remaining states and limits.

QA checks form-field values and placeholders, which font-size and contrast checks omit.

For covered screens, run `uv run scripts/check_page.py --help`: phones, tablets in both orientations, laptop, and desktop.

## Layout and reading

- No sideways scroll _(checked)_ or cut-off text _(checked)_ on any screen
- Aim for 45 to 75 characters per line where width permits, about `40rem` at 17px
- Fill tall tablet screens with the composition
- End the page at its last content, without dead scroll or blank tail

## Type

- Phone text is at least 12px _(checked for CSS font sizes and SVG scaling; QA checks HTML transforms)_. Use 16px form fields to prevent iOS zoom
- Use `rem` for sizes and container query thresholds to respect browser text size
- Use one scale, at most 8 sizes and 4 weights. Line height 1.6 for text, 1.15 for titles
- Headings `text-wrap: balance`, paragraphs `text-wrap: pretty`
- French typography: non-breaking spaces before `:` `;` `!` `?`, inside `« »`, between a number and its unit, and within a brand name where needed
- Fit long words at every width without mid-word breaks

## Colour and themes

- Text contrast 4.5:1, or 3:1 from 24px or 18.66px bold _(checked, except SVG text and text over an image)_; graphics and focus rings 3:1. For third-party reproductions, apply [Workflow step 5](../SKILL.md#workflow)
- Define colours once as `light-dark()` tokens in `:root`. Support browsers without `light-dark()`
- Use warm near-black dark surfaces, off-white text, and lighter accents for contrast. Deepen saturated blocks that glare in dark mode
- Switch every colour at once
- Use two `theme-color` metas, one per `prefers-color-scheme`. The switch sets both to the chosen theme
- Print in light, regardless of theme
- Under `forced-colors: active`, state colours map to `Highlight`, `CanvasText` and `GrayText`

## Controls and touch

- Use 44px touch hit areas, except controls inside running text _(checked by sampled hit testing, including labels, padding and pseudo-elements)_
- Nothing covers a control _(checked at sampled target centres on touch screens; QA checks other states)_
- Put hover styles inside `@media (hover: hover)`. Reveal hover content on focus and tap too
- `touch-action: manipulation` on buttons tapped in quick succession
- Inline controls wrap with their sentences inside their boxes

## Keyboard and screen readers

- Show focus at every stop, never hidden by sticky bars _(checked for up to 60 stops on one screen per scheme; QA covers the rest)_
- `aria-current="step"` on the current step of a journey, `aria-expanded` on what opens and closes
- Announce each change once, through focus on the new heading or `aria-live`, never both
- Every section has a heading, every icon button a name, foreign text its `lang`
- Preserve copied word spacing and exclude decorative glyphs

## Motion

- Under `prefers-reduced-motion: reduce`, show the finished state with no continuing motion _(checked)_
- No continuous drawing at rest _(checked for animation-frame callbacks and infinite CSS animations; QA checks timers, canvas and video)_; sampled scroll frames stay under 50ms _(checked)_
- Use native `scrollTo({ behavior: 'smooth' })` for jumps

## Loading and head

- No requests to another host _(checked)_. Inline fonts and images
- Hide the page until font load, 400ms at most. No font swap or layout shift
- `<meta name="viewport" content="width=device-width, initial-scale=1">` without `viewport-fit=cover`, `color-scheme`, a title, a description, `og:` tags and an icon
- Without JavaScript, show title, one line, and a link in `<noscript>`

## Robustness

- Keep the reading line in place through zoom, rotation, and window resize
- Deep links reach their targets. Back and Forward restore position. Back-forward cache restores state
- After hiding a tab during animation, resume without a visible jump
- From mid-page, print the whole page and return to the same position
