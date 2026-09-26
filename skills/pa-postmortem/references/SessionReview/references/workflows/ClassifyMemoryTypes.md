# ClassifyMemoryTypes

Classify each durable item using the session-review memory taxonomy.

## Memory Types

1. `observation` - Something noticed, including preferences and patterns
2. `decision` - A choice made with rationale
3. `learning` - A lesson learned
4. `error` - Something that went wrong
5. `action` - Something that was done
6. `thought` - Internal reasoning worth preserving
7. `project_status` - A current-state snapshot
8. `command_summary` - A summary of a command or tool-driven operation

## Method

1. Review the reconstructed session.
2. Extract only items worth remembering in the future.
3. Assign one primary memory type to each item.
4. If an item fits multiple types, choose the one that best reflects why it matters.

## Output

Use the exact label format:

```text
### N. Short Title

**MEMORY TYPE:** observation
```
