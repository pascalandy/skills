# The Ninety-Ninety Rule

Planning Mid-Level

The first 90% of the code accounts for the first 90% of development time; the remaining 10% accounts for the other 90%.

## Takeaways

- The final parts of a project (polishing, edge cases, integration, bug fixes) often take far more effort than anticipated, often as much as the initial development.
- What looks like the “finishing touches” involves many tricky problems and unknowns.
- Reaching a “mostly done” state can create optimism, but the rule warns that “almost done” often means only halfway in terms of time.

## Overview

This rule quantifies the extent to which projects get stuck in the final phase. Often, teams make good progress at the start, building core functionality, which leads to optimism. Then integration, corner cases, performance tuning, and bug fixing consume an unexpectedly large amount of time, often equal to or greater than what has already been spent.

In practical terms, this rule advises that the last bit of a project is not a small bit. You should plan for a significant effort in finishing, polishing, and delivering.

It is also related to Hofstadter’s Law, as it is another way our estimates fall short. We do not realize how hard that last leg is.

## Examples

A team develops a new app. In three months, the core features are done, and they hit “90% of the functionality.” Everyone expects to ship in one more month. Instead, integration testing reveals that multiple modules do not talk correctly, specific edge inputs crash the app, memory usage is too high. That final “10%” takes another three months.

When implementing a new website, you get a basic version up quickly (login, basic pages). The last bits: cross-browser fixes, responsive design adjustments, accessibility improvements, writing tests, and performance improvements seem like 10% of the work, but they take as much time as the main coding.

The rule is an important reminder: **Do not celebrate too early!**

## Origins

Credited to Tom Cargill of Bell Labs, and popularized by Jon Bentley’s September 1985 “Bumper-Sticker Computer Science” column in Communications of the ACM. It was originally called the “Rule of Credibility”, a name which did not stick.

It became popular in programming circles and is frequently referenced in discussions of why software is usually delivered late or why “90% done” claims can be misleading.

## Further Reading

- [Programming Pearls - Bumper Sticker Computer Science Jon Bentley's original column where the rule was popularized](https://moss.cs.iit.edu/cs100/Bentley_BumperSticker.pdf)
- [Programming Pearls (Book) Jon Bentley's classic book on programming wisdom and techniques](https://amzn.to/49bLHkn)
- [Ninety-Ninety Rule - Wikipedia Overview of the rule and its origins at Bell Labs](https://en.wikipedia.org/wiki/Ninety%E2%80%93ninety_rule)
- [Identifying and Mitigating the Ninety-Ninety Rule in Software Development Practical strategies for recognizing and countering the ninety-ninety trap](https://dev.to/ben/identifying-and-mitigating-the-ninety-ninety-rule-in-software-development-4ap3)

## Related Laws

- [Hofstadter's Law](https://lawsofsoftwareengineering.com/laws/hofstadters-law/) — It always takes longer than you expect, even when you take into account Hofstadter's Law
- [Parkinson's Law](https://lawsofsoftwareengineering.com/laws/parkinsons-law/) — Work expands to fill the time available for its completion.
- [Pareto Principle (80/20 Rule)](https://lawsofsoftwareengineering.com/laws/pareto-principle/) — 80% of the problems result from 20% of the causes.
