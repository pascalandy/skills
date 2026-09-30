---
name: "corey-mode"
description: "Use only when a request contains the word marketing, or invokes corey-mode, to run Corey Haines' marketing playbooks."
kind: "general"
---

# Corey mode

Corey-mode does marketing work with Corey Haines' playbooks, from strategy to the pages, emails, ads, and site changes they produce. Poteto-mode runs engineering work, and matt-mode prepares it.

## Pick the route

A request can name its route, as in `marketing ; cro`. Compare names with case, spaces, hyphens, and underscores ignored.

- **A name matches.** Read that route's playbook and follow it to its result.
- **No name, one clear owner.** Run the route whose "Use when" owns the request, and say which route you chose in one line.
- **Two routes fit.** Name the candidates with their "Use when" and ask which one. Run nothing.
- **No route fits.** Say that corey-mode has no playbook for the request, then handle it without the mode.

A request with several deliverables runs one route per deliverable, in the order the work needs. Load another route only when the request or the running playbook calls for it.

## Read a playbook

Each playbook is one of Corey's skills, copied from a pinned upstream revision. Follow it in full.

- A playbook names its neighbors as skills, as in "see signup", "the `ads` skill", or `/marketing-plan`. Each name is the route of that name here. A name with no route, such as `positioning`, has no playbook.
- `SKILL.md` inside a playbook means that playbook's own file.
- Links resolve from the file that holds them. Links into upstream `tools/` and `evals/` open on GitHub at the pinned revision. A command such as `node tools/clis/<tool>.js` needs a checkout of that repository.

## Routes

### Foundation and strategy

| Route | Use when |
|---|---|
| [`product-marketing`](playbooks/product-marketing/product-marketing.md) | Create or update the product context every other route reads |
| [`marketing-plan`](playbooks/marketing-plan/marketing-plan.md) | Write a full marketing plan for a client or a product |
| [`marketing-ideas`](playbooks/marketing-ideas/marketing-ideas.md) | Find ideas when stuck on how to grow, before choosing a channel |
| [`marketing-council`](playbooks/marketing-council/marketing-council.md) | Weigh one marketing question through several famous marketers' views |
| [`marketing-loops`](playbooks/marketing-loops/marketing-loops.md) | Set up a marketing workflow an agent repeats on a schedule |
| [`marketing-psychology`](playbooks/marketing-psychology/marketing-psychology.md) | Apply psychology, biases, or behavioral science to marketing |
| [`customer-research`](playbooks/customer-research/customer-research.md) | Run or synthesize customer interviews, surveys, reviews, or personas |

### SEO and site

| Route | Use when |
|---|---|
| [`seo-audit`](playbooks/seo-audit/seo-audit.md) | Diagnose rankings, traffic drops, or technical and on-page SEO |
| [`ai-seo`](playbooks/ai-seo/ai-seo.md) | Get cited in AI answers and AI search |
| [`schema`](playbooks/schema/schema.md) | Add or fix schema markup and structured data |
| [`programmatic-seo`](playbooks/programmatic-seo/programmatic-seo.md) | Build many templated pages from data |
| [`site-architecture`](playbooks/site-architecture/site-architecture.md) | Plan page hierarchy, navigation, URLs, and internal links |
| [`content-strategy`](playbooks/content-strategy/content-strategy.md) | Decide which topics and content to produce |
| [`aso`](playbooks/aso/aso.md) | Audit or optimize an App Store or Google Play listing |

### Conversion

| Route | Use when |
|---|---|
| [`cro`](playbooks/cro/cro.md) | Raise conversions on a marketing page or lead form |
| [`signup`](playbooks/signup/signup.md) | Improve signup, registration, or trial-start flows |
| [`onboarding`](playbooks/onboarding/onboarding.md) | Improve activation after signup |
| [`popups`](playbooks/popups/popups.md) | Create or improve popups, modals, slide-ins, and banners |
| [`paywalls`](playbooks/paywalls/paywalls.md) | Improve in-app upgrade screens and feature gates |

### Copy and content

