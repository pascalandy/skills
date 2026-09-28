> Frozen research record, 2026-09-28. The brief Claude Opus 5.5 gave GPT-6 Sol (high reasoning) through `codex exec` (Codex CLI 0.157.1), written 2026-09-28T12:52Z. Everything below the rule is unedited. Index: [README](README.md).

---

# Research task: GPT-Image-2.5 Flare and GPT-Image-2.5 Sunburst (OpenAI image models)

Today is 2026-09-28. OpenAI announced ChatGPT Images 2.5 (https://openai.com/index/introducing-chatgpt-images-2-5/):
"For developers, we're introducing two new models in the API. GPT-Image-2.5 Flare brings the same improvements in quality, editing, and speed, and GPT-Image-2.5 Sunburst offers an extra level of precision for detailed creative work with longer generation times."

Goal: collect EVERY variable a developer controls that affects output quality, speed, or cost when generating or editing images with these two models, so another agent can choose request settings without doing any web research. Use live web search. Do not edit any files.

## Sources, in priority order
1. OpenAI official: developers.openai.com (image generation guide, "GPT Image 2.5 prompting guide" at https://developers.openai.com/api/docs/guides/image-prompting, model pages for gpt-image-2.5-flare and gpt-image-2.5-sunburst, API reference for images.generate / images.edit, Responses API `image_generation` tool, pricing, rate limits, deprecations), openai.com announcement, OpenAI cookbook, OpenAI community/changelog.
2. Third-party (fal, WaveSpeed, Atlas Cloud, Kanaries, evolink, blogs): use only to fill gaps, and label every such claim as THIRD-PARTY. Note when third-party parameter names differ from OpenAI's (for example `aspect_ratio` on a reseller vs `size` on OpenAI).
If openai.com returns 403, try developers.openai.com, platform.openai.com, cookbook.openai.com, GitHub openai/openai-python or openai-openapi spec, and search-engine caches.

## Questions to answer (answer each explicitly; write "NOT FOUND" when you cannot confirm)
1. Exact API model IDs (and any dated snapshots / aliases), release date, endpoints (Images API generate/edit, Responses API tool, Batch API), and which ChatGPT surface uses which model.
2. Flare vs Sunburst: intended use, quality differences, latency (typical seconds per image by quality/size if published), pricing per image and per token (text input, image input, image output, cached), rate limits/tiers, org verification requirements.
3. Every request parameter with allowed values and defaults, per endpoint and per model: model, prompt (max length), n, size (fixed list and custom WIDTHxHEIGHT rules: multiples, max edge, ratio, min/max pixels; what `auto` does), quality (all tiers incl. any new ones like xhigh/max; default; what each changes; token counts per tier and size if published), background (transparent/opaque/auto — supported on which model?), output_format, output_compression, moderation, input_fidelity (supported?), image[] inputs (max count, formats, max size), mask (format rules), stream + partial_images, user, response_format, style, any new parameter introduced with 2.5 (for example reasoning/effort, aspect_ratio, seed, thinking, safety, "precision" or detail controls). For the Responses API image_generation tool: action (generate/edit/auto), partial_images, input_image_mask, multi-turn editing via previous_response_id / image_generation_call ids, which mainline models can call the tool.
4. What each parameter does to QUALITY vs SPEED vs COST, with concrete recommended settings for: quick draft, standard asset, dense text/infographic, photorealism, product shot, identity-preserving edit, transparent cutout, 4K print/hero, batch of variants.
5. Official prompting guidance specific to 2.5 (structure, text rendering, quoting exact text, layout, camera language, edits with invariants, multi-image references by index, iteration strategy, what to avoid, known failure modes). Summarize the prompting guide faithfully and completely; include any example prompts that illustrate a rule.
6. Known limitations and gotchas (text accuracy, small text, hands, consistency, transparency, sizes that fail, timeouts, content policy / moderation, C2PA metadata, latency spikes, output resolution limits vs what's actually returned).
7. Differences vs gpt-image-2 and gpt-image-1.5 that change how a developer should send requests.

## Output format
Return one Markdown report as your final message:
- Section per question number above.
- A single consolidated parameter table: parameter | endpoint(s) | Flare values/default | Sunburst values/default | effect on quality/speed/cost | source URL.
- Every factual claim ends with its source URL and a tag: [OFFICIAL] or [THIRD-PARTY] and, when sources conflict, list both values and which one you trust and why.
- End with "Open questions" listing anything you could not verify.
Be exhaustive but do not pad: no marketing prose.
