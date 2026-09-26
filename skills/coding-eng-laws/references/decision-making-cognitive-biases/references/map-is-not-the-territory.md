# The Map Is Not the Territory

Decisions Mid-Level

Our representations of reality are not the same as reality itself.

## Takeaways

- Design docs, UML diagrams, and architecture schematics are abstractions. Don’t confuse the blueprint with the actual running software.
- When implementing a system, expect that unforeseen factors will emerge that weren’t captured in the initial designs. Be prepared to adapt the plan as you discover new “terrain” during development and testing.
- Models and designs are valuable for guiding development, but always be willing to question assumptions when evidence from the real system contradicts them.

## Overview

“The Map Is Not the Territory” is a mental model originating from general semantics. It encapsulates the idea that our perceptions or conceptual models of things are not the things themselves.

In software, we constantly create “maps”: requirements documents map user needs, architecture diagrams map how components should interact, and our mental understanding of a codebase is a personal map of how we think the code works.

These maps are useful and necessary. Without them, we couldn’t plan or reason about complex systems. However, problems arise when we forget the map’s limits.

A typical example is overconfidence in initial design: a team designs a system on paper, but when coding begins, they discover modules cannot communicate due to latency issues not captured in their assumptions.

As statistician George Box said, “All models are wrong, but some are useful.”

![The Map Is Not the Territory illustration](/images/laws/map-is-not-territory.png)

## Examples

Consider designing a microservice system where Service A communicates with Services B and C via Kafka topics. The diagram assumed “the network is reliable” or “latency is negligible,” but in cloud infrastructure reality, those assumptions fall apart. The team updates the design to include retry mechanisms or schema validation.

In performance modeling, an engineer might model a database handling 10,000 queries per second based on specs. In production, due to specific query patterns and data distribution, it only achieves 5,000 qps. The model didn’t account for query plan edge cases.

The Agile methodology itself embodies “map vs territory” thinking: instead of detailed 2-year plans, Agile uses short iterations with continuous feedback from reality to correct its maps.

## Origins

The phrase was popularized in “Science and Sanity” (1933) by Alfred Korzybski, a Polish-American scholar. Korzybski highlighted how our language and knowledge mislead us into believing our constructs actually represent reality.

## Further Reading

- [Science and Sanity Alfred Korzybski's foundational work on general semantics](https://www.holybooks.com/wp-content/uploads/Science-and-Sanity.pdf)
- [Steps to an Ecology of Mind Gregory Bateson's collected essays on anthropology, psychiatry, and epistemology](https://www.press.uchicago.edu/ucp/books/book/chicago/S/bo3620295.html)

## Related Laws

- [Goodhart's Law](https://lawsofsoftwareengineering.com/laws/goodharts-law/) — When a measure becomes a target, it ceases to be a good measure.
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked.
- [The Law of Leaky Abstractions](https://lawsofsoftwareengineering.com/laws/law-of-leaky-abstractions/) — All non-trivial abstractions, to some degree, are leaky.
