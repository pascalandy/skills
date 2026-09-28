> Frozen research record, 2026-09-28. The 12-test plan Claude Opus 5.5 gave GPT-6 Astra (medium reasoning) through `codex exec` (Codex CLI 0.157.1), written 2026-09-28T12:56Z. Everything below the rule is unedited. Index: [README](README.md).

---

# Image generation test run: validate prompting assumptions for GPT Image 2.5

You are a test agent. Use the built-in `image_gen` tool (the Codex built-in image tool, NOT the `$imagegen` CLI fallback, NOT `scripts/image_gen.py`, no OpenAI API key exists). The built-in tool accepts only a prompt plus optional reference images, so every test here varies the PROMPT or the reference images, never API parameters.

Working directory: this directory. Save every output image into `./images/` as `TNN[a|b]-<slug>.png` by copying it from `$CODEX_HOME/generated_images/...` (default `~/.codex/generated_images/`). For reference-image tests, pass local paths from `./images/` via the tool's `referenced_image_paths`.

## Rules for validity
- Pass each prompt below to the tool VERBATIM. Do not rewrite, augment, or shorten it. One tool call per image.
- Record, for each call: the exact prompt, the reference paths (if any), everything the tool returned (revised prompt, background/transparency flag, quality, size, any other metadata, errors), wall-clock seconds (run `date +%s.%N` in the shell immediately before and after the tool call), output pixel dimensions, file size, image mode (RGB/RGBA).
- Inspect every image yourself with `view_image` before judging it. Judge strictly against the listed checks; quote the exact text you can read in the image when a check is about text.
- Use `uv run --with pillow python -c ...` (or a small script in this directory) for dimensions, mode, alpha statistics, and image diffs. Never use bare `python`/`python3`.
- If a call fails, record the failure verbatim, retry once unchanged, then move on.

## Tests
Each test states a hypothesis (H). Report PASS / FAIL / PARTIAL for H with evidence.

T01 Minimal vs specified prompt (2 images)
H: A specified prompt controls composition, light, and palette; a one-word-ish prompt yields a generic image with the model's own choices.
- T01a prompt: `A lighthouse.`
- T01b prompt: `Editorial photograph for a travel magazine cover. A white-and-red striped lighthouse on a granite headland at blue hour, lamp lit. Composition: lighthouse on the right third, empty dark sky in the upper-left third reserved for a masthead. Lighting: cool blue ambient light with the warm lamp as the only warm accent. Palette: navy, slate, one warm amber. Constraints: no people, no boats, no text, no watermark.`
Checks for T01b: lighthouse right third; empty upper-left area; blue hour; lamp lit and the only warm accent; no people/boats/text/watermark. Record the dimensions both calls produced.

T02 Prompt format invariance (2 images)
H (from OpenAI guide): labeled sections vs one paragraph carry the same intent equally well; format is for maintainability, not quality.
Requirements (8): a ceramic teapot; matte sage-green glaze; on a walnut table; morning side light from the left; one steam wisp; a folded linen napkin in the foreground right; shallow depth of field; square composition with the teapot centered.
- T02a prompt: `Scene: walnut table, morning.\nSubject: a ceramic teapot with a matte sage-green glaze, centered.\nDetails: soft morning side light from the left; one thin wisp of steam from the spout; a folded linen napkin in the foreground right.\nStyle: real photograph, shallow depth of field.\nComposition: square, teapot centered.` (the \n are real line breaks)
- T02b prompt: `A real photograph of a ceramic teapot with a matte sage-green glaze centered on a walnut table in the morning, soft side light from the left, one thin wisp of steam from the spout, a folded linen napkin in the foreground right, shallow depth of field, square composition with the teapot centered.`
Checks: count satisfied requirements out of 8 for each.

T03 Exact short text with accents (1 image)
H: Quoted text with an occurrence count and "no other text" renders exactly, including accents.
- Prompt: `Minimal poster for a French-Canadian bakery. Centered headline, exactly once, in a tall serif typeface: "PÂTISSERIE ONDINE". Below it, exactly once, in a small sans-serif: "Montréal · depuis 1987". Cream background, a single line illustration of a croissant above the headline. No other text anywhere.`
Checks: exact spelling incl. Â, é, middle dot; each string exactly once; no extra text.

T04 Dense small text / data (1 image)
H: Data given verbatim in the prompt renders correctly on a slide; small text is the weakest point.
- Prompt: `A 16:9 presentation slide, flat corporate style, white background. Title at top-left: "Q3 2026 revenue by region". A vertical bar chart with exactly four bars labeled on the x-axis: "North" 42, "South" 31, "East" 27, "West" 18 (values in millions USD, printed above each bar). Y-axis from 0 to 50 with gridlines every 10. Footnote bottom-left in small text: "Source: internal finance report, unaudited." No other text.`
Checks: every label, value, axis tick, and the footnote exact; bar heights proportional; no extra text.

