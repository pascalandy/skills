# Building blocks

Read this file at Step 7. Fill one row per block for the chosen infra; drop a row only with a reason.

| Block | Service | Module or layer | Port? |
|---|---|---|---|
| Front end | | inbound adapter | no |
| API and server logic | | inbound adapter calling use cases | no |
| Auth | | `identity`, infra | usually no |
| Payments | | `billing` | yes |
| Email | | `notifications` | yes |
| Database and ORM | | each module owns its tables | a repository per core module |
| Cache | | infra | usually no |
| File storage | | infra | yes |
| Background jobs and queue | | infra | thin wrapper |
| Observability: errors, analytics, logs | | cross-cutting | no |

## Common services per infra

Check that each service still exists and still fits before you recommend it.

| Block | Vercel | Cloudflare | AWS |
|---|---|---|---|
| Front end | Next.js | Workers static assets | S3 and CloudFront |
| API and server logic | Vercel Functions | Workers | Lambda, or ECS on Fargate |
| Database | Postgres through Neon or Supabase | D1 | RDS or DynamoDB |
| File storage | Vercel Blob | R2 | S3 |
| Background jobs and queue | Cron Jobs, Inngest, Trigger.dev | Queues, Cron Triggers | SQS, EventBridge |

Services that fit any infra: Stripe for payments, Resend for email, Better Auth or Clerk for auth, Upstash for cache, Sentry for errors, PostHog for analytics.
