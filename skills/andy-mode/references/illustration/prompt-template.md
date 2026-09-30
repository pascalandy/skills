# Image-generation prompt template

Generate each image separately. Replace every variable with material from the current source and never combine several images into one.

```text
Generate one standalone 16:9 horizontal article illustration.

Output language:
{English or Canadian French}

Visual DNA:
Pure white background. Minimalist black hand-drawn line art. Slightly wobbly pen lines. Lots of empty white space. Sparse handwritten annotations in the output language, using only red, orange, or blue when needed. Clean absurd product-sketch feeling. No gradients, shadows, paper texture, complex background, commercial vector style, slide-infographic look, cute mascot poster, children's illustration, or realistic UI.

Recurring IP character required:
Xiaohei, a small solid-black absurd creature with white dot eyes, tiny thin legs, a blank serious expression, and a slightly uneven hand-drawn body shape. Xiaohei must perform the core conceptual action, not decorate the scene. Make Xiaohei serious, deadpan, and slightly bizarre, not cute.

Theme:
{illustration theme}

Structure type:
{Workflow / system detail / before and after / character states / conceptual metaphor / layered method / route map / mini comic}

Core idea:
{one idea this image must communicate}

Composition:
{where Xiaohei is, what Xiaohei does, the main object, and how information moves}

Suggested elements:
{element 1} / {element 2} / {element 3} / {element 4}

Handwritten labels in the output language:
{label 1} / {label 2} / {label 3} / {label 4} / {optional label 5}

Colour use:
Black for main line art and Xiaohei. Orange for the main flow, path, or arrows. Red only for key warnings, problems, or results. Blue only for secondary notes, feedback, or system state.

Constraints:
One image explains only one core idea. Keep the main subject around 40% to 60% of the canvas. Preserve at least 35% blank white space. Prefer 3 to 5 short handwritten labels and never exceed 8. Do not write a title in the top-left corner. Do not write the composition type on the image. Do not make it a formal diagram, course slide, or dense explainer. Do not copy prior examples or reuse known case compositions unless explicitly requested. Invent a fresh visual metaphor for this specific article. It should be clear without becoming instructional, interesting without becoming childish, and strange without becoming cluttered.
```

## Image-editing prompts

Remove a top-left title:

```text
Edit the provided image. Remove only the handwritten title "{text to remove}" and its underline from the top-left corner. Fill that area with the same clean white background as the surrounding canvas. Preserve everything else exactly, including characters, labels, paths, line style, composition, aspect ratio, and image quality. Do not add text or objects.
```

Make Xiaohei more integral to the metaphor:

```text
Regenerate this illustration with the same core meaning and simple layout, but make Xiaohei central to the conceptual action. Xiaohei should perform the strange work that explains the idea rather than stand beside the diagram. Keep it clean, sparse, hand-drawn, and not cute. Preserve existing labels unless the user asks to translate them. Write any new or replacement copy in {English or Canadian French}.
```
