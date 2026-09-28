> Frozen research record, 2026-09-28. Claude Opus 5.5's own verification work, written from the working files and session notes of that day. Times are UTC; local time was EDT (UTC−4). Claims marked *(session record)* come from command output seen during the session and not saved to a file; claims marked *(re-checked)* were run again on 2026-09-28 while this record was written. Index: [README](README.md).

# Verification, 2026-09-28

## 1. Method

| Role | Who | How | When (UTC) |
|---|---|---|---|
| Orchestration, verification, writing | Claude Opus 5.5 in Claude Code | read raw documentation, measured images, ran probes | 12:50–15:00 |
| Desk research | GPT-6 Sol, high reasoning | `codex exec`, read-only, live web search; brief in [sol-research-prompt.md](sol-research-prompt.md) | 12:52–12:57 |
| Prompt-behavior tests | GPT-6 Astra, medium reasoning | `codex exec`, Codex built-in image tool, 17 images; plan in [astra-test-prompt.md](astra-test-prompt.md) | 12:56–13:12 |
| Plan-path probes | Claude Opus 5.5 | Codex trace log, config probe, 8 direct endpoint calls | 13:32–13:38 |
| CLI live runs | `gpt_image.py` v0.1.0 working copy | plan backend, controller GPT-6 Luna at low reasoning | 13:58–14:56 |

Environment: Codex CLI 0.157.1, logged in with a ChatGPT Pro plan. No `OPENAI_API_KEY` was available, so no Images API or Responses API request ran, and no output was independently verified as GPT Image 2.5.

Commands *(session record)*:

```sh
# Desk research, run in /tmp/gpt-image-25-research
codex exec -C /tmp/gpt-image-25-research --skip-git-repo-check -s read-only -c 'approval_policy="never"' -c 'web_search="live"' -m gpt-6-sol -c 'model_reasoning_effort="high"' --json -o result.md - < prompt.md

# Prompt-behavior tests, run in /tmp/gpt-image-25-tests
codex exec -C /tmp/gpt-image-25-tests -s workspace-write -c 'approval_policy="never"' -c 'sandbox_workspace_write.network_access=true' -m gpt-6-astra -c 'model_reasoning_effort="medium"' --json -o result.md - < prompt.md

# Trace of one built-in image call
RUST_LOG='codex_image_generation_extension=trace,codex_http_client=trace,codex_api=trace,reqwest=debug,hyper=info' codex exec -C "$(mktemp -d)" -s read-only -c 'approval_policy="never"' -m gpt-6-luna -c 'model_reasoning_effort="low"' --json "Call the image generation tool exactly once with the prompt: 'A red circle on white.' Then reply DONE." < /dev/null
```

The eight direct probes in section 6 sent `POST https://chatgpt.com/backend-api/codex/images/generations` with the Codex login's bearer token, `originator: codex_cli_rs`, the `ChatGPT-Account-ID` header, and a JSON body of `prompt`, `background: "auto"`, `model`, `quality`, and `size`.

## 2. Official documentation cross-check

Pages were fetched as Markdown by appending `.md` to developers.openai.com URLs between 12:53 and 13:04, from docs build `dpl_CuZKaKD9SpW2BQLdmdFR2chBnnPT`. The Codex docs on learn.chatgpt.com were fetched at 13:36–13:37. openai.com returned HTTP 403 *(session record)*, so the launch post was read through its copy on the OpenAI community forum (posted 2026-09-08T19:12Z).

| Page | Facts confirmed |
|---|---|
| `api/docs/models/gpt-image-2.5-flare` and `…-sunburst` | IDs and snapshots `…-2026-09-08`; Image generation and Image edit endpoints supported; Batch marked "Not supported"; usable as the Responses `image_generation` tool model; token prices text $5 / $1.25 cached, image input $8 / $2 cached, image output $30 per million; rate limits in images per minute: Tier 1 5, Tier 2 20, Tier 3 50, Tier 4 150, Tier 5 250; quality `low`, `medium`, `high`, `xhigh`, `max`, `auto` |
| `api/docs/guides/image-generation` | Size rules (multiples of 16, edge ≤ 3840, ratio ≤ 3:1, 655,360–8,294,400 px); sizes above 2560×1440 experimental; transparency needs PNG or WebP; JPEG faster than PNG; cached input only through the Responses tool; each partial image adds 100 output tokens; `moderation` `auto` or `low`; `image_generation_user_error` and `moderation_blocked` with `moderation_details`; complex prompts up to 2 minutes; mask needs alpha, same size and format, applies to the first image; the embedded token calculator (section 4) |
| `api/docs/guides/image-prompting` | Flare "comparable to GPT Image 2", Sunburst "higher image quality than GPT Image 2"; model choice and migration procedure; eight prompting fundamentals; example request settings per use case; outputs above 3,686,400 px experimental |
| `api/reference/resources/images` | Prompt up to 32,000 characters; `model` defaults to `dall-e-2` unless a GPT Image parameter is present; `n` 1–10; `output_compression` default 100; responses report `quality`, `size`, `usage`; edits take up to 16 images as JSON `images[]`; `input_fidelity` listed without a 2.5 rule |
| `api/reference/resources/responses` | `image_generation` tool fields: `action`, `background`, `input_fidelity`, `input_image_mask`, `model` (default `gpt-image-1`), `moderation`, `output_compression`, `output_format`, `partial_images`, `quality`, `size`; no `n` |
| `api/docs/guides/tools-image-generation` | `tool_choice: {"type": "image_generation"}`; JPEG not allowed with a transparent background; prefer "draw" or "edit" wording |
| `api/docs/pricing` | Standard table: both 2.5 models at the same rates as GPT Image 2. Batch table: GPT Image 2 at half price, no 2.5 rows |
| `api/docs/guides/batch` | Lists the image endpoints in general, without naming models |
| learn.chatgpt.com `docs/image-generation` | "Built-in image generation uses `gpt-image-2` and counts toward your general Codex usage limits" |
| learn.chatgpt.com `docs/pricing` | Image turns use included limits 3–5 times faster; no image generation on the Free plan; with an API key, API pricing applies |

