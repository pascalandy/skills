---
name: "day-one-architecture"
description: "Use when writing the architecture section of a build plan for a new end-user app (web, SaaS, mobile back end), deciding how to structure or split a new codebase into modules and layers, or choosing between monolith, modular monolith, Clean Architecture, hexagonal, or vertical slices for a new project."
kind: "dev"
---

# Day-one architecture

Turn a business case into an architecture section that starts the codebase on the right foot and stays as light as the rules allow. Scope: application-layer software for end users, such as SaaS, e-commerce, and consumer or B2B web apps. Systems software, such as an OS, drivers, or performance-critical engines, is out of scope.

Write the section in the language of the plan. Keep pattern names and code identifiers in English.

## Where the section goes

- **Plan written with `rolling-wave-planning`**: write the section to `plan/02-architecture.md`, link it from `01-project.md`, and record each decision from Step 8 as a `decisions.md` entry with the trigger `technical choice`
- **Any other plan**: add the section to the plan document and record the decisions as ADRs in `docs/adr/`

## Workflow

Copy this checklist and track your progress:

```
Architecture progress:
- [ ] Step 1: Inputs gathered
- [ ] Step 2: Three axes decided
- [ ] Step 3: Modules found
- [ ] Step 4: Layer level set per module
- [ ] Step 5: Ports chosen
- [ ] Step 6: Communication and reads defined
- [ ] Step 7: Building blocks mapped to the infra
- [ ] Step 8: Folder tree, guardrails, and decisions written
- [ ] Step 9: Evolution triggers written
- [ ] Step 10: Section checked
```

### Step 1: Inputs gathered

Collect from the business case and the conversation; ask only for a missing input that blocks a later step:

1. Problem, core value, and main user journeys
2. Stakeholders: who uses, pays, and operates the app; team size now and in 12 months
3. Infra, such as Vercel, Cloudflare, AWS, or Supabase
4. Language and framework, such as TypeScript and Next.js
5. Integrations: payments, email, auth, file storage, third-party APIs
6. Constraints: compliance, data residency, offline use, real time, budget

Done when each input is known or listed under open questions.

### Step 2: Three axes decided

Each axis is an independent decision. Monolith versus microservices says how many deployables exist; Clean Architecture says how the code inside one deployable is arranged.

| Axis | Question | Default for a new end-user app |
|---|---|---|
| Deployment | How many deployables? | One: a modular monolith |
| Code organization | Where to cut, and how to arrange the inside? | Modules by business domain; layer level per module |
| Communication | How do the parts talk? | Calls through module public APIs, plus a queue for slow or failable work |

Depart from a default only for a reason from Step 1, such as several independent teams or an offline requirement. Done when each axis has a choice and a one-line reason.

### Step 3: Modules found

Use DDD bounded contexts to decide where to cut:

1. List the nouns and verbs of the business case and group those that change together
2. Split where a word changes meaning: "customer" in billing and "customer" in support belong to different modules
3. Aim for 3 to 7 modules, such as `identity`, `billing`, `notifications`, plus 1 to 4 modules that hold the product's value
4. Label each module **core** (the competitive edge), **supporting** (specific but not differentiating), or **generic** (solved by a SaaS: auth, email, payments)

Done when each module has a one-sentence responsibility, the data it owns, its public API, and the events it emits.

### Step 4: Layer level set per module

Give each module the lowest level that fits its rules:

| Level | Shape | Fits |
|---|---|---|
| 0. Thin | Handler calls the database | CRUD, settings, admin screens |
| 1. Vertical slice | One folder per use case, end to end | Simple features, few rules |
| 2. Functional core | Pure business functions, effects at the edges, ports only for external services | Moderate rules, external integrations |
| 3. Full Clean | `domain/`, `application/` with use cases and ports, `infra/` with adapters | Rich, long-lived rules: money, permissions, scheduling |

Core modules usually take level 2 or 3; generic modules take level 0 or 1. At level 3, apply the dependency rule: `domain/` and `application/` import no framework and no vendor SDK. Done when each module has a level and a reason drawn from its rules.

### Step 5: Ports chosen

Create a port, an interface in `application/` with an adapter in `infra/`, when at least one holds:

- The vendor could realistically be swapped: payments, email, file storage, LLM provider
- The use case needs tests without network
- The external API is awkward enough to isolate

Keep framework-coupled concerns, such as the auth session, the framework cache, and routing, outside ports until a concrete need appears. Done when each external service is listed as a port with its adapter, or as skipped with a reason.

### Step 6: Communication and reads defined

- Modules call each other only through the module's public entry point, such as `modules/billing/index.ts`, or through domain events
- Each table belongs to one module; another module reaches that data through the owner's public API
- Slow or failable work goes through a queue or job runner: emails, outbound webhooks, image processing, third-party sync
- Inbound webhooks are inbound adapters: verify the signature, stay idempotent, call a use case
- Writes go through use cases; display reads may query a read model directly (CQRS light). In Next.js, server components read and server actions write

Done when each event names its emitter and consumers, and each async job names its runner.

### Step 7: Building blocks mapped to the infra

Fill the building-blocks table in [references/building-blocks.md](references/building-blocks.md) for the chosen infra. Read that file at this step. Done when each block has a service, a module or layer, and a port decision, or is marked out of scope with a reason.

### Step 8: Folder tree, guardrails, and decisions written

1. Adapt this tree to the language; the example is TypeScript and Next.js:

   ```
   src/
     app/                    # inbound adapters: validate, call a use case, render
       (marketing)/
       (app)/
       api/webhooks/<vendor>/route.ts
     modules/
       <module>/
         domain/             # level 3
         application/        # use cases and ports.ts, levels 2 and 3
         infra/              # adapters, levels 2 and 3
         index.ts            # public API of the module
     shared/
       infra/                # database client, cache, logger, queue client
       kernel/               # small shared types: ids, Money, Result
     composition.ts          # wires each port to its adapter
   ```

2. Name the boundary linter that enforces the module and layer rules in CI: `eslint-plugin-boundaries` or `dependency-cruiser` for TypeScript, `import-linter` for Python, ArchUnit for Java and Kotlin, `internal/` packages for Go
3. Record the first decisions: deployment choice, module list, level per module, ports created and skipped

Done when the tree lists every module from Step 3, the linter rules forbid the imports Steps 4 and 6 forbid, and each decision is recorded where [Where the section goes](#where-the-section-goes) says.

### Step 9: Evolution triggers written

Write when to revisit, so the first version stays small:

- Raise a module one level when its rules multiply, bugs cluster in it, or its tests get hard to write
- Extract a module into its own service only for a concrete reason: an independent team (Conway's law), different scaling or runtime needs, a different deploy cadence, or security isolation
- Consider another family when the product needs it: local-first or a sync engine for instant or collaborative UX; backend-as-a-service, such as Supabase, Firebase, or Convex, to trade layers for speed with vendor coupling

Done when each core module has a level-up trigger and the plan names at least one extraction trigger.

### Step 10: Section checked

Write the section from the template in [references/output-template.md](references/output-template.md), then check it against this list and fix each failure:

- Each core module owns its data
- No module sits above the level its rules justify
- Each external service is behind a port or listed as skipped with a reason
- Slow or failable work is async
- Business rules live in modules; `app/`, route handlers, and UI components hold none
- Folders follow business domains, and `shared/` holds only infra clients and kernel types

Done when every item passes. For named laws behind these choices, such as Gall's law or YAGNI, load `coding-eng-laws`.
