# Lehman's Laws of Software Evolution

Quality Senior

Software that reflects the real world must evolve, and that evolution has predictable limits.

## Takeaways

- The first law, Continuing Change, states that if a system isn’t continuously updated to meet new needs, it becomes less satisfactory to use. In practice, this means that successful software is never truly “finished”; to remain useful, it undergoes ongoing enhancements (or else users abandon it for something that keeps up).
- Over time, changes accumulate, making the system more complex (Law 2). Unless developers invest in refactoring or restructuring (i.e., paying down technical debt), the system’s internal complexity will increase, slowing further development.
- Even if users demand more, a development organization can only do so much in a given time. They can’t exponentially accelerate delivery forever. Factors such as team knowledge (familiarity) and process overhead limit it.
- The perceived quality of the system will decline (perhaps due to rising user expectations, environmental changes, or the accumulation of minor issues).

## Overview

Lehman’s Laws describe an unavoidable reality of long-lived software systems that operate in the real world. Such systems, business software, operating systems, and platforms, must continuously change to remain useful. That change is neither optional nor free.

As software evolves, complexity accumulates. Each change slightly increases internal disorder unless effort is spent counteracting it. Over time, this complexity reduces development speed, increases risk, and raises the cost of further change. Teams feel this as “everything taking longer than it used to.”

Organizations face hard limits: knowledge, coordination, and familiarity constrain how much change can be absorbed in a single release. Adding people does not remove these limits; it often reinforces them.

Lehman’s Laws of Software Evolution

## Examples

Consider a big **enterprise resource planning (ERP) system** deployed in 2000. Over 25 years, updates included new business rules, integrations with new technologies, and UI refreshes. According to Law 1 (Continuing Change), this was necessary. If they hadn’t continued updating, the system would no longer meet business needs. The company observes that adding functionality in 2025 takes longer than it did in 2005, reflecting Laws 2 and 7. Periodically, cleanup projects (refactoring) were needed, but output per year stabilized (Laws 4 and 5).

The **Linux kernel** provides another example. It has undergone continuous change, adapting to new hardware and requirements. If it stopped adapting, it would become irrelevant. Its functionality has grown massively, and complexity has increased, requiring subsystem maintainers.

The “conservation of familiarity” is seen in how changes are managed: big rewrites are rare, and maintainers enforce a pace the community can keep up with.

## Origins

Lehman’s early laws were formulated in 1974, based on his study of various software, including IBM’s OS/360. Lehman and Belady observed version histories, growth metrics, and other data, leading to the initial three laws.

Over the years, Lehman refined the laws through the 1980s and 1990s as more projects provided data. Initially there were 3 laws (1974), then 5, and eventually 8 laws by the 1990s.

## Further Reading

- [Programs, Life Cycles, and Laws of Software Evolution Lehman & Belady's original 1980 paper on software evolution](https://ieeexplore.ieee.org/document/1456074)
- [Laws of Software Evolution - The Nineties View Lehman et al. 1997 update on the laws with additional research](https://ieeexplore.ieee.org/document/637156)
- [The Evolution of the Laws of Software Evolution Overview of how Lehman's Laws evolved over time](https://link.springer.com/chapter/10.1007/978-3-540-75381-0_1)

## Related Laws

- [Brooks's Law](https://lawsofsoftwareengineering.com/laws/brooks-law/) — Adding manpower to a late software project makes it later.
- [Conway's Law](https://lawsofsoftwareengineering.com/laws/conways-law/) — Organizations design systems that mirror their own communication structure.
- [Technical Debt](https://lawsofsoftwareengineering.com/laws/technical-debt/) — Technical Debt is everything that slows us down when developing software.
