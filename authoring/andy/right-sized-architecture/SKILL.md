---
name: "right-sized-architecture"
description: "Use when writing the architecture section of a build plan for an end-user app (web, SaaS, mobile back end), assessing whether the modules and layers of an existing codebase are the right size, or choosing between monolith, modular monolith, Clean Architecture, hexagonal, or vertical slices."
kind: "dev"
---

# Right-sized architecture

Decide the smallest structure that fits an application, for a new project or an existing project. Include a module, layer, port, event, queue, or service only when a current requirement justifies it.

Scope: application software for end users, such as SaaS, e-commerce, and consumer or B2B web apps. Systems software, such as an OS, drivers, or performance-critical engines, is out of scope.

This skill decides structure at the scale of the application: modules, levels, and ports. To design types and function signatures before an implementation, use the `architect` skill.

Write the output in the language of the plan or of the request. Keep pattern names and code identifiers in English.

## Pick the branch

- **New project**: follow the [Workflow](#workflow). The output is the architecture section of the plan
- **Existing project**: read [references/existing-project.md](references/existing-project.md) and follow it. The output is a list of findings, without a change plan

## Keep the architecture small

These rules apply to every step:

- Each module, level above 0, port, event, queue, and building block needs a reason from Step 1
- When an item has no reason, leave the item out and write `none`
- A product with one business domain gets one module
- One or two modules at level 0 or 1, with no port, event, or queue, is a correct result

## Terms

- **Module**: a folder that holds one business domain and exposes one public API
- **Level**: one of the four ways to organize a module, from 0 to 3. Step 4 defines each level
- **Use case**: a function that runs one business action, such as `subscribe()`
- **Port**: an interface that a module declares for an external service
- **Adapter**: the code that implements a port for one vendor
- **ADR**: architecture decision record, a file that records one or more decisions

## Where the section goes

- **Plan written with `rolling-wave-planning`**: write the section to `plan/02-architecture.md`. Link that file from `01-project.md`. Record each Step 8 decision in `decisions.md` with the trigger `technical choice`, and update `Next IDs`
- **Project that already keeps ADRs**: add the section to the plan document. Record the Step 8 decisions in one ADR
- **Any other plan**: add the section to the plan document. The section is the record of the decisions

## Workflow

Copy this checklist and track your progress:

```
Architecture progress:
- [ ] Step 1: Inputs gathered
- [ ] Step 2: Three axes decided
- [ ] Step 3: Modules found
- [ ] Step 4: Level set per module
- [ ] Step 5: Ports chosen
- [ ] Step 6: Communication and reads defined
- [ ] Step 7: Building blocks mapped to the platform
- [ ] Step 8: Folder tree, guardrails, and decisions written
- [ ] Step 9: Evolution triggers written
- [ ] Step 10: Section checked
```

### Step 1: Inputs gathered

Collect these inputs from the business case and the conversation. Ask the user only for a missing input that blocks a later step.

1. Problem, core value, main user journeys, and business rules
2. Stakeholders: the people who use, pay for, and operate the app, and the team size now and in 12 months
3. Platform, such as Vercel, Cloudflare, AWS, or Supabase
4. Language and framework, such as TypeScript and Next.js
5. Integrations: payments, email, auth, file storage, third-party APIs
6. Constraints: compliance, data residency, offline use, real time, budget

Done when each input is known or listed as an open question.

### Step 2: Three axes decided

Each axis is an independent decision.

| Axis | Question | Default for an end-user app |
|---|---|---|
| Deployment | How many deployables exist? | One deployable |
| Code organization | Where are the module boundaries, and which level does each module have? | Modules by business domain, each at the lowest level that fits |
| Communication | How do modules communicate? | Direct calls to the public API of a module |

Depart from a default only for a reason from Step 1. These reasons are examples:

- Several independent teams: more than one deployable
- Writes that must work offline and synchronize later: local-first data with a sync engine
- Delivery speed matters more than vendor independence: a backend-as-a-service, such as Supabase, Firebase, or Convex, which replaces most layers

Done when each axis has a choice and a one-line reason.

### Step 3: Modules found

Find the module boundaries with bounded contexts from domain-driven design (DDD). A bounded context is an area where each business word keeps one meaning.

1. List the nouns and verbs of the business case, and group the words that change together
2. Put a boundary where a word changes meaning. For example, "customer" in billing and "customer" in support belong to different modules
3. Keep one module when the user journeys share the same business rules and data. Use at most 7 modules
4. Label each module **core** (the competitive edge), **supporting** (specific to the product but not differentiating), or **generic** (a vendor solves the problem, such as auth, email, or payments). A generic problem gets a module only when the product adds business rules to it

Done when each module has a one-sentence responsibility, the data it owns, its public API, and the events it emits or `none`.

### Step 4: Level set per module

Give each module the lowest level that fits its business rules. The label from Step 3 does not set the level. A core module with few business rules stays at level 0 or 1.

| Level | Shape | Fits |
|---|---|---|
| 0. Thin | A handler in the module reads and writes the database | CRUD, settings, admin screens |
| 1. Vertical slice | One folder per business action, from input to database | Simple features with few business rules |
| 2. Functional core | Pure business functions, with database and network calls at the edges | Moderate business rules |
| 3. Full Clean Architecture | `domain/`, `application/` with use cases and ports, `infra/` with adapters | Many long-lived business rules, such as money, permissions, or scheduling |

At level 3, dependencies point inward:

- `infra/` can import `application/` and `domain/`
- `application/` can import `domain/`
- `domain/` and `application/` import no framework and no vendor SDK

Done when each module has a level and a reason drawn from its business rules.

### Step 5: Ports chosen

The default is no port: the module calls the vendor SDK directly. If an external service meets one of these conditions, define a port and an adapter in the module that uses the service:

- The product must support two vendors for this service, or the team plans to change the vendor
- A business rule of a level 2 or 3 module calls the service and needs a test without network access
- The vendor API is hard to use, and several use cases call it

Keep these framework-coupled concerns outside ports: the auth session, the framework cache, and routing.

Done when each external service is listed as a port with its adapter, or as a direct call.

### Step 6: Communication and reads defined

- Call another module only through its public API, such as `modules/billing/index.ts`
- Give each table one owner module. Other modules read that data through the public API of the owner
- Inside the owner module, let a display read query the database directly. In Next.js, a server component can call that read
- At levels 2 and 3, send each write through a use case. At levels 0 and 1, the handler writes directly
- Emit an event only when a second module must react to a change
- Keep work synchronous when the response depends on its result
- Use a queue only for work that can finish later and needs background execution or retries. Examples are email, outbound webhooks, and image processing
- Make each inbound webhook handler verify the signature. When a delivery repeats completed work, the handler acknowledges the delivery and does not repeat the action

Done when each event names its emitter and consumers and each queued job names its queue. Write `none` when the plan has no event or no queued job.

### Step 7: Building blocks mapped to the platform

Read [references/building-blocks.md](references/building-blocks.md). Then fill one row of its table for each block that the product needs.

Done when each needed block has a service, a module or layer, and the port decision from Step 5.

### Step 8: Folder tree, guardrails, and decisions written

1. Draw the folder tree from the modules, levels, and integrations that you selected. Omit each folder that has no code in the first version. This example uses TypeScript and Next.js, with one level 0 module and one level 3 module:

   ```
   src/
     app/                    # routes and pages: validate input, call a module, render
     modules/
       settings/             # level 0
         index.ts            # public API: handlers that call the database
       billing/              # level 3
         domain/
         application/        # use cases and ports.ts
         infra/              # adapters
         index.ts            # public API of the module
     shared/                 # database client, logger
     composition.ts          # only when a port exists: connects each port to its adapter
   ```

2. If the plan has more than one module, name the mechanism that enforces the module boundaries in CI:
   - TypeScript: `eslint-plugin-boundaries` or `dependency-cruiser`
   - Python: `import-linter`
   - Java and Kotlin: ArchUnit
   - Go: `internal/` packages for module boundaries, and `depguard` for layer imports at level 3
3. Record the decisions: deployment choice, module list, level per module, and ports

Done when all of these conditions hold:

- The tree lists every module from Step 3 and no folder without code in the first version
- When the plan has a boundary mechanism, it forbids the imports that Steps 4 and 6 forbid
- Each decision is recorded where [Where the section goes](#where-the-section-goes) says

### Step 9: Evolution triggers written

A trigger says when to add structure, so the first version can stay small. Write each trigger as a condition on one module of the plan:

- When business rules multiply in a module, bugs cluster in it, or its tests become hard to write, raise the module one level
- When a Step 5 condition becomes true for an external service, add a port
- When an independent team, a different scaling need, a different deploy cadence, or security isolation appears, extract the module into a service

Done when each core module below level 3 has a level-up trigger. If Step 1 identifies a future reason to deploy a module separately, write an extraction trigger for that module.

### Step 10: Section checked

1. Read [references/output-template.md](references/output-template.md) and write the section from that template
2. Check the section against the list below
3. Fix each failure, then check again

- Each module, level above 0, port, event, queue, and building block has a reason from Step 1
- No module has a level higher than its business rules justify
- Each table has one owner module
- Each external service is listed as a port or as a direct call
- Only work that can finish later uses a queue
- Routes, pages, and UI components hold no business rules
- Folders follow business domains, and `shared/` holds only clients and small shared types

Done when every item passes.
