# Prototype formats

Adapted from Matt Pocock's logic and UI prototype formats. The Prototype playbook owns scope, scratch isolation, verification, and handoff. These formats do not authorize changes to production components.

## Explore a logic or state model

Build one self-contained HTML file with inline CSS and JavaScript so the user can open it without a server.

- State the question in a short visible introduction
- Keep the model separate from DOM handlers, using a reducer, state machine, or pure functions appropriate to the question
- Render the full relevant state as labelled fields in domain language after every action
- Provide free-play buttons for each action and a reset to the initial state
- Add guided scenarios for the normal path, an awkward edge case, and a forbidden transition when relevant. Each scenario starts from known state and offers real buttons for its steps
- Keep state in memory unless persistence is the question being investigated

Record the observed behavior and decision. Pass the validated model to Feature or architect as evidence; implementation remains a separate authorized step.

## Compare UI layouts

Build about three structurally different variants in the same scratch prototype. Keep representative content, density, and surrounding navigation consistent so differences remain comparable.

- Vary layout, information hierarchy, or primary interaction, rather than only colors or copy
- Label each variant and provide one shared switcher. A URL query parameter may preserve the selected variant when sharing or reloading the scratch page
- If arrow keys switch variants, do not intercept them while an input, textarea, or editable element has focus
- Use representative fixtures. Keep any mutations local to the prototype
- Capture each variant and record which parts the user selected, including combinations across variants

Keep the artifact available at the reported scratch path for review. Do not promote the switcher or prototype code into production as part of this playbook.
