# Antigravity native image generation (Nano Banana)

Use this route only when the request names Antigravity or Nano Banana. Otherwise stay on the default Codex plan route in `SKILL.md`.

## 1. Host requirement and fallback

Native image generation requires an Antigravity host (Antigravity IDE, Antigravity App, Antigravity CLI `agy`, or Antigravity ACP such as T3 Code) authenticated with a personal Google account. Google AI Pro and Ultra subscriptions provide higher quotas on a five-hour rolling window up to a weekly cap, with optional AI Credit overages (`useG1Credits: true` or `/usage` in CLI). Google Workspace accounts do not include Antigravity plan limits.

When running outside an Antigravity host (such as Claude Code, Codex, Pi, or OpenCode), stop and tell the user that native Nano Banana generation requires Antigravity, and offer the default Codex plan route instead.

## 2. How the pipeline works

Two models run in sequence:

1. **Director (`image-generator` subagent)**: runs at high reasoning, reads local reference images, composes a detailed visual prompt, invokes `generate_image`, inspects the output visually, and retries up to three times
2. **Painter (`generate_image`)**: runs **Nano Banana 2** (`gemini-3.1-flash-image`), fixed server-side

Exposed tool arguments are limited to `Prompt`, `ImageName`, `AspectRatio`, and optional `ImagePaths` (local reference images for style matching or targeted edits).

Fixed constraints on the Antigravity plan:

- **Model**: Nano Banana 2 only; no model selector on `generate_image` (the Antigravity Python SDK `google-antigravity` separately exposes `BuiltinTools.GENERATE_IMAGE`, defaults to `gemini-3.1-flash-lite-image` at 1K, and accepts model overrides and `aspect_ratio`)
- **Resolution**: 1K tier only (for example `1376x768` at `16:9` or `~1024x1024` at `1:1`); no `2K` or `4K` parameter
- **Format and location**: saves `.jpg` directly into the conversation artifacts folder; the subagent has no shell tool to convert, resize, or copy files
- **Thinking**: painter thinking level is not exposed; the `image-generator` subagent already runs at high reasoning
- **Watermarks**: outputs embed invisible SynthID and C2PA credentials; no visible Gemini sparkle watermark appears on Antigravity outputs

## 3. Steps on the Antigravity route

1. Confirm the built-in `image-generator` subagent is available in the current host; otherwise apply the fallback in [section 1](#1-host-requirement-and-fallback)
2. Send `image-generator` a concise brief specifying the deliverable, target `AspectRatio`, visible details, exclusions, and absolute local paths for any style or subject references (`ImagePaths`)
3. View the returned `.jpg` at full resolution and inspect composition, text accuracy, and fidelity. When a detail needs correction, pass the generated `.jpg` back to `image-generator` via `ImagePaths` and describe only the targeted edit plus what must stay unchanged
4. Run local post-processing in the parent agent when the caller needs `.png`, exact pixel dimensions (such as `1280x640`), or a specific destination path outside conversation artifacts
5. Deliver the final file path, route (Antigravity plan), model (Nano Banana 2, 1K JPEG), any post-processing applied, and unresolved defects

## 4. Maximizing quality within plan limits

- **Anchor with local references**: pass one to three style or subject images in `ImagePaths` to lock linework, palette, and texture more reliably than prose alone
- **Match `AspectRatio` to the final frame**: pick the ratio closest to the delivery frame (`16:9`, `1:1`, `3:2`, `21:9`) so the 1K pixel budget fills the composition without destructive cropping
- **Edit instead of restarting**: pass a mostly good `.jpg` back into `ImagePaths` for targeted fixes rather than regenerating from scratch
- **Keep post-processing local**: convert `.jpg` to `.png`, crop, or resize in the parent agent; resizing adds pixels, not native detail

## 5. Billing boundary and when to leave Antigravity

Google AI Pro covers Antigravity through its native OAuth login only. It does not cover the Gemini API (Google AI Studio). A Gemini API key cannot power Antigravity's built-in models, and external MCP servers calling the Gemini API bill separately per image (no free tier for Nano Banana 2, 2.1, or Pro). Reusing an Antigravity OAuth login in third-party software violates Antigravity terms of service.

Leave Antigravity only when a requirement exceeds plan limits:

- **Nano Banana Pro on the same Google AI Pro subscription**: generate on `gemini.google.com` and regenerate with Nano Banana Pro via the three-dot menu (also supports ~3 s animated GIFs)
- **Native 2K/4K, model choice, grounding, or Batch**: call the paid Gemini API for **Nano Banana 2.1** (`gemini-nano-banana-2.1`, 1K/2K/4K, Search and Image Search grounding, up to 14 references, Batch at 50% off), **Nano Banana Pro** (`gemini-3-pro-image`, 1K/2K/4K), or **Nano Banana 2 Lite** (`gemini-3.1-flash-lite-image`, 1K only)

## Sources

- [Antigravity models](https://antigravity.google/docs/models) and [plans](https://antigravity.google/docs/plans)
- [Antigravity hooks](https://antigravity.google/docs/hooks), [SDK tools](https://antigravity.google/docs/sdk/tools), and [FAQ](https://antigravity.google/docs/faq)
- [Gemini API image generation](https://aistudio.google.com/docs/image-generation) and [pricing](https://aistudio.google.com/docs/pricing)
