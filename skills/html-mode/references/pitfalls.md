# Pitfalls

Read rows matching a planned feature or observed defect. Confirm the cause before applying a fix. These fixes came from one page; they are not requirements for every page.

## The reviewer and the environment

| Symptom | Cause | Fix |
| --- | --- | --- |
| The reviewer calls a motion "dry", then "weird" after a rework | Their system has Reduce motion on, so they never saw it | Ask for their device, browser, window size and motion setting before tuning motion |
| Fine in Chromium, unknown on iPhone | WebKit never ran | Run `check_page.py --browser webkit` on a Mac |
| A finding cannot be reproduced | The reviewer tested the working file while it changed | Test a pushed commit, served from git |

## A scroll-synced indicator (a marker on a map, a rail, a progress bar)

| Symptom | Cause | Fix |
| --- | --- | --- |
| Each fix opens a new bug: a stuck jump, a recoil after a resize, a jump after a hidden tab | Separate states patched one by one: spring, jump, interrupted jump, anchor, fade | Model one reading position from `scrollY` and the layout, plus one record of the active jump that every event updates |
| The marker teleports during a click jump | It follows the section under the reading line, and the smooth scroll crosses several | During a jump, move the marker from start to target by the scrolled fraction |
| A jump never ends | The page can stop without a scroll event | End on target reached, timeout, or no movement; poll with `requestAnimationFrame` only while a jump runs |
| The marker slows at every stop | The spring runs in stop units, so its speed scales with each gap | Run the spring in pixels or path length |
| A long task on load | Nearest-point search on an SVG path at full resolution | Search coarse, then fine around the best sample |
| Frames run at rest | The animation loop stays armed | Request a frame only while something moves |
| The marker hides the stop it sits on and takes its taps | It is drawn above the stops | `pointer-events: none` on the marker; a ring in the stop's colour when it covers it |
| The marker reaches the end but a strip of track stays grey | The filled line stops at the marker's centre | Past the last stop, let the line gain on the marker until it touches the end |

## Navigation and history

| Symptom | Cause | Fix |
| --- | --- | --- |
| Back lands in the wrong place | The `popstate` handler scrolls where the browser already restores | Mark your own `pushState` entries; on `popstate`, act only on entries without the mark, such as a typed hash |
| A deep link lands, then jumps | A resize or the font load reruns the scroll during startup | Read the hash once, keep the page hidden until the font is ready (400ms at most), update nothing before a `ready` flag |
| The address flickers through every section during a jump | `replaceState` on each scroll | Freeze the address while a jump runs |

## Resize, zoom and rotation

| Symptom | Cause | Fix |
| --- | --- | --- |
| Zoom loses the line being read | A `vw`-based padding on an ancestor changes with every width, which suspends native scroll anchoring | Remember the text block under the reading line once scrolling settles, with the share already read, and put it back when the width changes |
| The page snaps back to an old place | The anchor predates a jump or a scroll | Retake the anchor when a jump ends; compare it with the last position a scroll event saw, since the browser may clamp `scrollY` before the resize handler runs |
| A second zoom step drifts | The page retook its anchor from the scroll it caused itself | Ignore only the echo of your own scroll, at the exact position you set |
| The anchor lands on the wrong block | The reading line falls in a margin or between two columns | Anchor text blocks only; probe below the line and across the column |
| The page jumps while scrolling on a phone | The address bar changes the height and fires `resize` | Act only when the width changes |
| A rotation during a jump lands beside the target | The target and the sticky bar height come from the old layout | On a width change during a jump, measure the bar, then retarget |

## Sticky bars and side panels

| Symptom | Cause | Fix |
| --- | --- | --- |
| A title lands under the sticky bar at a larger text size | `scroll-margin-top` uses a fixed bar height | Measure the bar with `ResizeObserver` into a CSS variable |
| A tall tablet shows a small map in a big panel | The panel's width limits the drawing | Use the top bar on a touch screen in portrait (`(orientation: portrait) and (hover: none)`) |
| A long name in a flex bar is cut without an ellipsis | `text-overflow` applies to the flex item's own text | Put `min-width: 0`, `overflow: hidden` and the ellipsis on the item that holds the text |

## Popovers and inline terms

| Symptom | Cause | Fix |
| --- | --- | --- |
| A term breaks out of its box on a phone | A `<button>` inside a `nowrap` group: the button is an inline block | Use an inline `<span role="button" tabindex="0">` that Enter and Space activate; glue its punctuation with non-breaking spaces |
| The popover opens beside a term split over two lines | It is placed from the bounding box | Place it under the last rect of `getClientRects()`, or above the first |
| A popover stays open after Tab | Nothing closes it when focus leaves | Close on `focusout`, unless focus moves into the popover |

## Type

| Symptom | Cause | Fix |
| --- | --- | --- |
| A long title word spills out of a narrow card | The size floor of `clamp()` ignores the card's width | Cap the size with `cqi` of the column |
| `overflow-wrap` breaks a word mid-syllable | Chromium on Linux has no French hyphenation dictionary | Size the text to fit instead of relying on hyphenation |
| `cqi` sizes come out too small | `cqi` measures the content box, without padding | Compute the factor from the content width |
| A `cqi` size follows the wrong box | Units resolve against the nearest eligible size container, regardless of its name | Check the nearest container's axis and width; names such as `container: text / inline-size` do not select which box units use |
| A number and its unit split across lines | A plain space | Insert a non-breaking space in the text escaping function |
| Copied text reads `Step 2 :Name` | The space ending a visually hidden span is dropped | End the hidden text with a non-breaking space |
| A decorative arrow is copied | It stays selectable | `-webkit-user-select: none; user-select: none` |

## Themes and colour

| Symptom | Cause | Fix |
| --- | --- | --- |
| On a theme switch, one block lags in the old theme | Each element runs its own colour transition | Turn transitions off for one frame during the switch |
| Every colour is missing on an older iPhone | `light-dark()` exists from Safari 17.5 | Add a `@supports not (color: light-dark(#000, #fff))` fallback built from the tokens |
| A contrast script reports nonsense | Chromium serializes mixed colours as `color(srgb …)` | Read colours through a 1×1 canvas pixel |

## The test bench

| Symptom | Cause | Fix |
| --- | --- | --- |
| Back and Forward never restore from cache | Playwright disables the back-forward cache by default | Launch without `--disable-back-forward-cache` to test it |
| Frame timings spike for no reason | Two benches ran on the same machine | Run one timing benchmark at a time |
| A test reads a state mid-animation | A fixed timeout | Wait for a condition, such as the hash and the title position |
| The coordinator times out waiting for QA | The QA agent handed its bench to a background job and ended its turn | The QA agent finishes its round within its turn |
