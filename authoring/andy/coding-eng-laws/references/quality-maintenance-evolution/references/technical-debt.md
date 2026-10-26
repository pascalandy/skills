# Technical Debt

Quality Junior

Technical Debt is everything that slows us down when developing software.

## Takeaways

- When we take a shortcut in code, we borrow time from the future. This gives an immediate benefit, but you owe principal (the work to fix) plus interest.
- If technical debt is not repaid, it accrues interest. Each minute spent on dirty code, bugs, and workarounds due to a lack of refactoring is interest on the debt.
- Not all technical debt is inherently bad. It is sometimes necessary, for instance, for market timing or prototyping.
- The way to pay down technical debt is to refactor code, add missing tests, and improve design.

## Overview

Technical debt highlights a fundamental tension in software engineering: speed vs. quality. The term helps explain to both developers and non-technical stakeholders why seemingly “done” software still needs ongoing work. When you write clumsy code or postpone cleanup, you’ve essentially taken out a loan: you get short-term feature delivery, but the complexity you introduce is the interest you’ll keep paying.

Properly managing technical debt means being conscious of when you’re adding a quick workaround or a “temporary” hack, and having a plan to revisit it. Teams often use tools to log technical debt items (like comments, issue tracker tickets, or dedicated debt backlogs).

When managed, technical debt can be an effective tool; you intentionally take on a bit of messiness to get feedback or meet a deadline, then clean it up. But if ignored, debt becomes a problem.

## Examples

A typical example is skipping automated tests. A team under deadline pressure releases a new feature without writing tests. The release is successful (debt incurred). But later, making changes becomes harder since every change risks unforeseen bugs because there’s no safety net of tests (interest payments). Eventually they must stop adding features and fix the debt by adding the missing tests and refactoring.

Another example is a startup that wants to deliver a quick prototyping effort to onboard the first customer. Developers do rapid but messy coding, with hardcoded variables and copy-and-paste code. This approach is made with technical debt in mind. The endeavor helps the startup win a customer; however, the customer’s codebase is now full of technical debt.

If they just continue to add to it, they will face bugs and slower performance due to the messy code (interest on debt). They realize this and therefore set up a “rehab” sprint to refactor the code, thereby resolving the most troublesome bits.

Technical Debt Metaphor (source: Richard Scarry’s Storybook Dictionary)

## Origins

The term “Technical Debt” was coined by Ward Cunningham (one of the authors of the Agile Manifesto) at the OOPSLA conference in 1992. He first used the financial metaphor while working on a finance application to explain to his boss why the team needed time to refactor code.

Ward compared developing software to borrowing money: it can be wise to take shortcuts (borrow) to achieve something sooner, provided you pay back the loan by cleaning up the code later.

## Further Reading

- [Debt Metaphor - Ward Cunningham Ward Cunningham's video explaining the original debt metaphor (OOPSLA 1992)](https://www.youtube.com/watch?v=pqeJFYwnkjE)
- [Technical Debt - Martin Fowler Martin Fowler's comprehensive blog post on technical debt](https://martinfowler.com/bliki/TechnicalDebt.html)
- [Technical Debt - Wikipedia Overview of the concept and its management strategies](https://en.wikipedia.org/wiki/Technical_debt)
- [Accelerate Forsgren, Humble, and Kim's research on how technical debt impacts software delivery](https://amzn.to/48Xugp3)

## Related Laws

- [Broken Windows Theory](https://lawsofsoftwareengineering.com/laws/broken-windows-theory/) — Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.
- [Hofstadter's Law](https://lawsofsoftwareengineering.com/laws/hofstadters-law/) — It always takes longer than you expect, even when you take into account Hofstadter's Law
- [The Boy Scout Rule](https://lawsofsoftwareengineering.com/laws/boy-scout-rule/) — Leave the code better than you found it.