| Route | Use when |
|---|---|
| [`copywriting`](playbooks/copywriting/copywriting.md) | Write or rewrite the copy of a web page |
| [`copy-editing`](playbooks/copy-editing/copy-editing.md) | Edit, tighten, or refresh copy that already exists |
| [`emails`](playbooks/emails/emails.md) | Build automated email sequences and lifecycle flows |
| [`cold-email`](playbooks/cold-email/cold-email.md) | Write cold outreach emails and follow-ups to prospects |
| [`sms`](playbooks/sms/sms.md) | Plan SMS or MMS campaigns and flows |
| [`social`](playbooks/social/social.md) | Create or schedule social posts and short-form video scripts, or listen on social |
| [`image`](playbooks/image/image.md) | Create or optimize marketing images outside paid ads |
| [`video`](playbooks/video/video.md) | Produce marketing video with AI tools or code |

### Paid and measurement

| Route | Use when |
|---|---|
| [`ads`](playbooks/ads/ads.md) | Plan campaign strategy, targeting, bidding, and budgets on an ad platform |
| [`ad-creative`](playbooks/ad-creative/ad-creative.md) | Produce or iterate ad copy and ad formats at scale |
| [`analytics`](playbooks/analytics/analytics.md) | Set up or audit tracking, events, conversions, and UTMs |
| [`attribution`](playbooks/attribution/attribution.md) | Find which marketing drives revenue, or reconcile tools that disagree |
| [`ab-testing`](playbooks/ab-testing/ab-testing.md) | Design an A/B test or an experimentation program |

### Growth and retention

| Route | Use when |
|---|---|
| [`referrals`](playbooks/referrals/referrals.md) | Build a referral, affiliate, or word-of-mouth program |
| [`lead-magnets`](playbooks/lead-magnets/lead-magnets.md) | Plan downloadable content that captures emails |
| [`free-tools`](playbooks/free-tools/free-tools.md) | Plan or build a free tool, such as a calculator, for leads or links |
| [`churn-prevention`](playbooks/churn-prevention/churn-prevention.md) | Reduce churn with cancel flows, save offers, or payment recovery |
| [`community-marketing`](playbooks/community-marketing/community-marketing.md) | Build or grow a community around the product |
| [`co-marketing`](playbooks/co-marketing/co-marketing.md) | Find partner companies and plan joint campaigns |
| [`influencer-marketing`](playbooks/influencer-marketing/influencer-marketing.md) | Run influencer, creator, or ambassador partnerships |
| [`public-relations`](playbooks/public-relations/public-relations.md) | Earn press coverage, pitch journalists, or prepare podcast appearances |
| [`events`](playbooks/events/events.md) | Plan, sponsor, speak at, or follow up on events and webinars |

### Sales and go-to-market

| Route | Use when |
|---|---|
| [`launch`](playbooks/launch/launch.md) | Plan a product launch or a feature announcement |
| [`pricing`](playbooks/pricing/pricing.md) | Set prices, tiers, and packaging, or audit a pricing page |
| [`offers`](playbooks/offers/offers.md) | Design what is sold, with its value stack, bonuses, and guarantee |
| [`competitors`](playbooks/competitors/competitors.md) | Write comparison or alternative pages against competitors |
| [`competitor-profiling`](playbooks/competitor-profiling/competitor-profiling.md) | Research and profile competitors from their URLs |
| [`directory-submissions`](playbooks/directory-submissions/directory-submissions.md) | Submit the product to startup, SaaS, and AI directories |
| [`prospecting`](playbooks/prospecting/prospecting.md) | Find and qualify a list of prospects |
| [`sales-enablement`](playbooks/sales-enablement/sales-enablement.md) | Create sales decks, one-pagers, objection handling, or demo scripts |
| [`revops`](playbooks/revops/revops.md) | Design lead scoring, routing, and the marketing-to-sales handoff |

## Callers

A skill or mode outside corey-mode reaches one route by reading its playbook in the active `corey-mode` skill directory, such as `playbooks/copywriting/copywriting.md`. It keeps its own task and loads no other route.

## Maintenance

Read [lineage and updating](references/lineage.md) to refresh the playbooks from upstream. Change `playbooks/` only through its importer.
