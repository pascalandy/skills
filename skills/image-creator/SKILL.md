---
name: "image-creator"
description: "Use when generating or editing images or animated GIFs from the terminal with OpenAI GPT Image, including requests for best quality (Sunburst) or speed (Flare)."
kind: "general"
api-key: "openrouter"
---

# Image Creator

Use `<skill_dir>/scripts/image_creator.py`. Read [settings](references/guide.md#3-request-reference) when choosing flags, [prompting](references/guide.md#4-write-the-prompt) when composing a brief.

## Steps

1. Pick the route from the request:

   | Request | Route |
   |---|---|
   | an image, with no quality or speed asked | Codex plan: no `--model` |
   | best quality, or Sunburst | `--model sunburst` |
   | fast, quick, or Flare | `--model flare` |
   | a GIF or an animation | `--out <name>.gif` with `--model sunburst`, or `--model flare` when speed is asked |

   The plan has one model chosen by OpenAI's server, fixed quality and size, and no GIF yet. `--model` bills OpenRouter, so before the request's first `--model` run, ask in one line: the plan does not offer this; use paid OpenRouter? In that line, name the quality levels, `low`, `medium`, `high` (default), `xhigh`, and `max`, and pass the one the user names with `--quality`. On no, stay on the plan, or for a GIF, stop
2. Set `--aspect W:H` for composition or `--size WxH` for exact delivery pixels. Add `--transparent` with `.png` or `.webp` for cutouts. Ask about unresolved requirements that have no documented default
3. Name the deliverable, composition, visible details, quoted text, and exclusions. For edits, state the change and what must remain unchanged. For a GIF, state the motion and how the loop closes
4. Run the CLI; use `--prompt-file` for long briefs and `--dry-run` to inspect settings. It answers in one JSON line

   ```sh
   uv run <skill_dir>/scripts/image_creator.py generate --aspect 16:9 --out out/hero.png --prompt "..."
   uv run <skill_dir>/scripts/image_creator.py generate --model sunburst --size 1536x864 --out out/best.png --prompt "..."
   ```

5. View every file under `files`, apply the [checks](references/guide.md#51-checks), and resolve each of the answer's `errors`. A written image that needs attention fails the run and still lists its `files`. `"ok":true` alone does not establish visual quality
6. Retry one variable at a time on the same route. `--quality` and `--model` apply only on OpenRouter
7. Deliver the chosen file, the answer's `backend`, and unresolved defects

Run `doctor` for backend readiness or `generate --help` for flags. There is no paid fallback when the [plan](references/guide.md#7-chatgpt-and-codex-plans) is unavailable. Resizing adds pixels, not native detail
