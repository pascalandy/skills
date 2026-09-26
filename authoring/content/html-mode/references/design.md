# Design direction

Read when visual decisions remain open. Existing user and project decisions constrain the choices below.

## HTML communication defaults

These defaults constrain the choices below for artifacts created through `html-mode`. Explicit user and project decisions take precedence.

- Keep the layout dense and scannable, like a specification. Do not add a hero or decorative chrome such as cards or pills
- Use true black (`#000`) for the background, white primary text, and dark gray only for secondary surfaces or accents
- Avoid marketing voice, em dashes, and light-gray subtitle lines above sections

## Choose a register

Anchor the direction in the subject, audience, and purpose. Derive composition from the subject's materials, tools, notation, or working context.

- Workmanlike for operational plans, briefs, and tools. Use quiet hierarchy, precise spacing, and restrained treatment
- Editorial for explainers, launches, research stories, and presentations that benefit from a stronger composition and deliberate pacing
- Expressive when an immersive visual or interactive idea is itself part of the message

Keep wireframes low fidelity regardless of the subject. Scale treatment to the review question.

Before CSS, record the visual premise, hierarchy, layout, color roles, type roles, density, and any interaction that carries meaning. Let the number of colors and fonts follow the brief. System fonts are valid; embed custom fonts only when their value justifies the weight and their license permits it.

## Compose deliberately

- Use a consistent type scale and readable prose measures around 65 characters; balance headings and give paragraphs breathing room
- Use grid or flex gaps to space sibling groups and keep the cascade simple enough that component rules preserve the layout
- Use tabular numerals where numbers align in columns
- Let numbering, dividers, labels, and grouping express actual hierarchy or sequence
- Write control labels that name their effect; errors explain the failure and the recovery action
- Keep status colors distinct from decorative accents and pair them with another state cue
- Concentrate editorial emphasis where it supports the argument, leaving surrounding content quieter

If both themes are required, define palette tokens and let components consume them. Put OS-preference token overrides before explicit root `data-theme` overrides so manual selection wins in both directions. Verify both palettes. A project's single-theme policy needs no additional theme system.

Before delivery, check whether the composition supports this particular content. If it could be reused unchanged for a different subject because the content never influenced it, revise the hierarchy, notation, type, or interaction within the user's chosen style.
