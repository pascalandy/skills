# Building blocks

Fill one row for each block that the product needs. Omit the other rows. Take each port decision from Step 5.

| Block | Service | Module or layer | Port |
|---|---|---|---|
| Front end | | routes and pages | no |
| API and server logic | | routes that call modules | no |
| Auth | | the framework, or the module that owns users | usually no |
| Payments | | the module that charges | Step 5 |
| Email | | the module that sends | Step 5 |
| Database | | each table has one owner module | repository at level 3 only |
| Cache | | `shared/` | usually no |
| File storage | | the module that owns the files | Step 5 |
| Queue | | `shared/` | no |
| Observability: errors, analytics, logs | | `shared/` | no |

## Common services per platform

Before you recommend a service, check that it still exists and fits the project.

| Block | Vercel | Cloudflare | AWS |
|---|---|---|---|
| Front end | Vercel hosting for Next.js | Workers static assets | S3 and CloudFront |
| API and server logic | Vercel Functions | Workers | Lambda, or ECS on Fargate |
| Database | Postgres through Neon or Supabase | D1 | RDS or DynamoDB |
| File storage | Vercel Blob | R2 | S3 |
| Queue | Vercel Queues, Inngest, Trigger.dev | Queues | SQS |

Services that fit any platform: Stripe for payments, Resend for email, Better Auth or Clerk for auth, Upstash for cache, Sentry for errors, PostHog for analytics.
