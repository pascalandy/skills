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
- Run one command per planned illustration; inspect every file in the answer's `files` and keep the candidate that passes the QA checklist
- Write candidates to a scratch folder outside the export destination, using a fresh output stem for each retry. Preserve the originals and copy the kept candidate to the filename required by step 5 of the illustration playbook
- Pass every user-provided reference image needed for the result with `edit --image`, repeating `--image` in the supplied order. If required references exceed the plan's input limit, report the limitation instead of dropping them or changing backend

In Codex, the plan CLI needs network access and writes under the Codex home. If a sandbox blocks these, follow the harness's permission workflow; if access remains unavailable, report the permission limitation and stop. A sandbox denial does not establish that the plan is disconnected.

If `image-creator` is unavailable or its `doctor` reports that the Codex plan is not connected, report the limitation and stop. Use a paid backend only when the user explicitly requests it; an unavailable plan does not authorize a paid fallback.
