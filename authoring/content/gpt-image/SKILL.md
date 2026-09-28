---
name: "gpt-image"
description: "Use when generating or editing a raster image from the terminal, such as a photo, poster, diagram, logo, or transparent cutout, with OpenAI's GPT Image models through a ChatGPT plan or an API key."
---

# GPT Image

`<skill_dir>/scripts/gpt_image.py` generates and edits images. It owns every request setting: backend, model, quality, size, format, candidates, and output checks. You supply an intent, a shape, and a prompt. [The guide](references/guide.md) explains every setting it chooses.

## Steps

1. **Pick the intent** from the user's words: `draft` for a quick idea, `standard` for an everyday image (the default), `high` for a client-facing final, dense text, a product shot, or a portrait, `max` when quality is paramount. Done when one intent is chosen.
2. **Pick the shape.** `--aspect W:H` from where the image will be shown, or `--size WxH` when the delivery needs exact pixels. An edit keeps its first input's size when you pass neither. Add `--transparent` for logos, stickers, and cutouts, with a `.png` or `.webp` output. Done when the shape matches the destination.
3. **Write the prompt** with the rules and template in [guide section 4](references/guide.md#4-write-the-prompt), and the matching row of its use-case table. Done when the prompt names the deliverable, composition, visible details, exact text in quotes with its count, and the exclusions.
4. **Run the CLI.** Pass long prompts with `--prompt-file`.

   ```sh
   uv run <skill_dir>/scripts/gpt_image.py generate --intent high --aspect 16:9 --out out/hero.png --prompt "..."
   uv run <skill_dir>/scripts/gpt_image.py edit --image in.png --out out/in-v2.png --prompt "Change only ... Keep ... unchanged."
   ```

   It prints one line naming the files, or the full receipt with `--json`. Each `warning:` line on stderr names a defect to handle in step 5. Done when the command exits 0.
5. **Inspect every output image** against the checks in [guide section 5.1](references/guide.md#51-checks). When the run produced candidates (`hero-1.png`, `hero-2.png`, …), pick the one that passes the most checks. Done when every output has been viewed and judged.
6. **Iterate one change at a time** with the ladder in [guide section 5.2](references/guide.md#52-the-ladder). With this CLI, "raise `quality`" and "switch to Sunburst" both mean raising `--intent` one step. Done when an output passes every check, or the user accepts it.
7. **Report** the chosen file, the backend from the receipt, and any unresolved warning.

## Backends

`gpt_image.py doctor` shows which backends are ready. The CLI chooses one per run and records why in the receipt:

- **Plan** (default): the user's ChatGPT plan through `codex exec`, with no API key. OpenAI fixes the model (`gpt-image-2`), quality, and a size near 1.57 MP there ([guide section 7](references/guide.md#7-chatgpt-and-codex-plans)). The CLI states the aspect ratio in the prompt, crops and resizes to `--size`, and spends `high` and `max` on 2 and 3 candidates
- **API**: `OPENAI_API_KEY`. Each intent maps to Flare or Sunburst at a quality tier. `high` and `max` use it automatically when a key exists, as do `--mask`, `--model`, and `--quality`. It bills API prices; `--dry-run --json` shows the estimate before any call

`--backend plan` or `--backend api` forces a backend. Run `gpt_image.py generate --help` for the full intent table and every flag.
