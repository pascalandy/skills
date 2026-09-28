# GPT Image 2.5 quality guide: Flare and Sunburst

Two modes: Codex plan by default, OpenRouter for explicitly requested GPT Image 2.5. Settings were checked against OpenAI and OpenRouter documentation on 2026-09-28. Presets are starting points, not experimentally proven optima; [test limits](#8-test-evidence) apply.

## 1. Decide the request

Default to the Codex plan with `gpt-image-2`. A request for higher quality, or the presence of an API key, never switches to paid generation. If the plan is unavailable, stop with the readiness error.

Only an explicit request for 2.5 selects OpenRouter. Use `--model flare` for generic 2.5 or Flare, `--model sunburst` for Sunburst. These flags select `--backend openrouter`, require `OPENROUTER_API_KEY`, and bill the OpenRouter account. Both generation and edits use `POST https://openrouter.ai/api/v1/images`.

Choose a preset, then set dimensions for the destination. For comparisons, specify backend, model, quality, size, and candidate count explicitly. Inspect the resolved request with `--dry-run --json` before generating.

## 2. Tiers

**Default: High** (`--intent high`). Use another tier only when requested. Ask about unresolved requirements without a documented default.

On the plan, Draft/Standard produce one candidate, High two, Max three. Intent does not change the plan model or generation quality.

For explicitly selected OpenRouter, these presets supply defaults. An explicit `--model` overrides the table; generic 2.5 uses `--model flare`. OpenAI positions Flare for speed and Sunburst for precision. Presets do not guarantee acceptance.

| Tier | Use when the user wants | `model` | `quality` | Pixel budget with `--aspect` |
|---|---|---|---|---|
| Draft | quick idea or layout test | Flare | `low` | about 1.0 MP |
| Standard | everyday blog, social, or web image | Flare | `medium` | about 1.6 MP |
| High | final image, dense text, product shot, portrait | Sunburst | `high` | about 2.4 MP |
| Max | more detail, with longer generation time | Sunburst | `xhigh` | about 3.7 MP |

`--size` overrides the pixel budget. Without either shape flag, generation omits `size` and uses the provider default; edits reuse a valid first-input size, otherwise its supported aspect ratio. Output extension chooses format. `--quality max` is a separate override, not the `max` preset.

## 3. Request reference

### 3.1 Parameters

OpenRouter controls below apply only after explicit 2.5 selection. On the plan, size guides post-processing and quality/model overrides are unavailable.

| CLI | API field | Values and effect |
|---|---|---|
| `--backend` | endpoint selection | `auto` defaults to plan; `plan` forces it; `openrouter` explicitly selects paid 2.5 |
| `--model` | `model` | `flare` or `sunburst` expands to `openai/gpt-image-2.5-flare` or `openai/gpt-image-2.5-sunburst` |
| `--quality` | `quality` | `low`, `medium`, `high`, `xhigh`, `max`; changes generation effort, latency, and cost |
| `--size` | `size` | `WIDTHxHEIGHT`; controls aspect ratio and pixel count |
| `--aspect` | computed `size` | `W:H`; CLI chooses valid dimensions near the preset's pixel budget |
| `--prompt`, `--prompt-file` | `prompt` | Up to 32,000 characters; file value `-` reads stdin |
| `--transparent` | `background` | Requests `transparent`; otherwise CLI sends `auto` |
| `--out` | `output_format` | `.png`, `.jpg`/`.jpeg`, `.webp` |
| `--candidates` | `n` | 1–10 variants; API default is one, billed per image |
| repeated `--image` | `input_references` | Up to 16 edit inputs, sent as data URLs |
| `--dry-run --json` | no request | Resolved settings and estimated image-output cost |
| `--json` | receipt | Requested settings, returned metadata, usage, files, warnings |

OpenRouter also exposes `output_compression` and provider options such as `moderation`; the CLI fixes JPEG/WebP compression at 85. Consult [OpenRouter image generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) for controls beyond CLI help.

This CLI does not expose masks, streaming, `seed`, `negative_prompt`, or `steps`. Put exclusions and edit boundaries in the prompt. Do not assume OpenAI-specific parameters work through OpenRouter.

### 3.2 Size

Custom 2.5 sizes must satisfy all four rules:

- Both dimensions are multiples of 16
- Neither edge exceeds 3,840 px
- Long edge is at most three times the short edge
- Total pixels are between 655,360 and 8,294,400

Above 2560×1440, sizes are experimental. Useful choices include `1024x1024`, `1536x1024`, `1024x1536`, `1536x864`, `2048x1152`, `2048x2048`, `2560x1440`, and `3840x2160`.

Choose aspect ratio for composition, then pixels for display, print, or cropping. Both size and quality can affect results; billing formulas do not establish their visual effects. Test them separately. A prompt asking for 4K does not set API dimensions.

### 3.3 Background, format, and compression

- Use PNG for fine text, line art, or assets that will be edited again
- Use JPEG/WebP for smaller delivery files; inspect compression around edges and lettering
- For cutouts, request transparent background with PNG/WebP and an isolated subject. Check actual alpha values and edges; a painted checkerboard is not transparency
- JPEG cannot carry transparency; PNG does not accept `output_compression`
- Unmodified API images retain their returned bytes. Format conversion or resizing requires re-encoding

### 3.4 Cost

OpenRouter bills separately from the Codex plan. Equal listed token rates do not guarantee equal cost per image; token use varies by model, quality, and request.

The CLI's `--dry-run --json` uses OpenAI's published calculator as an image-output estimate, not an OpenRouter quote. Add inputs, candidates, and retries. Verify actual charges with OpenRouter `usage.cost` and compare cost per accepted image.

### 3.5 Latency

Sunburst trades longer generation time for precision. Quality, size, input images, and request complexity can affect latency. Measure elapsed time for your workload.

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
Text (verbatim, exactly once each): "<string 1>" at <position>, <typeface>; "<string 2>" ...
Constraints: <must keep>; no other text, no logo, no watermark
```

## 5. Inspect and iterate

### 5.1 Checks

View every candidate at full resolution. Automated warnings cover file properties and returned metadata, not visual correctness.

- Required objects appear in the right places and counts; excluded elements are absent
- Every text string, number, chart relationship, and label is correct
- Anatomy, pose, gaze, and contact points are plausible
- Edits preserve the requested identity, geometry, labels, and unchanged regions
- Cutouts contain meaningful transparency without halos or background specks
- Receipt metadata and decoded dimensions match requested size, quality, background, format, and count where observable

### 5.2 The ladder

For OpenRouter, change one variable per retry, keeping backend and all other settings fixed:

1. For missing elements or wrong layout, clarify the prompt
2. For weak detail, compare the next `--quality` level at the same size
3. If Flare still fails, compare `--model sunburst` at the same quality
4. For insufficient delivery pixels, raise `--size` while keeping aspect ratio
5. Compare `xhigh` with `max` only if the remaining defect warrants more effort

These are experiments, not guaranteed fixes. Changing `--intent` can change model, quality, pixel budget, and candidate count together. For controlled comparisons, override those settings explicitly and repeat important comparisons to account for variation.

### 5.3 Edits and drift

Restate invariants in each edit and compare with the original. "Keep unchanged" does not guarantee pixel-identical preservation. If exact preservation matters, composite the accepted edit into the original outside the model.

## 6. Errors

Retry `429` and transient `5xx` with backoff. For invalid requests or moderation errors, inspect the returned error and change the request before retrying. Missing plan login or OpenRouter key is a readiness error, not permission to switch modes.

## 7. ChatGPT and Codex plans

The default uses Codex built-in image generation with `gpt-image-2` through the user's plan. The backend controls generation settings. `--quality` alone cannot select a paid mode and is rejected on the plan; request 2.5 explicitly first.

High/Max request two/three candidates. `--aspect` guides the prompt; `--size` crops and resizes the result. That can remove content or interpolate pixels without generating native detail. Inspect the saved image and receipt before delivery.

## 8. Test evidence

The original work reported 12 plan-backend scenarios producing 17 images, plus eight endpoint probes. It did not establish Flare/Sunburst API parameter behavior. Prompts, image artifacts, and raw results are not bundled, so these reports are not independently reproducible evidence. Single samples and shared conversation context also limit conclusions.

No verified, controlled Flare-versus-Sunburst API comparison is included. Validate model-specific recommendations with saved prompts, settings, outputs, usage, timing, and visual judgments; change one setting at a time and repeat consequential comparisons.

## Sources

- [Image generation guide](https://developers.openai.com/api/docs/guides/image-generation) and [Images API reference](https://developers.openai.com/api/reference/resources/images)
- [Prompting guide](https://developers.openai.com/api/docs/guides/image-prompting)
- [Flare](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare) and [Sunburst](https://developers.openai.com/api/docs/models/gpt-image-2.5-sunburst) model pages
- [OpenRouter image generation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation) and [Flare endpoint capabilities](https://openrouter.ai/api/v1/images/models/openai/gpt-image-2.5-flare/endpoints)
- [Codex image generation](https://learn.chatgpt.com/docs/image-generation)

## Open questions

Unverified here: comparative OpenRouter cost and acceptance rates, and reliability of experimental sizes above 2560×1440. No paid OpenRouter generation was run for this update.
