# Pareto Principle (80/20 Rule)

Decisions Junior

80% of the problems result from 20% of the causes.

## Takeaways

- Identify the top 20% of factors that contribute to 80% of whatever you care about. This could be 20% of features that account for 80% of usage, or 20% of bugs that cause 80% of crashes. Prioritize your time and resources on those vital few for maximum impact.
- Don’t spend the same effort on everything. If a particular area of code is rarely run, it probably doesn’t need the same optimization or attention as a hotspot.
- It’s not always exactly 80/20, but the idea is the same. Use profiling, analytics, and data gathering to empirically identify where the imbalances are.
- On a personal level, as an engineer or manager, identify which tasks produce most of your value. It might be coding core features or coaching team members.

## Overview

The Pareto Principle is more of an observation than a law, but the 80/20 pattern (or similar ratios like 90/10) appears frequently.

In the domain of software engineering we say that, “80% of the time in a program is spent in 20% of the code.” This insight is significant for optimization: instead of micro-optimizing everything, profile to identify the hot 20% and optimize that.

The principle influences product development too. Often, a few core features satisfy the majority of user needs. When planning an MVP, teams focus on that core set rather than trying to do everything. It is an essential check against equal prioritization: everything is not equally important.

The Pareto Principle encourages strategic allocation of effort to maximize outcomes by investing where returns are highest.

Pareto Principle

## Examples

Microsoft found that around **20% of bugs in Windows and Office caused 80% of all crashes**, and a tiny 1% of bugs caused around 50% of errors. By focusing on the critical 1-20% of bugs, they dramatically improved stability. This is textbook Pareto: address the small set of high-impact issues to make most users happier quickly.

A software team analyzed usage analytics and discovered that out of 50 features, only 5-10 (10-20%) were used by 80%+ of users. This guided them to simplify the interface around core features and remove unused ones.

**Hot spots in code** follow the Pareto pattern. A small part of the codebase drives most defects, slowdowns, and “scary to touch” work. Track commits plus incidents to find them, then pay down debt where it compounds: add tests, simplify paths, reduce coupling, tighten interfaces.

## Origins

The principle is named after Vilfredo Pareto, an Italian economist who in 1906 noted that about 80% of Italy’s land was owned by 20% of the population.

In the 1940s, quality management pioneer Joseph M. Juran adopted the idea when analyzing industrial defects, calling it the “vital few and trivial many” rule. Juran observed that by focusing on the vital few quality issues, one could improve quality with less effort than trying to tackle all problems at once.

## Further Reading

- [Microsoft's CEO: 80-20 Rule Applies To Bugs How Microsoft applied Pareto to prioritize bug fixes](https://www.crn.com/news/security/18821726/microsofts-ceo-80-20-rule-applies-to-bugs-not-just-features)
- [The 80/20 Principle - Richard Koch Book on applying the Pareto Principle to business and life](https://amzn.to/44QjIFH)
- [Pareto Principle - Wikipedia Overview of the principle and its applications](https://en.wikipedia.org/wiki/Pareto_principle)
- [Full Text of 10/02 Ballmer Memo Steve Ballmer's 2002 memo referencing the 80/20 rule in Microsoft's strategy](https://www.eweek.com/enterprise-apps/full-text-of-10-02-ballmer-memo/)

## Related Laws

- [Premature Optimization (Knuth's Optimization Principle)](https://lawsofsoftwareengineering.com/laws/premature-optimization/) — Premature optimization is the root of all evil.
- [KISS (Keep It Simple, Stupid)](https://lawsofsoftwareengineering.com/laws/kiss-principle/) — Designs and systems should be as simple as possible.
- [Tesler's Law (Conservation of Complexity)](https://lawsofsoftwareengineering.com/laws/teslers-law/) — Every application has an inherent amount of irreducible complexity that can only be shifted, not eliminated.
