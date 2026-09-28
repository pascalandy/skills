> Frozen research record, 2026-09-28. The results GPT-6 Astra (medium reasoning) wrote after running the plan in [astra-test-prompt.md](astra-test-prompt.md), finished 2026-09-28T13:12Z. Everything below the rule is unedited: links to `/tmp` and `/home/pascal` pointed to working files that were not preserved. The tests ran through Codex's built-in image tool, which requests `gpt-image-2` at settings the plan backend fixes (OpenAI's Codex docs say the same), and no output was independently verified as GPT Image 2.5, so they count as prompt-behavior evidence; see [verification.md](verification.md#6-the-codex-plan-path). Index: [README](README.md).

---

# Built-in image generation test results

Run date: 2026-09-28. All 17 calls used the built-in `image_gen` tool with the supplied prompts verbatim. T02a used real line breaks. No CLI/API fallback, API parameters, retries, or generation errors occurred. Every output was copied from the tool's saved path and inspected with `view_image`.

The tool did not disclose its model, so this run cannot independently confirm the name "GPT Image 2.5". Verdicts describe this run, not population-level reliability.

| Test | Image file | Dimensions | Mode | Bytes | Seconds | Hypothesis verdict | Evidence |
|---|---|---|---|---:|---:|---|---|
| T01a | [images/T01a-minimal-lighthouse.png](/tmp/gpt-image-25-tests/images/T01a-minimal-lighthouse.png) | 1145×1374 | RGB | 2,489,755 | 58.050 | PARTIAL | Composition and blue hour obeyed; additional warm accents remain |
| T01b | [images/T01b-specified-lighthouse.png](/tmp/gpt-image-25-tests/images/T01b-specified-lighthouse.png) | 1145×1374 | RGB | 2,259,270 | 47.795 | PARTIAL | Composition and blue hour obeyed; additional warm accents remain |
| T02a | [images/T02a-sectioned-teapot.png](/tmp/gpt-image-25-tests/images/T02a-sectioned-teapot.png) | 1254×1254 | RGB | 1,806,174 | 39.236 | PASS | Both formats satisfy 8/8 visual requirements |
| T02b | [images/T02b-paragraph-teapot.png](/tmp/gpt-image-25-tests/images/T02b-paragraph-teapot.png) | 1254×1254 | RGB | 1,885,920 | 44.936 | PASS | Both formats satisfy 8/8 visual requirements |
| T03 | [images/T03-bakery-text.png](/tmp/gpt-image-25-tests/images/T03-bakery-text.png) | 1145×1374 | RGB | 1,093,743 | 32.625 | PASS | Both accented strings appear exactly once |
| T04 | [images/T04-revenue-slide.png](/tmp/gpt-image-25-tests/images/T04-revenue-slide.png) | 1672×941 | RGB | 845,775 | 39.495 | PARTIAL | All chart text and data correct; small-text weakness not demonstrated |
| T05a | [images/T05a-wide-lavender.png](/tmp/gpt-image-25-tests/images/T05a-wide-lavender.png) | 1672×941 | RGB | 2,582,909 | 23.810 | PASS | Both 1672×941; explicit 4K request not honored |
| T05b | [images/T05b-4k-lavender.png](/tmp/gpt-image-25-tests/images/T05b-4k-lavender.png) | 1672×941 | RGB | 2,689,653 | 32.928 | PASS | Both 1672×941; explicit 4K request not honored |
| T06 | [images/T06-transparent-fox.png](/tmp/gpt-image-25-tests/images/T06-transparent-fox.png) | 1145×1374 | RGBA | 969,525 | 44.240 | PARTIAL | Real alpha, but residual pixels and imperfect opacity |
| T07 | [images/T07-fisherman.png](/tmp/gpt-image-25-tests/images/T07-fisherman.png) | 1536×1024 | RGB | 2,147,322 | 29.999 | PARTIAL | Natural texture and framing; full finger count occluded |
| T08 | [images/T08-cyclist.png](/tmp/gpt-image-25-tests/images/T08-cyclist.png) | 1370×1148 | RGB | 2,210,500 | 33.036 | PASS | Full body, pedal contact, handlebar grips, forward gaze |
| T09a | [images/T09a-snow-edit.png](/tmp/gpt-image-25-tests/images/T09a-snow-edit.png) | 1536×1024 | RGB | 2,413,531 | 25.005 | PARTIAL | Identity and framing retained; unrelated details also change |
| T09b | [images/T09b-blue-net-edit.png](/tmp/gpt-image-25-tests/images/T09b-blue-net-edit.png) | 1536×1024 | RGB | 2,248,360 | 46.059 | PARTIAL | Identity and framing retained; unrelated details also change |
| T10 | [images/T10-fox-composite.png](/tmp/gpt-image-25-tests/images/T10-fox-composite.png) | 1145×1374 | RGB | 2,209,163 | 28.142 | PARTIAL | Pose and scene retained; fox lighting and proportions differ |
| T11a | [images/T11a-owl-reference.png](/tmp/gpt-image-25-tests/images/T11a-owl-reference.png) | 1536×1024 | RGB | 2,348,359 | 21.912 | PASS | All defining details and style retained, using viewer-left |
| T11b | [images/T11b-owl-reading.png](/tmp/gpt-image-25-tests/images/T11b-owl-reading.png) | 1536×1024 | RGB | 3,144,937 | 29.284 | PASS | All defining details and style retained, using viewer-left |
| T12 | [images/T12-black-mug.png](/tmp/gpt-image-25-tests/images/T12-black-mug.png) | 1370×1148 | RGB | 1,511,802 | 21.270 | PASS | All five exclusions respected |

Seconds are shell-clock intervals from `date +%s.%N` immediately before and after generation, including tool/orchestration overhead. Exact timestamps are in [records.json](/tmp/gpt-image-25-tests/records.json). File sizes and pixel properties were measured with Pillow, not inferred from the preview.

## Checks and evidence

T01. Minimal versus specified prompt: PARTIAL

- PASS: T01a supplies its own sunset, white lighthouse, attached house, rocky coast, and portrait composition
- PASS: T01b lighthouse occupies the right third; upper-left is open dark sky
- PASS: cool blue-hour ambient light and a lit amber lamp
- FAIL: strictly only one warm accent; an amber reflection appears in a foreground puddle and the requested red bands remain visible
- PASS: no people, boats, text, or watermark
- Both files are 1145×1374

The red-band requirement itself conflicts with an exclusively navy/slate/amber palette. The added reflection comes from the lamp, but is still another visible warm area under the strict check.

T02. Prompt format invariance: PASS for this pair

| Requirement | T02a | T02b |
|---|---|---|
| Ceramic teapot | PASS | PASS |
| Matte sage-green glaze | PASS | PASS |
| Walnut-looking wood table | PASS | PASS |
| Morning-looking side light from left | PASS | PASS |
| One steam wisp from spout | PASS | PASS |
| Folded linen napkin, foreground right | PASS | PASS |
| Shallow depth of field | PASS | PASS |
| Square, centered teapot | PASS | PASS |

Both score 8/8. The single steam plume branches internally in places. Material species and time of day are judged from appearance. These two samples do not establish statistical equivalence or prove that format never affects quality.

T03. Exact accented text: PASS

- PASS: headline reads exactly "PÂTISSERIE ONDINE"
- PASS: subline reads exactly "Montréal · depuis 1987"
- PASS: Â, é, and the middle dot are present
- PASS: each string appears once
- PASS: no extra text

The cream background, croissant illustration, tall serif headline, and smaller sans-serif subline are also present.

T04. Dense text and data: PARTIAL hypothesis, all listed image checks PASS

- PASS: title reads "Q3 2026 revenue by region"
- PASS: labels read "North", "South", "East", "West"
- PASS: values above those bars read "42", "31", "27", "18", respectively
- PASS: y-axis ticks read "0", "10", "20", "30", "40", "50"
- PASS: gridlines occur every 10, with the baseline at zero
- PASS: footnote reads "Source: internal finance report, unaudited."
- PASS: exactly four bars and no extra text
- PASS: bar heights are proportional; sampled blue spans are 534, 393, 342, and 230 pixels, corresponding to approximately 42.11, 30.99, 26.97, and 18.14 on the 0–50 scale

The data-rendering part of H passed. The claim that small text is the weakest point was not demonstrated: even the footnote is readable and exact.

T05. Prompt size control: PASS for these calls

- PASS: both prompts yielded a wide image, 1672×941, approximately 1.7768:1
- FAIL: exact 16:9 pixel ratio, although the discrepancy is only about 0.05%
- FAIL: T05b's exact 3840×2160 request
- Neither file reaches 3840×2160
- PASS: lavender fields at sunset, no visible text

The results support aspect-ratio inference and failure of this exact-size instruction. They do not prove that every possible prompt must fail to produce 4K.

T06. Transparency: PARTIAL

- PASS: PNG mode is RGBA
- PASS: 749,783 of 1,573,230 pixels are fully transparent, fraction 0.476588293 or 47.6588%
- PASS: corner alpha values are 0, 0, 0, 0
- PASS: no painted checkerboard, including inspection of RGB with alpha removed
- PASS: no obvious dark or colored fringe when composited on solid gray; the requested white outline is present
- FAIL: a strictly clean alpha cutout; faint stray pixels remain outside the outline, and the underlying RGB has ragged white residue
- Only 1,630 pixels are fully opaque; 821,817 have intermediate alpha, mostly 253–254 in the subject
- PASS: no text or cast shadow

The tool returned no transparency/background flag. Transparency was established from the saved file. Inspection derivatives are in `inspection/`; the original output was not modified. The direct RGBA viewer rendered anomalously dark, so the alpha measurements and a solid-gray composite were used to verify it.

T07. Photorealism: PARTIAL

- PASS: visible facial wrinkles, beard strands, and weathered hand texture; no obvious plastic smoothing
- PASS: eye-level-looking medium framing, man in left third, softly blurred harbor on right, natural overcast light
- PASS: no readable text or watermark
- FAIL to fully verify: five digits per hand cannot all be counted independently because the grip and net hide them

In the close crop, four curled fingers are distinguishable on the image-left hand; its thumb is hidden. On the image-right hand, the thumb and roughly three curled finger contours are distinguishable, with the remaining contour obscured. No clear extra digit is visible. This is a verification limit, not a demonstrated anatomical defect. A generated image also cannot establish a real 50mm focal length or prove an absence of retouching.

T08. Body, pose, and contact: PASS

- PASS: full body and both feet included, side view
- PASS: each shoe rests on a visible pedal
- PASS: both hands grip the handlebars; near-hand fingers curl plausibly around the grip
- PASS: gaze points ahead along the road
- PASS: no readable text; frame marks look worn and cannot be transcribed

The far hand is partly occluded. The contact check passes visually, but this image does not expose all ten fingers for counting.

T09. Sequential edits: PARTIAL

T09a, snow edit:

- PASS: recognizable face, beard, and age retained
- PASS: pose, framing, camera angle, clothing colors, orange net, and diffuse lighting direction retained
- PASS: falling snow and a thin layer on the dock
- FAIL: only the requested change; warm harbor lights appear that were absent in T07, and small textures change

T09b, blue net edit:

- PASS: net becomes blue while the orange bib remains orange
- PASS: identity, overall pose, framing, snow, and scene colors broadly retained
- FAIL: everything else unchanged; beard detail and bib folds/texture are redrawn
- PASS: no text in either edit

| Comparison | Grayscale mean absolute difference, 0–255 |
|---|---:|
| T07→T09a | 16.860357 |
| T09a→T09b | 4.520057 |
| T07→T09b, additional cumulative comparison | 16.868444 |

Method: Pillow conversion to L, then Lanczos resize to 256×171, then the mean of the absolute pixel difference. These whole-image scores include intended changes and are not isolated measures of unwanted drift. The second edit visibly adds texture drift, but its smaller incremental score does not demonstrate increasing drift magnitude.

T10. Indexed multi-reference composite: PARTIAL

- PASS: seated fox pose resembles image 1, including tilted head, straight forelegs, and tail curled to image-right
- PASS: fox is rendered with realistic fur and placed on lower-left granite
- PASS: lighthouse remains in the same upper-right position; the horizon, blue sky, and broad rock layout are retained
- FAIL: exact proportions; the realistic fox has a smaller head relative to its body
- FAIL: fully consistent lighting; warm rim light along the fox's image-left edge is stronger than the surrounding cool rocks suggest, with the visible lamp on the opposite side
- PASS: no text

The numbered roles were followed. Scene preservation is strong at the composition level, not pixel-exact.

T11. Character consistency: PASS under a viewer-left interpretation

- PASS: mustard-yellow feathers
- PASS: one teal tuft on the image-left side, matching the front-view reference
- PASS: oversized red round glasses
- PASS: green knitted scarf with white stripes
- PASS: gouache brush texture and children's-book style remain consistent
- PASS: open book, mushroom shelter, rain, and no text

T11a shows front and side full-body views. "Left side" is ambiguous: the front-view tuft is on the viewer's left, which is the owl's anatomical right. An anatomical-left criterion would fail in both generations; the follow-up preserves the reference's placement.

T12. Product exclusions: PASS

- PASS: no logo
- PASS: no text
- PASS: no watermark
- PASS: no border
- PASS: no props

The output also depicts the matte black ceramic mug, gray seamless background, studio lighting, and gentle contact shadow.

## Returned metadata and audit files

Every call returned exactly two top-level fields:

- `image_url`: a `data:image/png;base64,...` string containing the PNG
- `output_hint`: the saved source path and instructions to copy the file while leaving the original in place

No call returned an explicit model, revised prompt, quality, size, background, transparency flag, seed, or error field. These fields were absent, not false or set to "auto". The RGBA result does not imply that a transparency flag was returned.

All source PNGs were under `/home/pascal/.codex/generated_images/01a0e816-876a-7613-a647-a0a6992675dc/`. For each call, the exact `output_hint` and full `image_url` are preserved in its raw JSON linked below. The hint followed this text, with each call's absolute source path substituted:

```text
Generated images are saved to /home/pascal/.codex/generated_images/01a0e816-876a-7613-a647-a0a6992675dc as <absolute source PNG path> by default.
If you need to use a generated image at another path, copy it and leave the original in place unless the user explicitly asks you to delete it.
The generated image is already displayed to the user. There is no need to render it in the final response as a Markdown image or file link.
```

Observed output sizes were 1145×1374, 1254×1254, 1672×941, 1536×1024, and 1370×1148. All contain approximately 1.573 million pixels. All are RGB except T06, which is RGBA.

[manifest.json](/tmp/gpt-image-25-tests/manifest.json) records exact prompts and reference paths. [records.json](/tmp/gpt-image-25-tests/records.json) records each attempt, source path, timestamps, and returned hint. [measurements.json](/tmp/gpt-image-25-tests/measurements.json) records dimensions, bytes, mode, SHA-256, alpha histogram, and drift scores. All 17 copied files match their returned base64 PNG bytes exactly.

[measure.py](/tmp/gpt-image-25-tests/measure.py) reproduces measurements and inspection crops. Run `uv --cache-dir .uv-cache run measure.py` from this directory. The initial Pillow command encountered a read-only default uv cache; using the workspace cache resolved it. This was a measurement setup error, not an image-generation failure.

## Exact prompts, references, and per-call raw responses

T01a. [Full raw response](/tmp/gpt-image-25-tests/raw-T01a.json)

References: none

```text
A lighthouse.
```

T01b. [Full raw response](/tmp/gpt-image-25-tests/raw-T01b.json)

References: none

```text
Editorial photograph for a travel magazine cover. A white-and-red striped lighthouse on a granite headland at blue hour, lamp lit. Composition: lighthouse on the right third, empty dark sky in the upper-left third reserved for a masthead. Lighting: cool blue ambient light with the warm lamp as the only warm accent. Palette: navy, slate, one warm amber. Constraints: no people, no boats, no text, no watermark.
```

T02a. [Full raw response](/tmp/gpt-image-25-tests/raw-T02a.json)

References: none

```text
Scene: walnut table, morning.
Subject: a ceramic teapot with a matte sage-green glaze, centered.
Details: soft morning side light from the left; one thin wisp of steam from the spout; a folded linen napkin in the foreground right.
Style: real photograph, shallow depth of field.
Composition: square, teapot centered.
```

T02b. [Full raw response](/tmp/gpt-image-25-tests/raw-T02b.json)

References: none

```text
A real photograph of a ceramic teapot with a matte sage-green glaze centered on a walnut table in the morning, soft side light from the left, one thin wisp of steam from the spout, a folded linen napkin in the foreground right, shallow depth of field, square composition with the teapot centered.
```

T03. [Full raw response](/tmp/gpt-image-25-tests/raw-T03.json)

References: none

```text
Minimal poster for a French-Canadian bakery. Centered headline, exactly once, in a tall serif typeface: "PÂTISSERIE ONDINE". Below it, exactly once, in a small sans-serif: "Montréal · depuis 1987". Cream background, a single line illustration of a croissant above the headline. No other text anywhere.
```

T04. [Full raw response](/tmp/gpt-image-25-tests/raw-T04.json)

References: none

```text
A 16:9 presentation slide, flat corporate style, white background. Title at top-left: "Q3 2026 revenue by region". A vertical bar chart with exactly four bars labeled on the x-axis: "North" 42, "South" 31, "East" 27, "West" 18 (values in millions USD, printed above each bar). Y-axis from 0 to 50 with gridlines every 10. Footnote bottom-left in small text: "Source: internal finance report, unaudited." No other text.
```

T05a. [Full raw response](/tmp/gpt-image-25-tests/raw-T05a.json)

References: none

```text
Wide cinematic 16:9 banner of rolling lavender fields at sunset, no text.
```

T05b. [Full raw response](/tmp/gpt-image-25-tests/raw-T05b.json)

References: none

```text
Output size exactly 3840x2160 pixels (4K UHD). Rolling lavender fields at sunset, no text.
```

T06. [Full raw response](/tmp/gpt-image-25-tests/raw-T06.json)

References: none

```text
Die-cut sticker of a red fox sitting, flat vector illustration with a thick white outline. Transparent background. No shadow, no text.
```

T07. [Full raw response](/tmp/gpt-image-25-tests/raw-T07.json)

References: none

```text
Real photograph, candid, not retouched. A middle-aged fisherman mending an orange net on a wooden dock at overcast midday. Framing: medium shot from waist up, eye level, 50mm lens look, subject on the left third, harbor softly out of focus on the right. Visible skin texture, weathered hands, natural color. No text, no watermark.
```

T08. [Full raw response](/tmp/gpt-image-25-tests/raw-T08.json)

References: none

```text
Real photograph. A young woman riding a bicycle on a quiet city street, side view. Full body visible, feet included, both feet on the pedals. Both hands naturally gripping the handlebars. She is looking ahead at the road. No text.
```

T09a. [Full raw response](/tmp/gpt-image-25-tests/raw-T09a.json)

References in order:

1. `/tmp/gpt-image-25-tests/images/T07-fisherman.png`

```text
Edit the image: change only the weather to light falling snow with a thin layer of snow on the dock. Keep the man's face, identity, clothing colors, pose, the orange net, framing, camera angle, and lighting direction unchanged. No text.
```

T09b. [Full raw response](/tmp/gpt-image-25-tests/raw-T09b.json)

References in order:

1. `/tmp/gpt-image-25-tests/images/T09a-snow-edit.png`

```text
Edit the image: change only the orange net to a blue net. Keep everything else unchanged, including the snow, the man's face and identity, pose, framing, and colors of everything except the net. No text.
```

T10. [Full raw response](/tmp/gpt-image-25-tests/raw-T10.json)

References in order:

1. `/tmp/gpt-image-25-tests/images/T06-transparent-fox.png`
2. `/tmp/gpt-image-25-tests/images/T01b-specified-lighthouse.png`

```text
Image 1 is the subject: the red fox sticker character. Image 2 is the scene: the lighthouse headland. Create a new image: the fox from image 1, drawn as a realistic red fox (not a sticker) with the same pose and proportions, sitting on the granite rocks in the lower-left of the scene from image 2. Keep the lighthouse, its position, the blue-hour lighting, and the palette of image 2 unchanged. No text.
```

T11a. [Full raw response](/tmp/gpt-image-25-tests/raw-T11a.json)

References: none

```text
Character reference sheet, children's book illustration, gouache style, plain off-white background. A small round owl named Pip: mustard-yellow feathers, one teal ear tuft on the left side only, oversized round glasses with red frames, a green knitted scarf with white stripes. Show Pip front view and side view, full body. No text.
```

T11b. [Full raw response](/tmp/gpt-image-25-tests/raw-T11b.json)

References in order:

1. `/tmp/gpt-image-25-tests/images/T11a-owl-reference.png`

```text
Same character as the reference: Pip the owl with mustard-yellow feathers, one teal ear tuft on the left side only, red round glasses, green scarf with white stripes. New scene: Pip reading a large open book under a mushroom during light rain, children's book gouache style. No text.
```

T12. [Full raw response](/tmp/gpt-image-25-tests/raw-T12.json)

References: none

```text
Product photograph for an e-commerce listing. A plain matte black ceramic coffee mug, unbranded, on a seamless light-grey backdrop, soft studio light, gentle shadow under the mug, three-quarter view. No logo, no text, no watermark, no border, no props.
```

## Cross-test findings

Observations:

- Composition, scene lighting, shallow depth of field, and object placement generally followed the prompt in these samples
- The two teapot prompt formats both scored 8/8
- All requested bakery and chart text was exact, including accents, punctuation, small footnote text, and numeric data
- Both lavender prompts produced 1672×941; asking for exact 4K did not change the output dimensions
- Transparent output had genuine alpha, but residual low-alpha pixels and slightly translucent subject pixels prevented a strict clean-cutout pass
- Edits preserved recognizable identity and overall framing while also changing unrequested lights and textures
- Numbered references preserved scene composition and subject pose; lighting integration and exact proportions were weaker
- Pip retained all defining visual details; the meaning of "left" remained ambiguous
- The mug respected all five negative constraints
- Occlusion limited complete finger-count verification, even where hand contact looked plausible

Interpretation:

- Detailed prompts appear useful for visual control, but this run does not establish deterministic behavior
- Prompt-only size instructions influenced shape more clearly than exact pixel dimensions
- Reference reuse supported continuity, but "keep unchanged" did not guarantee pixel-exact preservation
- This run provides no evidence that small text was the weakest capability
- One sample per condition cannot establish format invariance, causal benefit from camera language, or broad reliability; all calls also shared one conversation
- Whole-image grayscale differences measure intended edits and unwanted changes together, and cannot by themselves prove identity drift or compounded error