T05 Size control from the prompt (2 images)
H: The built-in tool infers aspect ratio from the prompt but cannot be forced to an exact pixel size or 4K.
- T05a prompt: `Wide cinematic 16:9 banner of rolling lavender fields at sunset, no text.`
- T05b prompt: `Output size exactly 3840x2160 pixels (4K UHD). Rolling lavender fields at sunset, no text.`
Checks: actual pixel dimensions of each; does either reach 3840x2160?

T06 Transparent background (1 image)
H: Asking for a transparent background yields a real alpha channel (not a painted checkerboard) with clean edges.
- Prompt: `Die-cut sticker of a red fox sitting, flat vector illustration with a thick white outline. Transparent background. No shadow, no text.`
Checks: mode RGBA?; fraction of fully transparent pixels; the four corners alpha=0?; any checkerboard pattern painted into RGB?; edge fringe. Report the tool's transparency flag.

T07 Photorealism with camera language (1 image)
H: Explicit "real photograph" plus framing/lens/light cues produce a natural, non-plastic photo.
- Prompt: `Real photograph, candid, not retouched. A middle-aged fisherman mending an orange net on a wooden dock at overcast midday. Framing: medium shot from waist up, eye level, 50mm lens look, subject on the left third, harbor softly out of focus on the right. Visible skin texture, weathered hands, natural color. No text, no watermark.`
Checks: natural skin texture (no plastic smoothing); hands anatomically correct (count fingers); framing as specified; no text.

T08 People, pose, and hands (1 image)
H: Explicit body-framing and interaction phrases produce correct full-body pose and hand contact.
- Prompt: `Real photograph. A young woman riding a bicycle on a quiet city street, side view. Full body visible, feet included, both feet on the pedals. Both hands naturally gripping the handlebars. She is looking ahead at the road. No text.`
Checks: full body incl. feet; both feet on pedals; both hands on handlebars with plausible fingers; gaze ahead.

T09 Edit with invariants, then a second edit (2 images, uses T07 output)
H: "Change only X; keep Y" edits preserve identity and composition; a second edit compounds some drift.
- T09a: reference `images/T07-*.png` as the edit target. Prompt: `Edit the image: change only the weather to light falling snow with a thin layer of snow on the dock. Keep the man's face, identity, clothing colors, pose, the orange net, framing, camera angle, and lighting direction unchanged. No text.`
- T09b: reference the T09a output as the edit target. Prompt: `Edit the image: change only the orange net to a blue net. Keep everything else unchanged, including the snow, the man's face and identity, pose, framing, and colors of everything except the net. No text.`
Checks: identity kept (face, beard, age); pose/framing kept; only the requested change. Also compute a crude drift metric: resize input and output to 256 px wide greyscale and report the mean absolute pixel difference, for T07→T09a and T09a→T09b.

T10 Multi-reference compositing by index (1 image, uses T06 and T01b outputs)
H: Assigning each reference a numbered role lets the model combine them while preserving the subject.
- References in this order: image 1 = `images/T06-*.png`, image 2 = `images/T01b-*.png`.
- Prompt: `Image 1 is the subject: the red fox sticker character. Image 2 is the scene: the lighthouse headland. Create a new image: the fox from image 1, drawn as a realistic red fox (not a sticker) with the same pose and proportions, sitting on the granite rocks in the lower-left of the scene from image 2. Keep the lighthouse, its position, the blue-hour lighting, and the palette of image 2 unchanged. No text.`
Checks: fox pose resembles image 1; scene/lighthouse position preserved; lighting consistent.

T11 Character consistency across two generations (2 images)
H: Re-using a character reference image and repeating defining details keeps a character consistent.
- T11a prompt: `Character reference sheet, children's book illustration, gouache style, plain off-white background. A small round owl named Pip: mustard-yellow feathers, one teal ear tuft on the left side only, oversized round glasses with red frames, a green knitted scarf with white stripes. Show Pip front view and side view, full body. No text.`
- T11b: reference the T11a output. Prompt: `Same character as the reference: Pip the owl with mustard-yellow feathers, one teal ear tuft on the left side only, red round glasses, green scarf with white stripes. New scene: Pip reading a large open book under a mushroom during light rain, children's book gouache style. No text.`
Checks: each defining detail present in T11b (yellow, single left teal tuft, red glasses, striped green scarf); style consistent.

T12 Negative constraints on a product shot (1 image)
H: Explicit exclusions (no logo, no text, no watermark, no border) are respected.
- Prompt: `Product photograph for an e-commerce listing. A plain matte black ceramic coffee mug, unbranded, on a seamless light-grey backdrop, soft studio light, gentle shadow under the mug, three-quarter view. No logo, no text, no watermark, no border, no props.`
Checks: each exclusion respected.

## Report
Write `./results.md` and return the same content as your final message:
1. A table: test | image file(s) | dims | mode | seconds | hypothesis verdict | one-line evidence.
2. Per test: the checks with PASS/FAIL each, exact text read from the image where relevant, drift metrics, any tool metadata returned.
3. What the built-in tool returned as metadata overall (does it reveal model, quality, size, or background?). Any sizes it chose.
4. Cross-test findings: what reliably worked, what failed, surprises. Stay factual; separate observations from interpretation.
