# GPT Image research, 2026-09-28

> **Frozen record.** This folder states what was true and tested on 2026-09-28. Never edit it. A later round of research goes in a new sibling folder named `research-YYYY-MM-DD/`, which may cite and supersede this one. For current guidance, read [the guide](../guide.md).

- **Date:** 2026-09-28, 12:52–14:56 UTC (08:52–10:56 EDT)
- **Question:** which request settings affect image quality for `gpt-image-2.5-flare` (A) and `gpt-image-2.5-sunburst` (B), how an agent should pick them from a quick draft to maximum quality, and whether a ChatGPT or Codex plan can reach A and B from the terminal
- **Scope:** this session's desk research, prompt tests, plan-path probes, and CLI live runs. It excludes the OpenRouter backend added to the skill later that day
- **Environment:** Codex CLI 0.157.1 on a ChatGPT Pro plan; GPT-6 Sol (high reasoning) for research, GPT-6 Astra (medium) for tests, GPT-6 Luna (low) as the CLI's plan controller; Claude Opus 5.5 orchestrating. GPT Image 2.5 snapshots were dated 2026-09-08. No OpenAI API key was available

## Files

| File | Content |
|---|---|
| [sol-research-prompt.md](sol-research-prompt.md) | Brief given to GPT-6 Sol |
| [sol-research-report.md](sol-research-report.md) | Sol's report, unedited; two errors are corrected in verification.md |
| [astra-test-prompt.md](astra-test-prompt.md) | The 12-test plan given to GPT-6 Astra |
| [astra-test-results.md](astra-test-results.md) | Astra's results, unedited; its `/tmp` and `/home/pascal` links pointed to working files that were not preserved |
| [verification.md](verification.md) | Documentation cross-check, errors found, token formula, independent image re-check, Codex plan probes, CLI live runs |

## Findings as of 2026-09-28

- Flare and Sunburst bill the same token rates, equal to GPT Image 2's. OpenAI's calculator gives both the same output tokens at the same size and quality, so Sunburst costs time, not money ([verification §4](verification.md#4-output-token-formula))
- Quality drives cost far more than size: at 1024×1024, `max` costs 36 times `low`. The 2.5 models add `xhigh` and `max`; 2.5 `high` bills like GPT Image 2 `medium`
- Always send `model`: the Images API falls back to `dall-e-2` and the Responses tool to `gpt-image-1`
- Neither 2.5 model supports the Batch API
- Codex's built-in image tool requests `gpt-image-2` with `quality`, `size`, and `background` at `auto`, and no Codex setting changes that. The plan endpoint ignores `model`, `quality`, and `size`; a made-up model name returns the same 1254×1254 result ([verification §6](verification.md#6-the-codex-plan-path))
- Therefore a ChatGPT or Codex plan cannot reach Flare or Sunburst, or choose a quality tier, from the terminal. That takes an API key
- On the plan backend, specified prompts controlled composition, light, palette, exact text including accents, chart data, pose, exclusions, and reference roles. Edits kept identity and framing but redrew textures and sometimes added unrequested details ([astra-test-results.md](astra-test-results.md), [verification §5](verification.md#5-independent-re-check-of-the-17-test-images))

## Not verified

- Any Flare or Sunburst output: no API key was available, so every parameter effect above rests on OpenAI's documentation and one third-party benchmark
- Which model the plan backend actually runs, since it ignores the requested model
- Whether 2.5 accepts `input_fidelity`, and how often sizes above 2560×1440 fail
- The 17 test images and probe outputs themselves; this folder keeps text only

## How to tell when GPT Image 2.5 reaches Codex

Check these in a later round and record the results in a new dated folder:

1. The Codex image-generation docs (<https://learn.chatgpt.com/docs/image-generation>) no longer say "Built-in image generation uses `gpt-image-2`"
2. A traced Codex image call (`RUST_LOG=codex_http_client::transport=trace`) sends a 2.5 model instead of `"model": "gpt-image-2"`
3. The plan endpoint rejects a made-up model name, or returns different sizes, quality values, or output tokens for different requested models and quality tiers
4. The Codex CLI changelog or `codex features list` mentions image model or quality selection
