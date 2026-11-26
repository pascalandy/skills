# Antigravity native image generation (Nano Banana)

Use this route only when the request names Antigravity or Nano Banana. Otherwise use the default Codex plan route in `SKILL.md`.

## 1. Host, plan, and fixed limits

Native image generation requires a signed-in Antigravity host (Antigravity IDE, Antigravity App, Antigravity CLI `agy`, or Antigravity ACP such as T3 Code) with its built-in `image-generator` subagent or `generate_image` tool available. Plan quotas and overage credits follow the active Antigravity account plan (Google AI Pro and Ultra apply to personal Google accounts; see [plans](https://antigravity.google/docs/plans)).

Two models run in sequence on this route:

1. **Director (`image-generator` subagent)**: runs at high reasoning, reads local reference images, writes a detailed visual prompt, invokes `generate_image`, inspects the output, and retries up to three times
2. **Painter (`generate_image`)**: runs **Nano Banana 2** (`gemini-3.1-flash-image`), fixed server-side

`generate_image` exposes only `Prompt`, `ImageName`, `AspectRatio`, and optional `ImagePaths` (local references for style matching or targeted edits). Fixed limits:

- **Model**: Nano Banana 2 only; no model selector (cannot select Nano Banana Pro, Nano Banana 2.1, or 2 Lite)
- **Resolution**: 1K tier only (for example `1376x768` at `16:9` or `~1024x1024` at `1:1`); no `2K` or `4K` parameter
- **Format and background**: opaque `.jpg` saved into conversation artifacts; no alpha transparency, no GIF or animation, and no shell tool inside `image-generator`
- **Thinking**: painter thinking level is not exposed; the `image-generator` subagent already runs at high reasoning
- **Watermarks**: invisible SynthID and C2PA credentials; no visible Gemini sparkle watermark observed on Antigravity outputs

## 2. Steps

1. Confirm the active session runs on an Antigravity host with the built-in `image-generator` subagent or `generate_image` tool available. Outside Antigravity (Claude Code, Codex, Pi, OpenCode), stop, report that native Nano Banana generation requires an Antigravity host, and offer the default Codex plan route
2. Check for unsupported requirements before generating. Stop and report the native limit when the request requires transparent background or cutout (converting `.jpg` to `.png` cannot create alpha transparency; offer the Codex plan `--transparent` route), GIF or animation, native 2K or 4K resolution, or a model other than Nano Banana 2 (such as Nano Banana Pro, Nano Banana 2.1, or the Gemini API)
3. Send the brief to the active Antigravity session's built-in `image-generator` subagent (or `generate_image` when exposed directly): set `AspectRatio` closest to the final frame (`16:9`, `1:1`, `3:2`, `21:9`) so the 1K pixel budget fills the composition without destructive cropping, include one to three absolute local `ImagePaths` when locking a visual style or subject, and state visible details and exclusions
4. View the returned `.jpg` at full resolution and verify composition, text accuracy, and fidelity. To fix a defect without losing a mostly good layout, pass the generated `.jpg` back via `ImagePaths` and describe only the targeted change plus what must stay unchanged
5. When the caller asked for `.png`, exact delivery dimensions (such as `1280x640`), or a path outside conversation artifacts, convert, crop/resize, and copy the accepted `.jpg` in the parent agent. Resizing adds pixels, not native detail
6. Deliver the final file path, route (Antigravity plan), model (Nano Banana 2, 1K JPEG), any post-processing applied, and unresolved defects

## 3. Billing boundary

Google AI Pro covers Antigravity through its native OAuth login only and excludes the Gemini API (Google AI Studio). This skill has no Gemini API backend; never switch to a separately billed Gemini API call or reuse an Antigravity OAuth login in third-party software (which violates Antigravity terms of service). When a request exceeds Antigravity's fixed 1K Nano Banana 2 limits, report the limit instead of paying externally.

## Sources

- [Antigravity models](https://antigravity.google/docs/models), [plans](https://antigravity.google/docs/plans), and [FAQ](https://antigravity.google/docs/faq)
- [Antigravity hooks](https://antigravity.google/docs/hooks) and [changelog](https://antigravity.google/docs/changelog)
- [Gemini image generation](https://aistudio.google.com/docs/image-generation) and [pricing](https://aistudio.google.com/docs/pricing)
