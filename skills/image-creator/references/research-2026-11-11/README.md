# GPT Image 2.6 plan probes, 2026-11-11

> **Frozen record.** This folder states what was true and tested on 2026-11-11. Never edit it. A later round of research goes in a new sibling folder named `research-YYYY-MM-DD/`, which may cite and supersede this one. For current guidance, read [the guide](../guide.md).

- **Date:** 2026-11-11, 15:30–15:50 UTC (10:30–10:50 EST)
- **Question:** after OpenAI's Images 2.6 launch on 2026-11-04, can a ChatGPT or Codex plan choose GPT Image 2.6 Flare or Sunburst, set quality or size, or produce a GIF from the terminal
- **Environment:** Codex CLI 0.167.1 and 0.169.0-alpha.11 on a ChatGPT plan; GPT-6 Luna (low) as the plan controller; Claude Opus 5.5 orchestrating. No OpenAI API key; no paid OpenRouter generation

## Findings

1. The launch post says "In the API, we offer GPT‑Image‑2.6 Flare and Sunburst for developers to choose from", and that Images 2.6 is in ChatGPT and Codex on every plan. The Codex image-generation page still says built-in generation uses `gpt-image-2`
2. Codex's built-in tool `image_gen.imagegen` takes only `prompt`, `transparent_background`, `referenced_image_paths`, and `num_last_images_to_include`. `codex-rs/ext/image-generation/src/tool.rs` on openai/codex `main` sets `IMAGE_MODEL = "gpt-image-2"`
3. A traced `codex exec` run sent `POST https://chatgpt.com/backend-api/codex/images/generations` with `{"background":"opaque","model":"gpt-image-2","quality":"auto","size":"auto"}`
4. Direct requests to that endpoint with the Codex login asked for `gpt-image-2.6-flare` at `low` and `1024x1024`, `gpt-image-2.6-sunburst` at `high` and `1024x1536`, `gpt-image-2.6-flare` at `medium` and `2048x1152`, and a nonexistent model. Each answered `quality: low`, `size: 1536x1024`, and 343 image output tokens, in 8.6–139 s. The endpoint ignores model, quality, and size. Without a Codex-like `User-Agent`, Cloudflare refused the request with error 1010
5. GIF: the endpoint answered HTTP 400 `{"detail":"GIF output is not enabled for this request."}` to `output_format: "gif"`. Codex 0.167.1 has no `image_generation_animation` feature. Codex 0.169.0-alpha.11 lists it as under development; with it enabled, Codex sent `output_format: "gif"`, `frame_count`, and `frame_duration_ms`, and no image came back
6. OpenRouter lists `openai/gpt-image-2.6-flare` and `openai/gpt-image-2.6-sunburst` with qualities `low` to `max`, `gif` output, and `complexity` as a passthrough parameter. OpenAI lists both at $30 per million image output tokens

## Decisions taken from these findings

- The plan stays the default; it cannot offer Flare, Sunburst, quality, or GIF
- Best quality, speed, and GIF go through OpenRouter after the user agrees to pay
- The CLI keeps `codex exec` rather than the private endpoint: the endpoint ignores the settings that would justify it and needs a spoofed client signature
