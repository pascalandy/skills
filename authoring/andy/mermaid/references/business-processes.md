# Business Processes

Use this reference for Mermaid diagrams that must show a business or operational process, its decisions, and the responsibilities of several teams, roles, or systems.

These conventions are reusable presentation defaults. Project-specific preferences remain authoritative after the applicable preference preflight.

## Choose the view

Prefer `sequenceDiagram` for a cross-team process when the reader must understand:

- the main path from top to bottom
- who owns each action
- the handoffs between roles and systems
- the decisions that redirect or stop the path
- the responsibilities that remain visible from beginning to end

Use native [`swimlane-beta`](https://mermaid.js.org/syntax/swimlanes.html) when ownership lanes and decisions are the main subject and the target supports Mermaid 11.16.0 or later. This is not a full BPMN implementation. Keep sequences for message order and handoffs, especially on older hosts. See [recent diagram compatibility](emerging-perspectives.md).

Use a vertical `flowchart` when the decision tree or logical progression matters more than handoffs. Flowchart `subgraph` groups can suggest lanes, but their layout is not reliably lane-like.

## Participants and lifelines

- Order participants according to the logical path
- Keep participants and lifelines neutral by default
- Use color around a participant group only when it communicates a confirmed responsibility boundary
- Do not color a participant merely to signal importance
- Do not represent a system as an autonomous business actor when an operator acts through it
- Do not add a participant solely to influence spacing

## Phases

Display a confirmed phase as a spanning note:

```text
Note over <first participant>,<last participant>: PHASE N — <action or result>
```

A phase should help the reader locate a coherent block of work. Its boundary must come from the process semantics, not from a need to balance the diagram visually. The business-analysis method determines the number and meaning of phases.

## Decisions

When a process uses the symbolic decision convention, announce a closed question with:

```text
DecisionMaker->>DecisionMaker: 🔷 Point de décision : <closed question>?
```

Use the symbols only with these stable meanings:

- `🔷` — decision point
- `⛔` — negative or stopping path
- `✅` — positive path and return to the main flow

The symbols are an explicit exception to Mermaid’s default preference to avoid emojis. Validate the target renderer before delivery.

### Negative path

Keep the negative response close to the decision in a local `break` fragment:

```text
break ⛔ Non — <state or consequence>
    <negative-path actions>
end
```

- Cover only the participants involved in the negative response
- State the consequence of `Non`
- Avoid a frame that encloses the rest of the process
- Treat this as a visual convention: UML normally uses `break` for interruption of an interaction

### Positive path

Return visibly to the main path with a spanning note:

```text
Note over <participants>: ✅ Oui — <confirmed result>
```

- Place it immediately after the negative path
- Name the confirmed result rather than writing only `Oui`
- Span only the participants needed to understand that result

## Review questions

Represent an unresolved review question as a normal activity owned by the participant responsible or expected to decide:

```text
DecisionMaker->>DecisionMaker: tk : Which authority approves the return to normal operation?
```

Do not use `Note over` for a `tk :`. Keep these questions limited to decisions that materially clarify authority, responsibility, criteria, evidence, closure, or transition.

## Styling

Use Catppuccin Frappé colors only when they encode a stable distinction:

- Phase notes: Rosewater `#f2d5cf`, Peach border `#ef9f76`, dark text `#303446`
- Positive-response notes: Green `#a6d189`, Teal border `#81c8be`, dark text `#303446`
- Participants, systems, and lifelines: neutral by default

Example configuration:

```yaml
config:
  theme: neutral
  themeVariables:
    noteBkgColor: "#f2d5cf"
    noteBorderColor: "#ef9f76"
    noteTextColor: "#303446"
  themeCSS: >-
    g:is([data-id="<positive-note-id>"]) rect.note {
      fill: #a6d189 !important;
      stroke: #81c8be !important;
    }
```

Mermaid does not provide a native class per note in sequence diagrams. If generated `data-id` selectors are used, centralize them in one selector and re-check them after every structural change. Prefer no color over color with an ambiguous meaning.

## Spacing and density

- Keep vertical groups reasonably close and consistent
- Shorten messages or note spans when a label creates a large empty corridor
- Do not add fake participants to adjust spacing
- Treat layout tuning separately from functional content

Automatic Mermaid layout limits precision. Validate the rendered image instead of assuming the source will produce balanced spacing.

## Required visual validation

After a substantive change:

1. Export the diagram with Mermaid CLI
2. Produce at least an SVG or PNG
3. Inspect the complete image
4. Check lifelines, frames, phase notes, decisions, colors, returns to the main path, and whitespace
5. Correct the source and repeat until satisfactory
6. Run the repository’s whitespace or diff validation

A syntactically valid diagram can still be ambiguous or visually misleading.
