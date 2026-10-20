# Design direction

Read when visual decisions remain open.

## HTML communication defaults

For `html-mode`, use these defaults unless user or project decisions override them.

- Keep layout dense and scannable, like a specification. No hero or decorative cards, pills, or other chrome
- Use true black (`#000`) backgrounds, white primary text, and dark gray only for secondary surfaces or accents
- Avoid marketing voice, em dashes, and light-gray subtitle lines above sections

## Pages for readers

For readers outside the team, such as a client page from a source document, replace the defaults above:

- Take branding from the source. Trace raster logos with `potrace` and sample their colours. Never replace a logo with type
- Open with one headline and one line, then content. Put secondary marks, such as partner badges, in the footer
- In split layouts, put text left and the map or picture right
- As readers progress, highlight the current part elsewhere on the page
- Organize real information with a metaphor, such as a stage map or ticket title. Remove decoration without information, such as punch holes or stamps
- No purple accent. Light surfaces may resemble paper. For dark palettes, use the quality bar
- Before components, set tokens for two section spacings, one radius scale, two durations, and one easing. Use `--t-quick` for hover and `--t-state` for state changes

## Choose a register

Choose direction from subject, audience, and purpose. Base composition on the subject's materials, tools, notation, or work context.

- Workmanlike for operational plans, briefs, and tools. Use quiet hierarchy, precise spacing, and restrained styling
- Editorial for explainers, launches, research stories, and presentations needing stronger composition and deliberate pacing
- Expressive when an immersive visual or interaction is part of the message

Keep wireframes low fidelity. Match styling to the review question.

Before CSS, record visual premise, hierarchy, layout, color roles, type roles, density, and meaningful interaction. Use the brief to choose color and font counts. System fonts are valid. Embed custom fonts only when their value justifies their weight and their license permits it.

## Compose deliberately

- Use a consistent type scale and prose lines around 65 characters. Balance headings and space paragraphs
- Space sibling groups with grid or flex gaps. Keep the cascade simple so component rules preserve layout
- Use tabular numerals where numbers align in columns
- Use numbering, dividers, labels, and grouping for actual hierarchy or sequence
- Name effects in control labels. Explain failures and recovery in errors
- Keep status colors distinct from decorative accents and pair them with another state cue
- Emphasize the argument and keep surrounding content quieter

If both themes are required, define palette tokens for components. Put OS-preference overrides before explicit root `data-theme` overrides so manual selection wins both ways. Verify both palettes. For single-theme projects, add no theme system.

Before delivery, check that content shaped the composition. If a different subject could reuse the design unchanged, revise hierarchy, notation, type, or interaction within the user's chosen style.
