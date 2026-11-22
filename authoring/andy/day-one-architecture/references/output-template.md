# Output template

Keep every heading, and write `none` under a heading that has no content. The two module rows are examples of the format: replace them.

```markdown
## Architecture

### Overview
- Deployment: <deployment choice> on <platform>
- Language and framework: <language>, <framework>
- Rationale: <one paragraph tied to team size and the business case>

### Modules
| Module | Type | Responsibility | Owns data | Level | Public API | Events |
|---|---|---|---|---|---|---|
| billing | core | Plans, subscriptions, invoices | subscriptions, invoices | 3 | `subscribe()`, `cancel()` | none |
| settings | supporting | User preferences | preferences | 0 | `getSettings()`, `updateSettings()` | none |

### Building blocks
<filled rows from references/building-blocks.md>

### Ports
- Port: `PaymentGateway`, implemented by `StripeGateway`. Reason: a billing rule needs a test without network access
- Direct call: auth session

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
- <module>: raise to level <n> when <trigger>
- Extract <module> into a service when <trigger>

### Open questions and risks
1. <question>. Owner or spike: <name>
```
