---
name: "gpt-image"
description: "Use when generating or editing raster images from the terminal with OpenAI GPT Image models through a Codex plan or, when explicitly requested, OpenRouter."
---

# GPT Image

Use `<skill_dir>/scripts/gpt_image.py`. Read [settings](references/guide.md#3-request-reference) when choosing flags, [prompting](references/guide.md#4-write-the-prompt) when composing a brief.

## Steps

1. Default to the Codex plan with `gpt-image-2`. Only when the user explicitly requests 2.5, use OpenRouter with `OPENROUTER_API_KEY`: `--model flare` for generic 2.5 or Flare, `--model sunburst` for Sunburst. A high-quality request alone does not authorize switching modes
2. Choose an [intent](references/guide.md#2-tiers), then set `--aspect W:H` for composition or `--size WxH` for exact delivery pixels. Add `--transparent` with `.png` or `.webp` for cutouts
3. Name the deliverable, composition, visible details, quoted text, and exclusions. For edits, state the change and what must remain unchanged
4. Run the CLI; use `--prompt-file` for long briefs and `--dry-run --json` to inspect settings and estimated output cost

   ```sh
   uv run <skill_dir>/scripts/gpt_image.py generate --intent high --aspect 16:9 --out out/hero.png --prompt "..."
   uv run <skill_dir>/scripts/gpt_image.py generate --model flare --quality high --size 1536x864 --out out/2.5.png --prompt "..."
   ```

5. View every output, apply the [checks](references/guide.md#51-checks), and resolve stderr warnings. Exit 0 alone does not establish visual quality
6. Retry one variable at a time within the chosen mode. OpenRouter exposes `--quality` and `--model`; the plan does not. Hold other settings fixed; changing `--intent` can change several together
7. Deliver the chosen file, receipt backend, and unresolved defects

Run `doctor` for backend readiness or `generate --help` for flags. There is no paid fallback when the [plan](references/guide.md#7-chatgpt-and-codex-plans) is unavailable. Its `high` and `max` intents request more candidates; resizing adds pixels, not native detail
