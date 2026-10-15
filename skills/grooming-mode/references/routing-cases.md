# Routing cases

Replay with `just replay-routing grooming-mode`. Run
`just replay-routing --help` for the table format.

| Request | Reads | Opens with |
|---|---|---|
| `grooming-mode` | `playbooks/epic.md` | |
| `grooming-mode ; milestone` | `playbooks/milestone.md` | |
| `grooming-mode ; refine` | `playbooks/refine.md` | |
| `grooming mode ; refine` | `playbooks/refine.md` | |
| `grooming mode refine` | `playbooks/refine.md` | |
| `grooming-mode ; sprint` | no route | |

Grade the last row's answer by hand: it shows epic, milestone and refine,
and runs nothing.