## 3. Errors found and corrected

In [sol-research-report.md](sol-research-report.md):

1. **Batch support.** The report says Batch accepts 2.5 through the image endpoints and recommends Batch for variants. Both 2.5 model pages mark Batch "Not supported", and the pricing page lists no 2.5 Batch rate. The Batch guide's endpoint list is generic
2. **"Pricing conflict".** The report says the pricing table lists GPT Image 2 at half the 2.5 rates. Those half rates are the Batch table; the Standard table lists identical rates
3. **Unverified token figures.** The report marks the 1024×1024 token counts (196, 439, 1,756, 3,122, 7,024) as third-party and unverified. They match the official formula in section 4 exactly
4. **Latency claim.** The report attributes "up to 50% lower latency for Flare than GPT Image 2" to the launch post. The forum copy of the post does not say it. DataNorth's coverage (<https://datanorth.ai/news/openai-launches-chatgpt-images-2-5>, 2026-09-09) says Images 2.5 "cuts the wait for an image by up to 50% compared with Images 2.0" *(re-checked)*

In [astra-test-results.md](astra-test-results.md):

5. **Which model ran.** The tests were designed as GPT Image 2.5 tests, but section 6 later showed the built-in tool requests `gpt-image-2`, which OpenAI's Codex docs also name, and no response identifies the serving model. No output was verified as 2.5, so the tests count as prompt-behavior evidence only
6. **T09 hypothesis.** "A second edit compounds drift" was not supported: the second edit changed less than the first

In Claude's first guide draft, fixed before or during PR 123:

7. The Draft tier cost omitted $0.006 at 1024×1024
8. The cost of a reference image appeared as both $0.01 and $0.011; the benchmark gives $0.010573 per fixed-tier image, for the reference image and its conditioning instructions
9. Added latency from one reference image was given as 1–7 s; the benchmark range is 0–7.1 s at 1024×1024 fixed tiers, and other conditions fall outside it (section 4)
10. T09 was summarized as "about 2% of pixels changed", from a grayscale metric that undercounts a blue-for-orange change
11. A size rule said prompt words never set the output size, but "16:9" did set the aspect ratio on the Codex tool
12. Alpha-threshold advice carried no inference tag
13. "The Images API sends your prompt unchanged" is not documented
14. T09 was described as adding "lit harbor windows"; the evidence shows warm harbor lights
15. The draft claimed every image had been inspected before T05a had been viewed
16. The draft said edit drift compounds across a chain, citing T09, which does not support it
17. The draft said Codex's built-in tool runs Images 2.5; section 6 shows it requests `gpt-image-2`

## 4. Output-token formula

Source: the `GptImageTokenCalculator` component embedded in the image generation guide (asset `GptImageTokenCalculator.react.DjdUjwEe.js`, SHA-256 prefix `72092424ca64a0bc`). It labels one model option "GPT Image 2.5 (Sunburst and Flare)", so both models share one formula.

```python
import math

GRID = {"low": 16, "medium": 24, "high": 48, "xhigh": 64, "max": 96}  # GPT Image 2: low 16, medium 48, high 96

def output_tokens(width: int, height: int, quality: str) -> int:
    long_grid = GRID[quality]
    scaled = long_grid / (max(width, height) / min(width, height))
    floor = math.floor(scaled)
    short_grid = floor + floor % 2 if scaled - floor == 0.5 else round(scaled)
    return math.ceil(long_grid * short_grid * (2_000_000 + width * height) / 4_000_000)

# cost in USD = output_tokens(width, height, quality) * 30 / 1_000_000
```

