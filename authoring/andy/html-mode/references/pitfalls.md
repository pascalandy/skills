# Pitfalls

Read matching features or defects. Confirm the cause before fixing. These fixes came from one page. Apply only where relevant.

## The reviewer and the environment

| Symptom | Cause | Fix |
| --- | --- | --- |
| Reviewer calls motion "dry", then "weird" after rework | Reduce motion hid the motion | Before tuning, ask for device, browser, window size, and motion setting |
| Fine in Chromium, unknown on iPhone | WebKit never ran | Run `check_page.py --browser webkit` on a Mac |
| Finding cannot be reproduced | Reviewer tested a changing working file | Test a pushed commit, served from git |

## A scroll-synced indicator (a marker on a map, a rail, a progress bar)

| Symptom | Cause | Fix |
| --- | --- | --- |
| Fixes cause stuck jumps, recoil after resize, or jumps after a hidden tab | Separately patched states: spring, jump, interrupted jump, anchor, fade | Derive one reading position from `scrollY` and layout. Keep one active-jump record that every event updates |
| Marker teleports during click jumps | Smooth scroll crosses several sections under the reading line | During jumps, move the marker from start to target by the scrolled fraction |
| Jump never ends | Page can stop without a scroll event | End on target, timeout, or no movement. Poll with `requestAnimationFrame` only during jumps |
| Marker slows at each stop | Spring uses stop units, so speed scales with each gap | Run the spring in pixels or path length |
| Long task on load | Full-resolution nearest-point search on an SVG path | Search coarse, then fine around the best sample |
| Frames run at rest | Animation loop stays armed | Request frames only while something moves |
| Marker hides a stop and intercepts taps | Marker is above stops | Set `pointer-events: none` on the marker. When covering a stop, add a ring in that stop's colour |
| Marker reaches the end but track stays partly grey | Filled line stops at marker's centre | Past the last stop, advance the line faster than the marker until it reaches the end |

## Navigation and history

| Symptom | Cause | Fix |
| --- | --- | --- |
| Back lands incorrectly | `popstate` scrolls where the browser already restores | Mark your `pushState` entries. On `popstate`, act only on unmarked entries, such as typed hashes |
| Deep link lands, then jumps | Resize or font load reruns startup scroll | Read the hash once. Hide the page until font load, 400ms at most. Update nothing before a `ready` flag |
| Address flickers through sections during jumps | `replaceState` on each scroll | Freeze the address during jumps |

## Resize, zoom and rotation

| Symptom | Cause | Fix |
| --- | --- | --- |
| Zoom loses the reading line | Ancestor `vw` padding changes with width and suspends native scroll anchoring | Once scrolling settles, record the text block under the reading line and fraction read. Restore on width change |
| Page returns to an old position | Anchor predates a jump or scroll | After jumps, retake the anchor. Compare with the last scroll-event position. The browser may clamp `scrollY` before resize handling |
| Second zoom step drifts | Page retook the anchor after its own scroll | Ignore only your scroll's echo, at the exact position you set |
| Anchor lands on the wrong block | Reading line falls in a margin or between columns | Anchor text blocks only. Probe below the line and across the column |
| Page jumps during phone scrolling | Address bar changes height and fires `resize` | Act only on width changes |
| Rotation during a jump misses target | Target and sticky bar height use the old layout | On width change during jumps, measure the bar, then retarget |

## Sticky bars and side panels

| Symptom | Cause | Fix |
| --- | --- | --- |
| At larger text sizes, title lands under sticky bar | `scroll-margin-top` uses fixed bar height | Measure the bar with `ResizeObserver` into a CSS variable |
| Tall tablet shows a small map in a large panel | Panel width limits drawing | On portrait touch screens, use the top bar: `(orientation: portrait) and (hover: none)` |
| Long name in a flex bar is cut without ellipsis | `text-overflow` applies to the flex item's own text | Put `min-width: 0`, `overflow: hidden`, and ellipsis on the text's item |

## Popovers and inline terms

| Symptom | Cause | Fix |
| --- | --- | --- |
| Term escapes its box on phones | `<button>` is an inline block inside a `nowrap` group | Use inline `<span role="button" tabindex="0">` activated by Enter and Space. Attach punctuation with non-breaking spaces |
| Popover opens beside a two-line term | Position uses bounding box | Place below the last rect of `getClientRects()`, or above the first |
| Popover stays open after Tab | Focus leaving does not close it | Close on `focusout`, unless focus enters the popover |

## Type

| Symptom | Cause | Fix |
| --- | --- | --- |
| Long title word escapes a narrow card | `clamp()` floor ignores card width | Cap size with the column's `cqi` |
| `overflow-wrap` breaks words mid-syllable | Chromium on Linux lacks French hyphenation dictionary | Size text to fit without hyphenation |
| `cqi` sizes are too small | `cqi` measures content without padding | Compute the factor from content width |
| `cqi` follows the wrong box | Units use the nearest eligible size container, regardless of name | Check nearest container's axis and width. Names such as `container: text / inline-size` do not select the box |
| Number and unit split across lines | Plain space | Insert a non-breaking space in the text escaping function |
| Copied text reads `Step 2 :Name` | Trailing space in a visually hidden span is dropped | End hidden text with a non-breaking space |
| Decorative arrow is copied | Arrow remains selectable | `-webkit-user-select: none; user-select: none` |

## Themes and colour

| Symptom | Cause | Fix |
| --- | --- | --- |
| Block retains old theme during switch | Elements run separate colour transitions | Disable transitions for one frame during the switch |
| Colours missing on older iPhones | Safari supports `light-dark()` from 17.5 | Add a token-based `@supports not (color: light-dark(#000, #fff))` fallback |
| Contrast script reports nonsense | Chromium serializes mixed colours as `color(srgb …)` | Read colours through a 1×1 canvas pixel |

## The test bench

| Symptom | Cause | Fix |
| --- | --- | --- |
| Back and Forward never restore from cache | Playwright disables back-forward cache by default | To test, launch without `--disable-back-forward-cache` |
| Frame timings spike | Two benches ran on one machine | Run one timing benchmark at a time |
| Test reads state mid-animation | Fixed timeout | Wait for a condition, such as hash and title position |
| Coordinator times out waiting for QA | QA agent ended its turn with a background bench running | QA agent finishes its round within its turn |
