# Output template

Keep every heading. If a heading or a line has no content, write `none` there. The two module rows are examples of the format, so replace them.

```markdown
## Architecture

### Overview
- Deployment: <deployment choice> on <platform>
- Language and framework: <language>, <framework>
- Rationale: <one paragraph tied to team size and the business case>

### Modules
| Module | Type | Responsibility | Owns data | Level and reason | Public API | Events |
|---|---|---|---|---|---|---|
| billing | core | Plans, subscriptions, invoices | subscriptions, invoices | 3: proration and refund rules | `subscribe()`, `cancel()` | none |
| settings | supporting | User preferences | preferences | 0: reads and writes only | `getSettings()`, `updateSettings()` | none |

### Building blocks
<filled rows from references/building-blocks.md>

### Ports
- Port: <port>, implemented by <adapter>. Reason: <Step 5 condition>
- Direct call: <service>

### Communication
- Calls: module public APIs only
- Events: <event>, emitted by <module>, consumed by <module>
- Queued jobs: <job>, run by <queue>

### Folder tree
<tree from Step 8>

### Guardrails
- Boundary mechanism: <tool and rules>
- Decisions recorded: <decision IDs, ADR file, or "this section">

### Evolution triggers
- When <trigger>, raise <module> to level <n>
- When <Step 5 condition>, add a port for <service>
- When <trigger>, extract <module> into a service

### Open questions and risks
1. <question>. Owner or spike: <name>
```
