# Image tools

## Select the tool

1. Use the image tool explicitly requested by the user
2. Otherwise, use the default tool below
3. If a user-selected tool is unavailable, explain the limitation and ask before switching tools

## `image-creator` (default)

The `image-creator` skill is the default image tool in every harness, through the Codex plan.

- Load `image-creator` before generating or editing an image, and follow its steps
- Use the Codex plan backend (`--backend plan`); select OpenRouter only when the user explicitly requests that backend or GPT Image 2.5, as `image-creator` documents
- Pass `--aspect 16:9`, the filled prompt template through `--prompt-file`, and a `.png` output path through `--out`
- Run one command per planned illustration; inspect every returned candidate and keep the one that passes the QA checklist. On the plan, Draft and Standard return one candidate, High (the default) two, and Max three
- Pass every user-provided reference image with `edit --image`, repeating `--image` in the supplied order

If `image-creator` is unavailable or its `doctor` reports that the Codex plan is not connected, report the limitation and stop. Use a paid backend only when the user explicitly requests it; an unavailable plan does not authorize a paid fallback.
