# GPT Image 2.5 quality guide: Flare and Sunburst

This guide tells an agent how to send a request to `gpt-image-2.5-flare` (A, Flare) or `gpt-image-2.5-sunburst` (B, Sunburst) so the image meets the user's quality bar at the lowest acceptable latency and cost. It is self-contained: every fact needed to choose settings is here. The skill's `scripts/gpt_image.py` applies sections 1–3 and 7 for you; read them to understand or override its choices.

Facts were checked against OpenAI's developer docs on 2026-09-28. A claim that is not an official fact carries a tag:

- **[3p]**: third-party measurement or report, listed in [Sources](#sources)
- **[test]**: our tests on 2026-09-28, detailed in [section 8](#8-test-evidence). They ran through Codex's plan backend, whose model and settings are fixed ([section 7](#7-chatgpt-and-codex-plans)), so they show prompt behavior, not Flare- or Sunburst-specific behavior
- **[inference]**: our reasoning from official facts; treat it as a default, not a rule

## 1. Decide the request

Follow these steps in order. The request is done when the image passes every check in [section 5](#5-inspect-and-iterate) that applies to it and no cheaper setting would also pass.

1. **Pick the surface.**
   - Images API, `POST /v1/images/generations` and `POST /v1/images/edits`: one image job from one prompt. Use it by default: it exposes every control, and no mainline model rewrites your prompt.
   - Responses API with the `image_generation` tool: multi-turn editing in a conversation, File IDs as inputs, cached-input pricing. A mainline model rewrites your prompt first; the call returns it as `revised_prompt`.
   - Codex built-in `image_gen` tool on a ChatGPT plan: no API key needed, but it runs `gpt-image-2` at settings the backend fixes, so Flare and Sunburst are unreachable. Read [section 7](#7-chatgpt-and-codex-plans) before using it.
2. **Pick the tier** from the user's intent with the [tier table](#2-tiers). With no signal from the user, use *Standard*. When the user says quality is paramount, use *High*, then *Max* if a check fails.
3. **Set `size`** from the delivery target ([3.2](#32-size)). Send an explicit `size` and `quality`; `auto` makes output and cost unpredictable.
4. **Set `background`, `output_format`, and `output_compression`** ([3.3](#33-background-format-and-compression)).
5. **Write the prompt** ([section 4](#4-write-the-prompt)).
6. **Inspect the image, then move one step on the ladder** ([5.2](#52-the-ladder)). Change one variable per retry.

## 2. Tiers

Sunburst is the base model and produces higher image quality than GPT Image 2; Flare is the small, fast model with quality comparable to GPT Image 2. Sunburst is also the model OpenAI recommends when editing precision matters. Both bill the same token rates, and OpenAI's calculator gives them the same output-token count for the same size and quality ([3.4](#34-cost)), so **Sunburst costs time, not money**.

| Tier | Use when the user wants | `model` | `quality` | `size` | `output_format` | Output cost · typical time |
|---|---|---|---|---|---|---|
| Draft | a quick idea, thumbnail, layout test | Flare | `low` | `1024x1024`, `1536x1024`, `1024x1536` | `jpeg`, `output_compression` 85 | $0.005–0.006 · ~10 s |
| Standard | an everyday blog, social, or web image | Flare | `medium`; `high` when it holds small text | aspect-matched, about 1.5 MP (`1536x1024`, `1536x864`, `1024x1536`) | `png` or `webp` | $0.008–0.041 · 14–18 s |
| High | a client-facing final, slide, infographic, dense text, product shot, portrait | Sunburst | `high` | `1536x864`, `1536x1024`, `2048x1152` | `png` | $0.032–0.042 · ~30 s |
| Max | "quality is paramount", print or hero art, latency does not matter | Sunburst | `xhigh`; `max` only after `xhigh` fails a check | `2048x1152` up to `3840x2160` | `png` | $0.075–0.40 · 45–90 s |
| Precise edit | identity, product geometry, or layout must survive the edit | Sunburst via `/v1/images/edits` | `high` | the input image's aspect ratio | `png` | plus about $0.01 per reference image [3p] · ~30 s |
| Variants | several options of one prompt | Flare, `n` 2–10 | `low` or `medium` | as Draft or Standard | as Draft or Standard | cost × `n` |

Costs cover image output only ([3.4](#34-cost)). Times are [3p] medians at 1024×1024 without streaming ([3.5](#35-latency)); larger sizes add seconds.

## 3. Request reference

### 3.1 Parameters

Send `model` on every request: the Images API falls back to `dall-e-2` when no GPT Image-specific parameter is present, and the Responses tool defaults to `gpt-image-1`.

**Images API, generate and edit:**

| Parameter | Values (default) | Effect and rule |
|---|---|---|
| `model` | `gpt-image-2.5-flare`, `gpt-image-2.5-sunburst`, or the pinned snapshots `gpt-image-2.5-flare-2026-09-08`, `gpt-image-2.5-sunburst-2026-09-08` | Speed versus quality. Pin a snapshot when outputs must stay stable across releases |
| `prompt` | up to 32,000 characters | The largest quality lever you control ([section 4](#4-write-the-prompt)) |
| `quality` | `low`, `medium`, `high`, `xhigh`, `max`, `auto` (`auto`) | Detail, text legibility, latency, and cost. `xhigh` and `max` exist only on 2.5 models. The response's `quality` field reports the tier used |
| `size` | `auto` or `WIDTHxHEIGHT` (`auto`) | Aspect ratio and pixel count ([3.2](#32-size)). The response's `size` field reports the result |
| `background` | `transparent`, `opaque`, `auto` (`auto`) | [3.3](#33-background-format-and-compression) |
| `output_format` | `png`, `jpeg`, `webp` (`png`) | [3.3](#33-background-format-and-compression) |
| `output_compression` | 0–100 (100) | `jpeg` and `webp` only |
| `n` | 1–10 (1) | Variants of one prompt; each image bills separately. Send distinct prompts as separate requests |
| `moderation` | `auto`, `low` (`auto`) | `low` filters less; filtering stays on |
| `stream` | boolean (`false`) | Emits `image_generation.partial_image` events, then `image_generation.completed` |
| `partial_images` | 0–3 | Previews while streaming; each costs 100 extra output tokens ($0.003). You may receive fewer than requested |
| `user` | string | End-user ID for abuse monitoring; no effect on the image |

**Edit only, `/v1/images/edits`:**

| Parameter | Values | Effect and rule |
|---|---|---|
| `image` | up to 16 images: multipart `image[]` files, or JSON `images` entries of `{file_id}` or `{image_url}` (URL or base64 data URL); each under 50 MB | Order matters: the prompt refers to them as image 1, image 2. Each adds image-input tokens |
| `mask` | one image with an alpha channel, same size and format as image 1 | Transparent areas mark where to edit. The mask guides the model rather than clipping it, and applies to the first image only |
| `input_fidelity` | `low`, `high` | Omit it. OpenAI documents no 2.5 behavior, and `gpt-image-2` rejects it because it always uses high input fidelity |

**Responses API `image_generation` tool** takes `model`, `quality`, `size`, `background`, `output_format`, `output_compression`, `moderation`, `partial_images`, `input_image_mask`, `input_fidelity` (omit it), and `action`:

- `action`: `auto` (default) lets the model choose, `generate` forces a new image, `edit` forces an edit and errors when no image is in context
- `tool_choice: {"type": "image_generation"}` forces the tool call
- `previous_response_id`, or the prior `image_generation_call` ID, continues an edit
- The tool has no `n`, and the mainline model's tokens bill on top of the image
- `gpt-5` and newer mainline models can call the tool; OpenAI's own example uses `gpt-6-astra`

**Not accepted by GPT Image 2.5:** `style` and `response_format` belong to DALL·E (GPT Image returns base64), and OpenAI's API has no `seed`, `aspect_ratio`, `negative_prompt`, or `steps`, though some resellers use those names. Put style and exclusions in the prompt and aspect ratio in `size`.

### 3.2 Size

A custom `size` is valid when all four rules hold:

- width and height are multiples of 16
- neither edge exceeds 3,840 px
- the long edge is at most 3 times the short edge
- total pixels are between 655,360 and 8,294,400

Sizes above 2560×1440 (3,686,400 px) are experimental. Common sizes: `1024x1024`, `1536x1024`, `1024x1536`, `1536x864` (16:9), `2048x2048`, `2048x1152`, `2560x1440`, `3840x2160`, `2160x3840`.

Choose the aspect ratio from where the image will be displayed, then the pixel count from what the delivery needs: print, a large display, or room to crop. To fix missing detail or garbled text, raise `quality` instead: in OpenAI's token formula ([3.4](#34-cost)) the generation grid depends only on quality and aspect ratio, and pixel count only scales the cost [inference]. Set dimensions in `size`; the prompt does not set pixel dimensions.

### 3.3 Background, format, and compression

- **Transparent asset:** `background: "transparent"` with `output_format` `png` or `webp`, plus a prompt asking for an isolated subject with clean edges. A painted checkerboard is not transparency: decode the file and check its alpha channel at hair, glass, shadows, and edges. Subject pixels can come back at alpha 253–254 rather than 255, with faint alpha 1–2 specks around them [test T06]; when deriving a mask, threshold alpha at about 250 and treat values below about 8 as background [inference]
- **Photo delivered to the web:** `jpeg` or `webp` with `output_compression` 80–90 when file size or latency matters. `jpeg` returns faster than `png`
- **Asset that will be edited again, or holds fine text or line art:** `png`
- **Invalid combinations:** `jpeg` with `transparent`; `output_compression` with `png`

### 3.4 Cost

Per million tokens, both models bill: text input $5 (cached $1.25), image input $8 (cached $2), image output $30. These equal GPT Image 2's standard rates. Cached-input rates apply only through the Responses tool. The 2.5 model pages mark the Batch API unsupported and the pricing page lists no Batch rate for 2.5.

Access: rate limits are counted in images per minute (IPM): Tier 1 5, Tier 2 20, Tier 3 50, Tier 4 150, Tier 5 250. OpenAI may require API organization verification before GPT Image models work.

A request costs its text-input tokens, plus image-input tokens for edits and references, plus image-output tokens, plus any partial images. OpenAI's calculator uses one output-token formula for Flare and Sunburst. Output tokens and cost per image:

| Size | low | medium | high | xhigh | max |
|---|---:|---:|---:|---:|---:|
| `1024x1024` | 196 · $0.006 | 439 · $0.013 | 1,756 · $0.053 | 3,122 · $0.094 | 7,024 · $0.211 |
| `1536x1024` | 158 · $0.005 | 343 · $0.010 | 1,372 · $0.041 | 2,459 · $0.074 | 5,488 · $0.165 |
| `1536x864` | 120 · $0.004 | 280 · $0.008 | 1,078 · $0.032 | 1,917 · $0.058 | 4,312 · $0.129 |
| `2048x2048` | 397 · $0.012 | 892 · $0.027 | 3,568 · $0.107 | 6,343 · $0.190 | 14,272 · $0.428 |
| `2048x1152` | 157 · $0.005 | 367 · $0.011 | 1,413 · $0.042 | 2,511 · $0.075 | 5,650 · $0.170 |
| `2560x1440` | 205 · $0.006 | 478 · $0.014 | 1,843 · $0.055 | 3,276 · $0.098 | 7,370 · $0.221 |
| `3840x2160` | 371 · $0.011 | 865 · $0.026 | 3,336 · $0.100 | 5,930 · $0.178 | 13,342 · $0.400 |
| `3072x1024` | 103 · $0.003 | 247 · $0.007 | 988 · $0.030 | 1,729 · $0.052 | 3,952 · $0.119 |

For another size, use the calculator's formula:

```python
import math

GRID = {"low": 16, "medium": 24, "high": 48, "xhigh": 64, "max": 96}

def output_tokens(width: int, height: int, quality: str) -> int:
    long_grid = GRID[quality]
    scaled = long_grid / (max(width, height) / min(width, height))
    floor = math.floor(scaled)
    short_grid = floor + floor % 2 if scaled - floor == 0.5 else round(scaled)
    return math.ceil(long_grid * short_grid * (2_000_000 + width * height) / 4_000_000)

# cost in USD = output_tokens(width, height, quality) * 30 / 1_000_000
```

What the table implies:

- Quality drives cost far more than size: at 1024×1024, `max` costs 36 times `low`, while 4K `high` costs twice 1024×1024 `high`
- At the same quality, a non-square image can cost less than a square one, because the grid shrinks on the short side
- The same label means different work across models: 2.5 `high` bills like GPT Image 2 `medium`, and 2.5 `max` like GPT Image 2 `high`
- `quality: "auto"` has no fixed cost; one [3p] run billed it at 1024×1024 between `medium` and `high`
- Inputs cost little next to output: a 100-token prompt costs $0.0005, and one reference image added about $0.01 per request [3p]
- The response's `usage` object reports actual tokens. Judge cost per *accepted* image, counting retries

### 3.5 Latency

OpenAI publishes no latency table; its docs say complex prompts can take up to 2 minutes. Press coverage of the launch reports up to 50% lower latency than Images 2.0 [3p]. Set client timeouts to at least 180 s for `max` and 4K [inference].

[3p] median seconds at 1024×1024, PNG, no streaming, three calls per cell:

| Model | low | medium | high | xhigh | max | auto |
|---|---:|---:|---:|---:|---:|---:|
| Flare | 10.4 | 13.8 | 18.1 | 26.7 | 45.6 | 15.9 |
| Sunburst | 15.7 | 18.1 | 29.9 | 46.7 | 85.0 | 22.9 |
| GPT Image 2 (reference) | 23.0 | 48.1 | 154.7 | n/a | n/a | n/a |

The same source's single calls at larger sizes: Flare `high` took 15.8 s at 1536×864 and 27.5 s at 3840×2160; Sunburst `high` took 27.9 s and 33.5 s. One reference image added 0–7 s. Two of three Sunburst calls completed at `low` and at `high`, so keep a retry path.

To cut perceived latency, stream with `partial_images` 1–3 and show the previews.

### 3.6 Request examples

Generate (Images API):

```bash
curl -s https://api.openai.com/v1/images/generations \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-image-2.5-sunburst",
    "prompt": "…",
    "size": "1536x864",
    "quality": "high",
    "output_format": "png"
  }' | jq -r '.data[0].b64_json' | base64 --decode > out.png
```

Edit with ordered references and an optional mask (multipart):

```bash
curl -s https://api.openai.com/v1/images/edits \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F "model=gpt-image-2.5-sunburst" \
  -F "image[]=@scene.png" \
  -F "image[]=@subject.png" \
  -F "mask=@mask.png" \
  -F "quality=high" \
  -F 'prompt=Image 1 is the scene; image 2 is the subject. …' \
  | jq -r '.data[0].b64_json' | base64 --decode > edited.png
```

Responses tool: set the tool's options inside `tools`, and read the base64 image from the output item whose `type` is `image_generation_call` (field `result`):

```json
{
  "model": "gpt-6-astra",
  "input": "…",
  "tools": [{"type": "image_generation", "model": "gpt-image-2.5-flare", "quality": "medium", "size": "1536x1024", "action": "generate"}],
  "tool_choice": {"type": "image_generation"}
}
```

## 4. Write the prompt

The prompt decides content, composition, and text; the parameters decide resolution, detail budget, and format. Keep the parameters in the request.

### 4.1 Rules

1. **Define the result.** Name the deliverable and its use (magazine cover, product listing, slide), then the composition: framing, placement, empty space reserved for copy. Organize complex prompts as scene, subject, details, and constraints. State positions from the viewer's side ("image-left", "viewer's right"): "the left side" of a character is ambiguous [test T11]. Keep constraints consistent with each other: "red-and-white stripes" and "the lamp is the only warm accent" pull against each other [test T01].
2. **Pick a maintainable format.** Labeled lines and a single paragraph carried the same eight requirements equally well [test T02]; choose the one easiest to edit.
3. **Describe what is visible.** Materials, lighting and its direction, colors, medium. Write "real photograph" or "photorealistic" when that is the goal. Camera terms (35 mm film, 50 mm lens, eye level, shallow depth of field) steer appearance rather than simulate a camera. Replace mood words with concrete scale, atmosphere, and color.
4. **Specify people and actions.** Body framing ("full body visible, feet included"), gaze ("looking down at the open book"), and contact ("both hands gripping the handlebars") [test T08].
5. **Specify exact text.** Quote each string, give its count, position, and typeface, and add "no other text". Spell unusual names letter by letter. Give chart data as numbers [tests T03, T04].
6. **Separate change from constraints in edits.** "Change only X. Keep A, B, and C unchanged." List what must survive: identity, pose, geometry, layout, lighting, labels, camera angle. Name the exclusions: no text, no logo, no watermark [test T12].
7. **Give each reference a role.** "Image 1 is the subject; image 2 is the scene." Say which element moves where, at what scale, that its lighting, shadows, and color temperature match the destination, and what stays unchanged [test T10]. Use verbs like "edit image 1 by adding the dog from image 2" rather than "combine" or "merge".
8. **Iterate one change at a time.** Feed the previous output back as the edit input, ask for one change, and restate the invariants.

A bare subject gets the model's generic default; a specified prompt gets the requested placement, light, and palette [test T01].

### 4.2 Template

Use the labels that help and drop the rest:

```text
Deliverable: <asset type and where it will be used>
Scene: <environment, time, weather>
Subject: <main subject, its placement and scale>
Details: <materials, textures, lighting and its direction, colors>
Style: <real photograph | watercolor illustration | flat vector | 3D render ...>
Composition: <framing, camera angle, lens look, empty areas reserved for copy>
Text (verbatim, exactly once each): "<string 1>" at <position>, <typeface>; "<string 2>" ...
Constraints: <must keep>; no other text, no logo, no watermark
```

### 4.3 Patterns by use case

The *Settings* column names a [tier](#2-tiers) or overrides one setting.

| Use case | What to put in the prompt | Settings |
|---|---|---|
| Photorealism | "Real photograph", candid context, framing and lens look, light source and direction, texture words ("visible skin texture, pores, worn materials"), "no heavy retouching" | High for portraits, Standard otherwise |
| Exact text: ads, posters, packaging | Quoted copy, count, position, typeface, "no other text"; letter-by-letter spelling for odd words | `high` or above when the text is small |
| Slides, charts, diagrams | Write an artifact spec: deliverable, canvas, hierarchy, every label and number verbatim, visual language, "no clip art, no decorative clutter". For science, list the required components and what to leave out | Landscape (`1536x864`); `high` for small labels, axes, footnotes |
| UI mockups | Describe the product as if it already ships: real screens, hierarchy, spacing, real labels; name the device frame; avoid concept-art language | `1024x1536` for mobile |
| Comics | "Panel 1: …", one concrete visual beat per panel | Portrait for vertical strips |
| Logos | Brand, shapes, silhouette, "flat, vector-like, legible at small sizes", generous padding, "original, non-infringing" | `transparent` + `png`; `n` for options |
| Transparent cutout from a photo | "Extract the product and isolate it on a fully transparent background; crisp silhouette, no halos; preserve geometry and label; no backdrop, checkerboard, or shadow" | `transparent` + `png`; repeat the transparency requirement in later edits |
| Historical scene | Place and date ("Bethel, New York, August 16, 1969"), "period-accurate clothing and staging"; verify the details afterwards | Standard |
| Local edit: swap, remove, weather | "Replace ONLY the white chairs with wooden chairs. Preserve camera angle, room lighting, floor shadows, surrounding objects" | Precise edit |
| Identity or clothing edit | List the face, skin tone, body shape, pose, expression, and hairstyle to preserve; "replace only the clothing" | Precise edit |
| Combine references | Assign roles by index, name destination and scale, match lighting and color temperature, "do not change anything else" | Precise edit |
| Style transfer | Give the reference its role (palette, texture, medium), then describe the new subject | Standard |
| Sketch to render | "Preserve the exact layout, proportions, and perspective; add realistic materials and lighting; do not add new elements or text" | High |
| Translate text in an image | "Translate the text to Spanish. Do not change any other aspect of the image"; check for untranslated words | `high` |
| Recurring character | Generate a reference sheet first; for each new scene, pass it as a reference, repeat every defining detail, and add "do not redesign the character" [test T11] | Precise edit |

## 5. Inspect and iterate

### 5.1 Checks

Inspect every output before delivering it; read text at full resolution.

- Every required element is present, placed, and counted as asked, and nothing excluded appears
- Text: every string is spelled exactly, appears the requested number of times, and no extra text appears
- Data and diagrams: every number, label, and relationship is correct, and bar heights match values
- People: hands, fingers, limbs, and contact points are plausible, and gaze and pose match. Hands hidden by the pose cannot be verified; ask for visible hands when they matter [test T07]
- Edits: only the requested region changed, and identity, geometry, and labels survived
- Transparency: the decoded file has an alpha channel with transparent corners and clean edges
- Output: the returned `size`, `quality`, `background`, and `output_format` match the request

### 5.2 The ladder

When a check fails, change one variable and retry, in this order:

1. **Instruction failure** (missing element, wrong layout, extra text): fix the prompt. Add the missing constraint, quote the text, assign reference roles. A higher tier rarely fixes an unclear instruction.
2. **Detail failure** (garbled small text, mushy texture, weak hands): raise `quality` one step.
3. **Still failing on Flare at `high`**: switch to Sunburst at the same quality.
4. **Too few pixels for the delivery**: raise `size` and keep the aspect ratio.
5. **Only `xhigh` fails**: try `max` and compare both images; a higher tier does not guarantee a better result for every prompt.

When the output passes and latency or cost matters, walk the other way: lower `quality` one step at a time, then try Flare, and keep the cheapest setting that still passes.

### 5.3 Edits and drift

"Keep unchanged" preserves identity, pose, and framing, but the model redraws textures and can add details nobody asked for: a snow edit added warm harbor lights, and a second edit redrew beard and fabric texture [test T09]. Restate the invariants in every edit prompt and compare each result with its input. When a region must stay pixel-identical, composite the approved edit into the original outside the model.

## 6. Errors

- `429` and `5xx`: retry with backoff
- `error.type = "image_generation_user_error"`: change the prompt or inputs before retrying; branch on `error.code`
- `error.code = "moderation_blocked"`: `error.moderation_details.moderation_stage` is `input`, `output`, or `unknown`, and `categories` holds coarse labels such as `violence`. Rephrase, and show end users a generic message
- A forced Responses `action: "edit"` with no image in context returns an error

## 7. ChatGPT and Codex plans

**A ChatGPT or Codex plan cannot reach Flare or Sunburst, or any quality tier, from the terminal.** OpenAI's Codex docs state that built-in image generation uses `gpt-image-2` and counts toward the general Codex usage limits, which image turns consume 3–5 times faster than other turns; the Free plan has no image generation. To use Flare or Sunburst at a chosen quality and size, set `OPENAI_API_KEY` and call the Images API ([3.6](#36-request-examples)); API pricing then applies. An agent running in Codex can make that call from its shell.

What the plan path does [test T13]:

- Codex's built-in tool posts to `https://chatgpt.com/backend-api/codex/images/generations` with `{"model": "gpt-image-2", "quality": "auto", "size": "auto", "background": "auto"}` hard-coded; no Codex config key changes them
- The endpoint ignores the values anyway. Eight direct calls naming Flare, Sunburst, `gpt-image-2`, or a made-up model, at `low`, `high`, or `max`, at 1024×1024, 1536×1024, or 3840×2160, all returned a 1254×1254 image reporting `quality: "low"` and 515 output tokens in 22–24 s. A made-up model name succeeds, so the response never proves which model ran
- The other plan route, a Codex chat request with the hosted `image_generation` tool, reports `gpt-image-2-codex` whatever model is requested and also ignores `size` [3p]. Third-party tools that advertise Sunburst at `xhigh` through a plan use one of these two routes [inference from their READMEs]
- Using Codex with an API key applies API pricing, but the built-in tool still requests `gpt-image-2`, because the model is hard-coded [inference]

The built-in tool's arguments are `prompt`, plus either `referenced_image_paths` (local files to edit or use as references) or `num_last_images_to_include` (the last 1–5 conversation images), never both. It returns the PNG and a save-path hint only. Files land in `$CODEX_HOME/generated_images/<thread-id>/`; copy the chosen file to its destination.

Observed across 17 built-in calls [tests T01–T12]:

- **Size:** every output held about 1.57 million pixels, in an aspect ratio inferred from the prompt: 1254×1254, 1145×1374, 1370×1148, 1536×1024, 1672×941. These sizes are not multiples of 16. "Output size exactly 3840x2160 pixels" returned 1672×941
- **Time:** 21–58 s per call, median 33 s, including tool overhead
- **Transparency:** "Transparent background" in the prompt returned a real RGBA file, with the alpha caveats in [3.3](#33-background-format-and-compression)
- **Edits and references:** `referenced_image_paths` edits kept identity and framing ([5.3](#53-edits-and-drift))

The prompting rules in [section 4](#4-write-the-prompt) apply unchanged on the plan path. Because the plan fixes quality, spend a higher quality bar on more candidates and pick the best. The Codex `imagegen` skill's API fallback (`scripts/image_gen.py`, Codex 0.157.1) predates 2.5: with a 2.5 model it rejects `xhigh` and `max` and allows only `1024x1024`, `1536x1024`, `1024x1536`, and `auto`, so call the Images API directly.

## 8. Test evidence

T01–T12 (17 images) ran on 2026-09-28 through the Codex built-in tool, driven by a GPT-6 Astra (medium) agent, then re-checked by a second reviewer who inspected every image and recomputed dimensions, alpha statistics, and pixel differences. T13 probed the plan endpoint directly with explicit settings. The plan backend fixes the model and settings ([section 7](#7-chatgpt-and-codex-plans)), so these tests validate prompt behavior on the model behind ChatGPT and Codex, not Flare or Sunburst specifically. API parameter effects rest on OpenAI's docs and the [3p] benchmark.

| Test | Hypothesis | Result |
|---|---|---|
| T01 | A specified prompt controls composition, light, and palette | Pass with a caveat. "A lighthouse." returned a generic sunset postcard; the specified cover prompt placed the lighthouse on the right third, left the upper-left sky empty for a masthead, and kept blue hour. The lamp's reflection in a puddle broke "only warm accent" |
| T02 | Labeled lines and a paragraph carry the same intent | Pass: both 8 of 8 requirements, near-identical images |
| T03 | Quoted text with accents renders exactly | Pass: "PÂTISSERIE ONDINE" and "Montréal · depuis 1987" exact, once each, no other text |
| T04 | Chart data given verbatim renders correctly | Pass: title, four labels, values 42/31/27/18, axis ticks, and footnote exact; bar heights within 0.2 of their values |
| T05 | The built-in tool takes aspect ratio from the prompt but not pixel size | Pass: both 16:9 prompts returned 1672×941, including the one asking for 3840×2160 |
| T06 | "Transparent background" yields real alpha | Partial: RGBA, transparent corners, no painted checkerboard; subject alpha 253–254 and faint alpha 1–2 specks |
| T07 | Camera language gives a natural photo | Pass: natural skin and hand texture, requested framing. The grip hid some fingers, so the count was unverifiable |
| T08 | Body-framing phrases give the requested pose | Pass: full body, feet on pedals, hands on the handlebars, gaze ahead |
| T09 | "Change only X" edits keep everything else | Partial: identity, pose, framing, and both requested changes correct; the snow edit added warm harbor lights, and the net edit redrew beard and fabric texture. Mean grayscale difference from the input: 16.9 for the snow edit, 4.5 for the net edit, on a 0–255 scale that includes the intended change |
| T10 | Numbered reference roles combine two images | Partial: roles followed, pose and scene kept; the fox's head was smaller and its warm rim light did not match the blue-hour scene |
| T11 | A reference sheet plus repeated details keeps a character consistent | Pass: every defining detail carried over. "Left side" was read as the viewer's left |
| T12 | Explicit exclusions are respected | Pass: no logo, text, watermark, border, or props |
| T13 | The Codex plan endpoint honors `model`, `quality`, and `size` | Fail: 8 calls naming Flare, Sunburst, `gpt-image-2`, or `gpt-image-9-bogus`, at `low`, `high`, or `max`, at 1024×1024 to 3840×2160, all returned 1254×1254, `quality: "low"`, 515 output tokens, 22–24 s |

Limits: one sample per condition, and T01–T12 ran in one Codex conversation, which may carry context between calls.

## Sources

Official, read 2026-09-28:

- Image generation guide: <https://developers.openai.com/api/docs/guides/image-generation>. Its embedded `GptImageTokenCalculator` supplies the output-token formula in [3.4](#34-cost)
- Image prompting guide for GPT Image 2.5: <https://developers.openai.com/api/docs/guides/image-prompting>
- Model pages: <https://developers.openai.com/api/docs/models/gpt-image-2.5-flare>, <https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst>
- Images API reference: <https://developers.openai.com/api/reference/resources/images>
- Responses API reference and image generation tool guide: <https://developers.openai.com/api/reference/resources/responses>, <https://developers.openai.com/api/docs/guides/tools-image-generation>
- Pricing: <https://developers.openai.com/api/docs/pricing>
- Codex docs, image generation and usage limits: <https://learn.chatgpt.com/docs/image-generation>, <https://learn.chatgpt.com/docs/pricing#image-generation-usage-limits>
- Launch post, September 8, 2026: <https://openai.com/index/introducing-chatgpt-images-2-5/>, mirrored at <https://community.openai.com/t/introducing-chatgpt-images-2-5/1395897>

Third-party:

- Genflick, "GPT Image 2.5 cost and speed benchmark", September 8, 2026: <https://genflick.com/blog/gpt-image-2-5-cost-speed-benchmark>. Its per-image costs match the official token formula at every size it tested
- OmniRoute issue #14617, measured with a ChatGPT Pro Codex login on 2026-09-23: <https://github.com/diegosouzapw/OmniRoute/issues/14617>
- Launch coverage reporting up to 50% lower latency: <https://www.unite.ai/openai-releases-chatgpt-images-2-5-with-sketch-and-two-new-api-models/>, <https://datanorth.ai/news/openai-launches-chatgpt-images-2-5>

## Open questions

- Whether 2.5 accepts `input_fidelity`, and with what default
- Whether Flare and Sunburst ever return different output-token counts at the same size and quality. The calculator treats them as equal; the guide says token use "can differ by model and quality setting"
- How often sizes above 2560×1440 fail or return a smaller image
