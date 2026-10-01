# Amdahl's Law

Scale Senior

The speedup from parallelization is limited by the fraction of work that cannot be parallelized.

## Takeaways

- Sequential work sets the ceiling, and no amount of parallelism can overcome it.
- Scaling exposes bottlenecks. More resources make limits visible, not disappear.
- Fix before you scale: reduce sequential paths first. Parallelism comes second.
- It applies to people, too. Decision bottlenecks can dominate at the team scale.

## Overview

As you add CPU cores, only the parallelizable fraction of your code speeds up. The sequential fraction remains unchanged and eventually dominates total execution time. If “s” is the sequential fraction, the maximum speedup with infinite parallel resources is 1/s. So if 10% is sequential, maximum speedup is 10x. If 50% is sequential, maximum speedup is only 2x.

This applies beyond hardware. If your system has a database that can’t be parallelized, adding application servers hits a wall. The same holds for organizations: if one person or committee handles all architectural decisions, adding engineers increases coordination costs without increasing throughput.

Amdahl’s Law (Wikipedia)

## Examples

Adding application servers doesn’t help if all requests hit a single database instance. One database becomes the limit.

Another example is breaking a monolith into microservices won’t improve performance if all requests ultimately serialize through a shared dependency, such as an authentication or billing service.

## Origins

Gene Amdahl, a computer architect known for his work on IBM mainframes, introduced the law in 1967 at the AFIPS Spring Joint Computer Conference.

It was originally framed around processor performance but has since proven universally applicable to systems and organizations.

## Further Reading

- [Validity of the Single Processor Approach to Achieving Large Scale Computing Capabilities Gene Amdahl's original 1967 paper](https://dl.acm.org/doi/10.1145/1465482.1465560)
- [Amdahl's Law - Wikipedia Overview of the law with visual examples](https://en.wikipedia.org/wiki/Amdahl%27s_law)
- [The Mythical Man-Month Fred Brooks' classic on software engineering and scaling](https://amzn.to/3MUjDL7)

## Related Laws

- [Gustafson's Law](https://lawsofsoftwareengineering.com/laws/gustafsons-law/) — It is possible to achieve significant speedup in parallel processing by increasing the problem size.
- [Metcalfe's Law](https://lawsofsoftwareengineering.com/laws/metcalfes-law/) — The value of a network is proportional to the square of the number of users.
