# Output template

Read this file at Step 10. Fill every heading; write `none` rather than delete one.

```markdown
## Architecture

### Overview
- Deployment: modular monolith on <infra>
- Language and framework: <language>, <framework>
- Rationale: <one paragraph tied to team size and the business case>

### Modules
| Module | Type | Responsibility | Owns data | Level | Public API and events |
|---|---|---|---|---|---|
| billing | core | Plans, subscriptions, invoices | subscriptions, invoices | 3 | `subscribe()`, `cancel()`; emits `SubscriptionActivated` |
| settings | generic | User preferences | preferences | 0 | `getSettings()`, `updateSettings()` |

### Building blocks
<filled table from references/building-blocks.md>

### Ports
- Created: `PaymentGateway` → `StripeGateway`: the vendor could change, and tests run without network
- Skipped: auth session: coupled to the framework, no swap planned

### Communication
- Sync: module public APIs only
- Events: `SubscriptionActivated` from `billing` → `notifications`
- Async jobs: welcome email, run by <job runner>

### Folder tree
<tree from Step 8>

### Guardrails
- Boundary linter: <tool>, rules: <rules>
- Decisions recorded: <decision IDs or ADR files>

### Evolution triggers
- settings: raise to level 1 when <trigger>
- Extract a service when <trigger>

### Open questions and risks
1. <question> → <owner or spike>
```
