---
name: "image-creator"
description: "Use when generating or editing images or animated GIFs from the terminal with OpenAI GPT Image, including requests that name Flare, Sunburst, a quality level, or the API."
kind: "general"
api-key: "openrouter"
model-version: "2.6"
---

# Image Creator

Use `<skill_dir>/scripts/image_creator.py`. Read [settings](references/guide.md#3-request-reference) when choosing flags, [prompting](references/guide.md#4-write-the-prompt) when composing a brief.

## Steps

1. Pick the route from the request, without asking the user:

   | Request | Route |
   |---|---|
   | an image, even one that names Flare, Sunburst, a quality, or speed | Codex plan: no `--model` |
   | an image that names the API or OpenRouter | `--model sunburst`, or `--model flare` when it names speed or Flare |
   | a GIF or an animation that names the API or OpenRouter | `--out <name>.gif` on the API route above |
   | a GIF or an animation without the API | stop: the plan has no GIF yet; the API has it |

   The plan is the user's Codex subscription: Images 2.6, with the model chosen by OpenAI's server and a fixed quality and size. Flare, Sunburst, quality levels, and GIF exist only through the API, which bills OpenRouter. A request that names the API is the consent to pay: pass the quality it names with `--quality` (`low`, `medium`, `high`, `xhigh`, or `max`, which "maximum" means), or keep the default `high`
2. Set `--aspect W:H` for composition or `--size WxH` for exact delivery pixels. Add `--transparent` with `.png` or `.webp` for cutouts. Ask about unresolved requirements that have no documented default
3. Name the deliverable, composition, visible details, quoted text, and exclusions. For edits, state the change and what must remain unchanged. For a GIF, state the motion and how the loop closes
4. Run the CLI; use `--prompt-file` for long briefs and `--dry-run` to inspect settings. It answers in one JSON line

   ```sh
   uv run <skill_dir>/scripts/image_creator.py generate --aspect 16:9 --out out/hero.png --prompt "..."
   uv run <skill_dir>/scripts/image_creator.py generate --model sunburst --size 1536x864 --out out/best.png --prompt "..."
   ```

5. View every file under `files`, apply the [checks](references/guide.md#51-checks), and resolve each of the answer's `errors`. A written image that needs attention fails the run and still lists its `files`. `"ok":true` alone does not establish visual quality
6. Retry one variable at a time on the same route. On the plan, change the prompt or the shape flags; `--quality` and `--model` apply only on OpenRouter
7. Deliver the chosen file, its route, model, and quality, and unresolved defects. On the plan, that is the Codex plan, Images 2.6, quality fixed by OpenAI; when the request named Flare, Sunburst, or a quality, add in one line that this choice needs the API

Run `doctor` for backend readiness or `generate --help` for flags. There is no paid fallback when the [plan](references/guide.md#7-chatgpt-and-codex-plans) is unavailable. Resizing adds pixels, not native detail
