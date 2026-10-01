# The Boy Scout Rule

Quality Junior

Leave the code better than you found it.

## Takeaways

- Don’t leave bad things rot in a project. This means take a moment to refactor or fix at least one small thing in the area you’re working on. It can include anything from variable names to simplifying logic.
- A cleaner codebase is easier to read, work with, and extend. This improves project maintainability and reduces technical debt.
- When every developer follows this rule, it creates a culture of ownership in the code. Teams collectively feel responsible for code quality.

## Overview

The Boy Scout Rule basically means: leave the code better than you found it. In practice, it’s not about doing big-bang rewrites or achieving perfection in one go. Instead, it’s about constant and incremental improvements.

Whenever a developer encounters a piece of code, whether adding a new feature or hunting down a bug, they take the opportunity to polish something nearby. For example, if there’s a confusing function name, you rename it clearly. If you notice some duplicated code, you refactor it into a single helper. If a test case is missing for a critical method, you add it.

These are often small changes that might take only a few extra minutes, but they compound over time.

## Examples

You’re working on an old module to add a new feature. The code works, but you notice a couple of things: there’s a function `processData()` that has more than 200 lines, and there are some `//TODO` comments and commented-out code blocks. Following the rule, you split `processData()` into smaller, better-named functions to improve readability and delete those commented-out sections that are no longer needed.

On a larger scale, Google’s engineers often say “If you touch it, you own it”. This means that when you modify code, you take ownership of its quality, leading to fixing even minor issues as they arise during unrelated tasks. Over the lifespan of a product, thousands of such small clean-ups occur, preventing major problems.

## Origins

The mantra “leave the campsite cleaner than you found it” comes from the Boy Scouts of America and Scouting organizations worldwide.

In the domain of software development, the Boy Scout Rule was popularized by Robert C. Martin (Uncle Bob) in his book “Clean Code: A Handbook of Agile Software Craftsmanship” (2008).

Uncle Bob adapted this simple wisdom to software development, recognizing that large refactoring projects rarely happen but continuous small improvements can transform a codebase over time.

## Further Reading

- [Clean Code: A Handbook of Agile Software Craftsmanship Robert C. Martin's influential book on writing clean code](https://amzn.to/3LjRFYI)
- [The Boy Scout Rule Uncle Bob's essay in 97 Things Every Programmer Should Know](https://www.oreilly.com/library/view/97-things-every/9780596809515/ch08.html)
- [Refactoring: Improving the Design of Existing Code Martin Fowler's guide to incremental code improvement](https://martinfowler.com/books/refactoring.html)
- [Code Complete Steve McConnell's comprehensive guide to software construction](https://amzn.to/3N57T8t)

## Related Laws

- [Broken Windows Theory](https://lawsofsoftwareengineering.com/laws/broken-windows-theory/) — Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.
- [YAGNI (You Aren't Gonna Need It)](https://lawsofsoftwareengineering.com/laws/yagni/) — Don't add functionality until it is necessary.
- [Technical Debt](https://lawsofsoftwareengineering.com/laws/technical-debt/) — Technical Debt is everything that slows us down when developing software.
