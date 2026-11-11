# GPT Image 2.6 guide: plan, Flare, and Sunburst

Two modes: the Codex plan by default, OpenRouter for GPT Image 2.6 Flare or Sunburst after the user agrees to pay. Settings were checked against OpenAI and OpenRouter documentation and probed on the plan on 2026-11-11. Defaults are starting points, not experimentally proven optima; [test limits](#8-test-evidence) apply.

## 1. Decide the request

Default to the Codex plan. It generates with Images 2.6, but OpenAI offers the Flare and Sunburst choice only in the API: the plan has one model, chosen by the server, and fixed quality and size. A request for best quality, speed, or a GIF needs OpenRouter. The presence of an API key never switches to paid generation. If the plan is unavailable, stop with the readiness error.

`--model flare` or `--model sunburst` selects OpenRouter, reads the key from the keyring entry `openrouter`, user `api_key`, then from `OPENROUTER_API_KEY`, and bills the OpenRouter account. Both generation and edits use `POST https://openrouter.ai/api/v1/images`. `--backend` names the provider; OpenRouter is the only paid one today.

Set dimensions for the destination. For comparisons, specify model, quality, size, and candidate count explicitly. Inspect the resolved request with `--dry-run` before generating.

## 2. Models and quality

| Request | Model | API name |
|---|---|---|
| fast, quick | Flare | `openai/gpt-image-2.6-flare` |
| best quality | Sunburst | `openai/gpt-image-2.6-sunburst` |

Both models take the same quality levels: `low`, `medium`, `high`, `xhigh`, `max`. The CLI sends default `high` for both; `--quality` sets another. OpenAI announces Flare in about six seconds at `low`, and Sunburst's gains at `medium` or `high`.

Complexity, how much the model plans before rendering, takes `low`, `medium`, or `high`; the CLI omits it, so the API uses `high`. Lower complexity suits focused edits but can introduce unwanted changes. It has no separate fee.

With `--aspect`, the CLI picks a size near 2.4 MP. `--size` sets exact pixels. Without either shape flag, generation omits `size` and uses the provider default; edits reuse a valid first-input size, otherwise its supported aspect ratio. Output extension chooses format.

## 3. Request reference

### 3.1 Parameters

OpenRouter controls below apply only after `--model`. On the plan, size guides post-processing and quality and model are unavailable.

| CLI | API field | Values and effect |
|---|---|---|
| `--backend` | endpoint selection | `auto` defaults to plan; `plan` forces it; `openrouter` needs `--model` |
| `--model` | `model` | `flare` or `sunburst` expands to the API name in [section 2](#2-models-and-quality) |
| `--quality` | `quality` | changes rendering effort, latency, and cost |
| `--size` | `size` | `WIDTHxHEIGHT`; controls aspect ratio and pixel count |
| `--aspect` | computed `size` | `W:H`; CLI chooses valid dimensions near 2.4 MP |
| `--prompt`, `--prompt-file` | `prompt` | Up to 32,000 characters; file value `-` reads stdin |
| `--transparent` | `background` | Requests `transparent`; otherwise CLI sends `auto` |
| `--out` | `output_format` | `.png`, `.jpg`/`.jpeg`, `.webp`, `.gif` |
| `--candidates` | `n` | 1–10 variants; default one, billed per image |
| repeated `--image` | `input_references` | Up to 16 edit inputs, sent as data URLs |
| `--dry-run` | no request | Answers the resolved settings |
| `-v` | none | Receipt on stderr: requested settings, returned metadata, usage, files |

OpenRouter also exposes `output_compression` and passthrough options such as `moderation` and `complexity`; the CLI fixes JPEG/WebP compression at 85. Consult [OpenRouter image generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) for controls beyond CLI help.

This CLI does not expose masks, markup edits, SVG output, streaming, `seed`, `negative_prompt`, or `steps`. Put exclusions and edit boundaries in the prompt. Do not assume OpenAI-specific parameters work through OpenRouter.

### 3.2 Size

Custom sizes must satisfy all four rules:

- Both dimensions are multiples of 16
- Neither edge exceeds 3,840 px
- Long edge is at most three times the short edge
- Total pixels are between 655,360 and 8,294,400

Above 2560×1440, sizes are experimental. Useful choices include `1024x1024`, `1536x1024`, `1024x1536`, `1536x864`, `2048x1152`, `2048x2048`, `2560x1440`, and `3840x2160`.

Choose aspect ratio for composition, then pixels for display, print, or cropping. Both size and quality can affect results; test them separately. A prompt asking for 4K does not set API dimensions.

### 3.3 Background, format, and compression

- Use PNG for fine text, line art, or assets that will be edited again
- Use JPEG/WebP for smaller delivery files; inspect compression around edges and lettering
- For cutouts, request transparent background with PNG/WebP and an isolated subject. Check actual alpha values and edges; a painted checkerboard is not transparency. On the plan, the CLI sets the Codex tool's `transparent_background` flag and fails the run when Codex sent an opaque request
- JPEG and GIF cannot carry this transparency; PNG does not accept `output_compression`
- Unmodified API images retain their returned bytes. Format conversion or resizing requires re-encoding

### 3.4 GIF

A `.gif` `--out` asks OpenRouter for an animated GIF from either model. OpenAI's defaults are 9 frames of 200 ms; the CLI does not set frames. A GIF's `size` is per frame and shares the request's pixel budget, so the CLI sends it only with `--size`; an `--aspect` goes into the prompt instead. Describe the subject, the motion, and the loop. For a sprite-sheet look, ask for identical panels, a fixed camera, and a last frame that leads back to the first. A returned GIF with one frame fails the run.

### 3.5 Cost

OpenRouter bills separately from the Codex plan. OpenAI lists the same token rates for both 2.6 models; token use varies by model, quality, and request. Verify actual charges with the answer's `cost` and OpenRouter's `usage.cost`.

### 3.6 Latency

Sunburst trades longer generation time for precision. Quality, complexity, size, input images, and request complexity can affect latency. Measure elapsed time for your workload.

## 4. Write the prompt

### 4.1 Rules

1. Name the deliverable and destination, then framing, placement, and empty space for copy. Use "image-left" or "viewer's right" to avoid ambiguous positions
2. Describe visible materials, lighting, colors, and medium. Camera terminology steers appearance; it does not simulate a camera
3. Specify body framing, gaze, pose, and contact when people matter
4. Quote exact text, count occurrences, specify placement, and exclude extra text. Supply chart labels and values verbatim
5. For edits, separate the change from invariants: identity, geometry, labels, pose, framing, or lighting
6. Assign references roles by index and identify the destination, scale, and lighting to match

### 4.2 Template

Keep only relevant lines:

```text
Deliverable: <asset type and where it will be used>
Scene: <environment, time, weather>
Subject: <main subject, its placement and scale>
Details: <materials, textures, lighting and its direction, colors>
Style: <real photograph | watercolor illustration | flat vector | 3D render ...>
Composition: <framing, camera angle, lens look, empty areas reserved for copy>
Motion (GIF): <what moves, in which order, how the loop closes>
Text (verbatim, exactly once each): "<string 1>" at <position>, <typeface>; "<string 2>" ...
Constraints: <must keep>; no other text, no logo, no watermark
```

## 5. Inspect and iterate

### 5.1 Checks

View every candidate at full resolution. The CLI's own checks cover file properties and returned metadata, not visual correctness; a mismatch fails the run.

- Required objects appear in the right places and counts; excluded elements are absent
- Every text string, number, chart relationship, and label is correct
- Anatomy, pose, gaze, and contact points are plausible
- Edits preserve the requested identity, geometry, labels, and unchanged regions
- Cutouts contain meaningful transparency without halos or background specks
- A GIF keeps the subject consistent across frames and loops without a jump
- Receipt metadata and decoded dimensions match requested size, quality, background, format, and count where observable

### 5.2 The ladder

On OpenRouter, change one variable per retry, keeping all other settings fixed:

1. For missing elements or wrong layout, clarify the prompt
2. For weak detail, compare the next `--quality` level at the same size
3. If Flare still fails, compare `--model sunburst` at the same quality
4. For insufficient delivery pixels, raise `--size` while keeping aspect ratio

These are experiments, not guaranteed fixes. Repeat important comparisons to account for variation.

### 5.3 Edits and drift

Restate invariants in each edit and compare with the original. "Keep unchanged" does not guarantee pixel-identical preservation. If exact preservation matters, composite the accepted edit into the original outside the model.

## 6. Errors

Retry `429` and transient `5xx` with backoff. For invalid requests or moderation errors, inspect the returned error and change the request before retrying. Missing plan login or OpenRouter key is a readiness error, not permission to switch modes.

## 7. ChatGPT and Codex plans

The default runs `codex exec` with Codex's built-in image tool through the user's plan. Codex sends `model: gpt-image-2`, `quality: auto`, and `size: auto`; on 2026-11-11 the plan endpoint answered `quality: low` at `1536x1024` whatever model, quality, or size it received. `--model` selects OpenRouter; `--quality` requires it and never applies to the plan.

`--aspect` guides the prompt; `--size` crops and resizes the result. That can remove content or interpolate pixels without generating native detail. Inspect the saved image before delivery; `-v` names each upscale.

The plan endpoint refuses GIF output with "GIF output is not enabled for this request." Codex prepares GIF behind the under-development feature `image_generation_animation`. When the plan accepts GIF, the CLI's plan refusal is the line to remove.

## 8. Test evidence

[research-2026-09-28](research-2026-09-28/README.md) keeps the GPT Image 2.5 research as a frozen record. [research-2026-11-11](research-2026-11-11/README.md) keeps the 2.6 plan probes. Images and raw logs are not bundled, so visual judgments cannot be re-checked.

No paid OpenRouter 2.6 generation was run: GIF output, size handling, and quality through OpenRouter are unverified. Validate model-specific recommendations with saved prompts, settings, outputs, usage, timing, and visual judgments; change one setting at a time and repeat consequential comparisons.

## Sources

- [Introducing Images 2.6](https://openai.com/index/introducing-images-2-6/)
- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation) and [Images API reference](https://developers.openai.com/api/reference/resources/images)
- [Prompting guide](https://developers.openai.com/api/docs/guides/image-prompting)
- [Flare](https://developers.openai.com/api/docs/models/gpt-image-2.6-flare) and [Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.6-sunburst) model pages, and [pricing](https://developers.openai.com/api/docs/pricing#image-generation)
- [OpenRouter image generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) and [Sunburst endpoint capabilities](https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.6-sunburst/endpoints)
- [Codex image generation](https://learn.chatgpt.com/docs/image-generation)
