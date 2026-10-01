# Architecture Diagrams Reference

Architecture diagrams visualize cloud services, CI/CD deployments, and infrastructure relationships. Introduced in Mermaid v11.1.0.

## Basic Syntax

```mermaid
architecture-beta
    group public_api(cloud)[Public API]
    service api1(server)[API Server] in public_api
    service db(database)[Database]

    api1:R --> L:db
```

## Building Blocks

### Groups

Group related services together:

```
group {groupId}({icon})[{title}] (in {parentId})?
```

```mermaid
architecture-beta
    group public_api(cloud)[Public API]
    group private_api(cloud)[Private API] in public_api
```

### Services

Declare services (nodes):

```
service {serviceId}({icon})[{title}] (in {parentId})?
```

```mermaid
architecture-beta
    group backend(cloud)[Backend]
    service api(server)[API Server]
    service db(database)[Database]
    service cache(database)[Cache] in backend
```

### Edges

Connect services with edges:

```
{serviceId}{{group}}?:{T|B|L|R} {<}?--{>}? {T|B|L|R}:{serviceId}{{group}}?
```

**Directions:** `T` (top), `B` (bottom), `L` (left), `R` (right)

**Arrows:** `<` for incoming, `>` for outgoing

```mermaid
architecture-beta
    service client(internet)[Client]
    service api(server)[API]
    service db(database)[Database]

    client:B --> T:api
    api:R --> L:db
```

### Junctions

Create 4-way splits:

```
junction {junctionId} (in {parentId})?
```

```mermaid
architecture-beta
    service input(server)[Input]
    service output1(server)[Output 1]
    service output2(server)[Output 2]

    junction j1

    input:R --> L:j1
    j1:T --> B:output1
    j1:B --> T:output2
```

## Icons

**Default icons:** `cloud`, `database`, `disk`, `internet`, `server`

**Custom icons:** Register a pack in the renderer before using its prefix. Installing or writing an icon name alone does not register it. Missing packs can render question marks without a CLI error. These text examples require the `logos` pack; use built-in icons for portable diagrams

```text
architecture-beta
    service web(logos:aws-ec2)[Web Server]
    service storage(logos:aws-s3)[Storage]
```

### Using @iconify-json Icon Packs

Use icon packs with Mermaid CLI for technology logos:

```bash
pnpm add -D @iconify-json/logos @mermaid-js/mermaid-cli
pnpm exec mmdc --iconPacks @iconify-json/logos -i ./diagram.mmd -o ./output.svg
```

Use icons with the `logos:` prefix:

```text
architecture-beta
    service web(logos:docker)[Docker Container]
    service k8s(logos:kubernetes)[Kubernetes Cluster]
    service aws(logos:aws-ec2)[AWS Services]
    service github(logos:github)[GitHub Actions]

    web:R --> L:k8s
    k8s:R --> L:aws
    web:R --> L:github
```

**Popular icon packs:**

| Icon Pack                    | Description                                   | Install                            |
| ---------------------------- | --------------------------------------------- | ---------------------------------- |
| `@iconify-json/logos`        | Technology brands (Docker, AWS, GitHub, etc.) | `pnpm add -D @iconify-json/logos`        |
| `@iconify-json/bi`           | Bootstrap icons                               | `pnpm add -D @iconify-json/bi`           |
| `@iconify-json/mdi`          | Material Design icons                         | `pnpm add -D @iconify-json/mdi`          |
| `@iconify-json/simple-icons` | Simple icons                                  | `pnpm add -D @iconify-json/simple-icons` |

Usage: `pack:icon-name` (e.g., `logos:docker`, `mdi:database`)

## Complex Example

```mermaid
architecture-beta
    group internet(cloud)[Internet]
    group private_vpc(cloud)[Private VPC]

    service lb(internet)[Load Balancer] in internet
    service api1(server)[API Server 1] in private_vpc
    service api2(server)[API Server 2] in private_vpc
    service db(database)[Primary Database] in private_vpc
    service replica(database)[Read Replica] in private_vpc

    lb:R --> L:api1
    lb:R --> L:api2
    api1:R --> L:db
    api2:R --> L:db
    db:R --> L:replica
```

## Edge Patterns

| Pattern              | Description               |
| -------------------- | ------------------------- |
| `A:R -- L:B`         | Horizontal edge           |
| `A:T -- B:B`         | Vertical edge |
| `A:T -- L:B`         | Edge joining different axes |
| `A:R --> L:B`        | Edge with arrow           |
| `A:R <--> L:B`       | Bidirectional edge        |
| `A{group}:R --> L:B` | Edge from group boundary  |

## Group Edges

Connect groups using the `{group}` modifier:

```mermaid
architecture-beta
    group frontend(cloud)[Frontend]
    group backend(cloud)[Backend]

    service client(internet)[Client] in frontend
    service api(server)[API] in backend

    client{group}:B --> T:api{group}
```

## Best Practices

1. Group services by environment (public/private) or layer (frontend/backend)
2. Use consistent icons for service types
3. Use a flowchart or C4 view when protocol labels on edges are essential; architecture edge syntax has no text label field
4. Use junctions for fan-out patterns
5. Keep diagrams focused; split complex architectures into multiple views

## Reference

- [Official Documentation](https://mermaid.js.org/syntax/architecture.html)
- [Iconify Icons](https://iconify.design)