Output tokens and image-output cost per image:

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

Validation: Genflick's benchmark (<https://genflick.com/blog/gpt-image-2-5-cost-speed-benchmark>, dated 2026-09-08) derives its costs from returned `usage`. Its per-image costs equal the formula plus about 100 text-input tokens at every size compared here: 1024×1024 (all five tiers) and 1536×864, 2560×1440, and 3840×2160 (`low` and `high`); for example `high` at 3840×2160 costs $0.1001 by formula and $0.1006 measured. Its 1536×1024 results were not compared. It also reports identical costs for Flare and Sunburst at matching settings.

What the formula implies: the token grid depends only on quality and aspect ratio, and pixel count only scales the cost; `max` costs about 36 times `low` at 1024×1024, while `high` at 3840×2160 costs about twice `high` at 1024×1024; 2.5 `high` bills like GPT Image 2 `medium`, and 2.5 `max` like GPT Image 2 `high`.

The same benchmark measured median seconds at 1024×1024, PNG, no streaming, three calls per cell (third-party, not re-measured here):

| Model | low | medium | high | xhigh | max | auto |
|---|---:|---:|---:|---:|---:|---:|
| Flare | 10.4 | 13.8 | 18.1 | 26.7 | 45.6 | 15.9 |
| Sunburst | 15.7 | 18.1 | 29.9 | 46.7 | 85.0 | 22.9 |
| GPT Image 2 | 23.0 | 48.1 | 154.7 | n/a | n/a | n/a |

Two of three Sunburst calls completed at `low` and at `high`. Single calls at larger sizes: Flare `high` 15.8 s at 1536×864 and 27.5 s at 3840×2160; Sunburst `high` 27.9 s and 33.5 s. Adding a reference image with its conditioning instructions changed the 1024×1024 medians by 0 to 7.1 s across fixed tiers and up to 12.3 s at `auto`; single calls at larger sizes ranged from −12.5 s (Sunburst `low`, 1536×864) to +21.4 s (Sunburst `high`, 3840×2160).

## 5. Independent re-check of the 17 test images

Claude viewed every image Astra produced and recomputed the measurements with Pillow.

- **Sizes.** Every output held about 1.57 million pixels: 1254×1254, 1145×1374, 1370×1148, 1536×1024, 1672×941. Four of these five sizes break the API's multiple-of-16 rule; 1536×1024 satisfies it. Both 16:9 prompts returned 1672×941, including "Output size exactly 3840x2160 pixels"
- **Time.** 21–58 s per call, median 33 s, measured around the tool call
- **Verdicts.** Agreed with Astra's checks on T01–T12. Notable direct observations: T01's bare prompt returned a generic sunset postcard while the specified prompt followed placement, light, and palette; T02's two prompt formats gave near-identical images; T03 rendered "PÂTISSERIE ONDINE" and "Montréal · depuis 1987" exactly; T04's labels, values, ticks, and footnote were exact; T10 followed the numbered roles, but the fox's warm rim light did not match the blue-hour scene; T11 read "left side" as the viewer's left
- **Transparency (T06).** RGBA with transparent corners; 47.7% of pixels fully transparent; subject alpha 253–254 rather than 255 (96.5% of non-transparent pixels at 250 or above); about 15,000 pixels at alpha 1–2 around the subject
- **Edit drift (T09).** Grayscale mean absolute difference, 0–255, after converting to grayscale and resizing to 256 px wide with Pillow's default resampling *(session record)*: 16.77 from T07 to T09a and 4.43 from T09a to T09b; pixels differing by more than 30: 13.9% and 2.0%. Astra's Lanczos resize gave 16.86 and 4.52. Both edits kept identity, pose, and framing; the snow edit added warm harbor lights, and the net edit redrew beard and fabric texture

## 6. The Codex plan path

1. **Tool arguments.** Strings in the Codex CLI 0.157.1 binary define the built-in tool's input as `ImagegenArgs` with `prompt`, `referenced_image_paths`, and `num_last_images_to_include` ("struct ImagegenArgs with 3 elements") *(re-checked)*. It has no model, quality, or size argument
2. **Traced request.** With `RUST_LOG='codex_image_generation_extension=trace,codex_http_client=trace,codex_api=trace,reqwest=debug,hyper=info'` (13:32), Codex sent `POST https://chatgpt.com/backend-api/codex/images/generations` with `{"prompt": "...", "background": "auto", "model": "gpt-image-2", "quality": "auto", "size": "auto"}`. Response headers reported plan type `pro`, 32% of a 10,080-minute usage window used
3. **Config keys.** `codex exec --strict-config` rejected `image_generation.model`, `tools.image_generation.model`, `imagegen.model`, `image_gen.model`, `tools.image_gen.model`, and `image_generation_model` with "unknown configuration field" *(session record; the first key re-checked)*. Other keys were not tried
4. **Direct probes (T13).** Eight calls to that endpoint with the Codex login and the prompt "A red circle on white.":

