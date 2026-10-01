# First Principles Thinking

Decisions Mid-Level

Breaking a complex problem into its most basic blocks and then building up from there.

## Takeaways

- Do not accept the problem as it is. Break the problem down into its inherent parts and then question your assumptions: Are they really true, or are they just accepted standards? Once you grasp the underlying requirements, you may develop new solutions.
- Just because “everyone uses Framework Y for this” isn’t a reason you should do so. First principles thinking pushes you to ask why people do certain things the way they do.
- Rather than saying, “This feature will take 3 months because that’s how long similar features took,” break the feature down. Estimate from the basics, which can sometimes show that the “similar” feature had additional issues that you may not have anymore.

## Overview

First-principles thinking solves problems by questioning existing solutions rather than blindly copying them. Instead of “We’ll do X because that other project did X,” ask: “What are we really trying to accomplish? What are constraints versus assumptions?” This approach is good for incremental improvements but essential for fundamental changes.

In software design, first principles challenge how current systems work: “If we started from scratch today, how would we build this?” This thinking led to microservices (questioning the monolith) and serverless computing (questioning server management). The drawback is that it is mentally intensive and not always necessary. Many problems are well-solved by known patterns.

## Examples

Before SpaceX, launching rockets was costly because industry practice used expensive materials and discarded rockets after one use. Elon Musk applied first-principles thinking: What is a rocket made of? Mainly aluminum, titanium, copper, and carbon fiber. Raw material costs were a fraction of finished rocket prices. From that insight, SpaceX decided to build rockets from scratch and make them reusable.

In software, consider a company paying licensing fees for a proprietary analytics platform. An engineer challenged this by examining what the platform actually does: ingest data, run statistical computations, generate reports. These could be implemented using open-source software and custom programming. A proof-of-concept in Python showed 90% of the solution at a fraction of the cost.

## Origins

The term “first principles” has roots in classical philosophy. Aristotle referred to first principles as foundational propositions that cannot be deduced from anything else, the bedrock of knowledge. René Descartes emphasized starting from fundamental truths (“I think, therefore I am”).

In modern times, first-principles thinking gained fame through Elon Musk, who credits it for SpaceX and Tesla innovations. Instead of thinking “rockets are expensive,” he broke down raw material costs and realized building in-house was viable.

## Further Reading

- [First Principles: The Building Blocks of True Knowledge Farnam Street's comprehensive guide to first principles thinking](https://fs.blog/first-principles/)
- [Posterior Analytics - Aristotle Stanford Encyclopedia of Philosophy on Aristotle's foundational logic](https://plato.stanford.edu/entries/aristotle-logic/)
- [How to Solve It - George Pólya Classic book on mathematical problem-solving and heuristics](https://amzn.to/4b9q3Qo)

## Related Laws

- [Occam's Razor](https://lawsofsoftwareengineering.com/laws/occams-razor/) — The simplest explanation is often the most accurate one.
- [KISS (Keep It Simple, Stupid)](https://lawsofsoftwareengineering.com/laws/kiss-principle/) — Designs and systems should be as simple as possible.
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked.
