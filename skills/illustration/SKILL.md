---
name: "illustration"
description: "Use only when explicitly invoked as `illustration`."
---

# Illustration

## Purpose

Design and generate 16:9 inline illustrations for written content. Turn one important argument, process, structure, state, or metaphor into a sparse, strange, readable hand-drawn scene. Do not produce commercial artwork, slide infographics, or cute cartoons.

The recurring character is Xiaohei, a solid-black creature with white dot eyes, thin legs, and a blank expression. Xiaohei seriously performs an absurd but meaningful task and must drive the image's central action rather than decorate the scene.

## Choose the output language

Choose one of the two supported output languages before planning or generating images, or before an edit that adds or replaces copy:

- Follow an explicit user request for English or Canadian French
- Otherwise, use Canadian French when the source content is primarily French
- Otherwise, use English
- For mixed-language source material, use the dominant language unless the user specifies one

Use the chosen language for the shot list, new image labels, captions, and delivery summary. During edits, preserve untouched labels and use the chosen language for any new or replacement copy. Keep image-generation instructions in English if that produces more reliable results. Do not generate new Chinese copy.

## Read references only when needed

Resolve every relative path against the directory containing this `SKILL.md` file.

- Read `references/image-tools.md` before generating or editing an image
- Read `references/style-dna.md` before planning or generating illustrations
- Read `references/xiaohei-ip.md` when defining Xiaohei's appearance or action
- Read `references/composition-patterns.md` when choosing a composition or inventing a metaphor
- Read `references/prompt-template.md` immediately before generating or editing an image
- Read `references/qa-checklist.md` after generation or editing and before delivery
- Open `assets/examples/` only when visual calibration is necessary, never as the default path

The bundled examples contain legacy Chinese labels. Use them only to calibrate line density, whitespace, colour restraint, and Xiaohei's role. Never copy their wording, objects, or composition.

## Choose the mode

- Planning only: complete steps 1 and 2, then stop
- Generate images: complete steps 1 through 5
- Edit an image: skip steps 1 through 3 unless the edit needs source context, apply the requested change with `references/prompt-template.md`, inspect the result, then export and report

## Process

### 1. Understand the source

Read the supplied article, link, Notion page, Markdown file, screenshot, or concept. Identify the central argument, turning points, passages suitable for illustration, and passages that should remain text.

Do not distribute illustrations evenly. Select cognitive anchors such as a central claim, a point where a process breaks, an input-output loop, branching, a before-and-after contrast, reuse, handoff, failure mode, or change in character state.

This step is complete when every proposed illustration earns its place by clarifying one distinct idea.

### 2. Plan before generating

When the user asks only for analysis or illustration ideas, return a shot list. For each image, include:

- Placement after a specific passage
- Theme
- Core idea
- Composition type
- Xiaohei's action
- Suggested objects
- Short labels in the chosen output language

Default to 4 to 8 images. Use 1 to 3 for short pieces and exceed 9 only when the source clearly supports it.

This step is complete when the list covers the strongest visual anchors without turning the article into an illustrated deck.

### 3. Generate each image separately

When the user explicitly asks to generate images, do not pause for confirmation. Select and invoke the image tool according to `references/image-tools.md`. Never combine several planned illustrations into one image.

Each image must explain one central idea and include:

- A 16:9 horizontal canvas
- A pure white background
- Thin black hand-drawn line art
- A few handwritten labels in the chosen output language, using only red, orange, or blue when needed
- Generous whitespace
- Xiaohei performing the central action
- No slide layout, commercial vector style, cute mascot treatment, complex architecture, or composition-type title in the top-left corner

Invent a new strange but coherent metaphor from the current source. Do not reuse known example compositions unless the user explicitly requests a reproduction.

This step is complete when every requested image exists as a separate generated asset.

### 4. Inspect and iterate

Apply `references/qa-checklist.md` to every image. Regenerate or edit an image when Xiaohei is decorative, the canvas is crowded, the result resembles a slide or formal diagram, labels are excessive or unreadable, a type title appears, the style is cute or stiff, or the background is not pure white.

This step is complete when every delivered image passes all required QA checks.

### 5. Export and report

Use an explicit user-provided destination first, then the project's asset convention. Resolve that destination before generating images.

With no specified destination or established convention, use:

```text
assets/<article-slug>-illustrations/
```

Use ordered, descriptive filenames:

```text
01-topic-name.png
02-topic-name.png
```

Use lowercase ASCII kebab-case for portable filenames. Preserve original generated files and do not overwrite existing assets unless the user explicitly requests replacement.

Write the delivery summary in the chosen output language and include:

- Number of images generated
- Purpose of each image
- Export path
- Strongest images and optional images

Keep the summary brief. This step is complete when the files are exported without overwriting existing assets and the user can locate each one.