| Time | Requested model | quality | size | Returned size | Returned quality | Output tokens | Seconds |
|---|---|---|---|---|---|---:|---:|
| 13:34:34 | `gpt-image-2.5-flare` | low | 1024x1024 | 1254x1254 | low | 515 | 23.35 |
| 13:35:11 | `gpt-image-2.5-sunburst` | low | 1024x1024 | 1254x1254 | low | 515 | 22.71 |
| 13:35:13 | `gpt-image-2.5-flare` | low | 1536x1024 | 1254x1254 | low | 515 | 23.93 |
| 13:35:11 | `gpt-image-9-bogus` | low | 1024x1024 | 1254x1254 | low | 515 | 22.15 |
| 13:35:35 | `gpt-image-2.5-flare` | max | 1024x1024 | 1254x1254 | low | 515 | 22.00 |
| 13:35:36 | `gpt-image-2.5-flare` | low | 3840x2160 | 1254x1254 | low | 515 | 23.12 |
| 13:35:37 | `gpt-image-2` | low | 1024x1024 | 1254x1254 | low | 515 | 23.84 |
| 13:37:43 | `gpt-image-2` | high | 1024x1024 | 1254x1254 | low | 515 | 23.44 |

   All returned HTTP 200. A made-up model name succeeding means the response never proves which model ran
5. **OpenAI's statement.** The Codex docs say built-in image generation uses `gpt-image-2` (section 2)
6. **Independent corroboration.** OmniRoute issue #14617 (<https://github.com/diegosouzapw/OmniRoute/issues/14617>, measured 2026-09-23 with a Pro login) found that the Codex chat route's hosted `image_generation` tool reports `gpt-image-2-codex` whatever model is requested, that the dedicated images route accepts a nonexistent model with HTTP 200, and that neither route honors `size`
7. **Third-party "2.5 through a plan" tools.** `the-jey/codex-sub-imagen` advertises Sunburst at `xhigh` through a Codex login, and `jdmnk/codex-imagegen-cli` calls the same endpoints, according to their READMEs *(session record)*. Neither shows which model served a request; treated as unverified
8. **Codex's own fallback script.** `scripts/image_gen.py` in the Codex 0.157.1 `imagegen` skill *(re-checked)* defaults to `gpt-image-2`, accepts only `low`, `medium`, `high`, `auto` quality, and limits models other than `gpt-image-2` to 1024×1024, 1536×1024, 1024×1536, and `auto`
9. **`codex exec` as a backend.** With `--ephemeral`, the image still lands in `$CODEX_HOME/generated_images/<thread-id>/`; `--disable computer_use --disable browser_use --disable in_app_browser` kept the controller on the image tool; the trace line shows the exact prompt sent; startup took about 7 s before the image request

Conclusion as of 2026-09-28: the tested Codex route did not honor the requested model, quality, or size, and no verified plan-based way to select Flare or Sunburst was found. OpenAI's Codex docs name `gpt-image-2` for the built-in tool; the documented way to select a 2.5 model is the API.

## 7. CLI live runs

Working copies of `gpt_image.py` v0.1.0 on the plan backend, before commit `262e953` was made:

| Time | Command | Settings | Seconds | Prompt sent verbatim | Result |
|---|---|---|---:|---|---|
| 13:58:42 | `generate` | `--size 1536x864`, bicycle photograph | 33.0 | yes | 1536×864 RGB, resized down from 1672×941 |
| 13:59:25 | `edit` | recolor the bicycle, input 1536×864 | 35.5 | yes | 1672×941 RGB; only the requested change |
| 14:00:30 | `generate` | `--transparent --aspect 1:1`, cat sticker | 57.4 | yes | 1254×1254 RGBA, transparent corners, 42.4% transparent |
| about 14:55 | `generate` | `--intent max --aspect 2:3`, poster prompt below | 44.8 CLI-reported: the longest of three parallel calls; total wall time not recorded | not recorded (no `--json`) | three 1024×1536 candidates; text exact in all three; each added mountains and a lake the prompt did not request |

The edit returning 1672×941 instead of its input's 1536×864 led to the rule that an edit keeps its first input's size, added before the poster run *(session record)*.

Poster prompt *(session record)*:

```text
Minimal concert poster, screen-print style, two ink colors: deep navy and warm orange on cream paper. Centered headline, exactly once, bold condensed sans-serif: "NORTHERN LIGHTS". Below it, exactly once, small caps: "Montréal · 14 novembre 2026". A single stylized aurora band above the headline. No other text, no logo, no watermark.
```
