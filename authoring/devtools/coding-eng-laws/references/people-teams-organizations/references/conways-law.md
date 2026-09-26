# Conway's Law

Teams Senior

Organizations design systems that mirror their own communication structure.

## Takeaways

- The architecture of software systems often mirrors the organization’s org chart or team structure.
- If your company is organized in silos, you might end up with siloed software modules that don’t communicate well, reflecting those barriers.
- To achieve a desired software architecture (e.g., microservices), you might need to restructure teams accordingly, because teams build software aligned with their communication paths.
- When starting a project, realize that how you split teams or departments will likely lead to software boundaries at the same places.

## Overview

Conway’s Law states that **software systems reflect the communication structure of the organization that builds them**. A company with separate frontend, backend, and database departments will likely produce a three-tier architecture. Small, distributed teams tend to produce modular service architectures, while large, collocated teams tend to build monoliths.

To mitigate this, teams can use the **Inverse Conway Maneuver**: intentionally structuring the organization to match the desired software architecture.

Conway’s Law

## Examples

A company had separate departments for frontend, backend, and database. The software they built had a three-tier architecture, with each tier independently designed by its respective department. Integration between tiers was painful because the teams had misaligned goals.

Amazon famously organized “two-pizza teams”, each owning a specific service. Conway’s Law suggests that’s why Amazon’s architecture is service-oriented, with clear API contracts between services.

## Origins

**Melvin Conway** introduced the idea in his 1967 paper “How Do Committees Invent?” After Harvard Business Review rejected it for lacking formal proof, Datamation published it in 1968.

Fred Brooks later named it “Conway’s Law” in *The Mythical Man-Month*, which established the concept as foundational in software engineering.

## Further Reading

- [How Do Committees Invent? Melvin Conway's original 1968 paper](https://www.melconway.com/Home/Committees_Paper.html)
- [Conway's Law Martin Fowler's explanation of Conway's Law](https://martinfowler.com/bliki/ConwaysLaw.html)
- [Spotify Engineering Culture The original Spotify Model blog post](https://engineering.atspotify.com/2014/3/spotify-engineering-culture-part-1)
- [Team Topologies Modern application of Conway's Law to organizational design](https://amzn.to/4jgRZ6V)

## Related Laws

- [Brooks's Law](https://lawsofsoftwareengineering.com/laws/brooks-law/) — Adding manpower to a late software project makes it later
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked
- [The Law of Leaky Abstractions](https://lawsofsoftwareengineering.com/laws/law-of-leaky-abstractions/) — All non-trivial abstractions, to some degree, are leaky
- [Hyrum's Law](https://lawsofsoftwareengineering.com/laws/hyrums-law/) — With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody.
