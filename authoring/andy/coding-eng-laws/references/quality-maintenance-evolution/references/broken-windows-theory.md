# Broken Windows Theory

Quality Mid-Level

Don't leave broken windows (bad designs, wrong decisions, or poor code) unrepaired.

## Takeaways

- If you let minor bugs and bad style slide, people assume quality doesn’t matter, and they’ll ship messier code.
- A clean, well-maintained codebase encourages engineers to keep it clean, whereas a chaotic codebase encourages corner-cutting and further degradation.
- Fix problems while they’re small. Refactor destructive code, update outdated docs, to prevent a downward spiral of code health.

## Overview

The Broken Windows Theory in software was popularized by the book The Pragmatic Programmer. In a city, a broken window left unfixed signals neglect and invites more vandalism. Similarly in code, an apparent bug or messy section left untreated can lead to more developers bypassing the process or introducing more mess.

The idea is that quality problems snowball if left unaddressed. For example, if a team routinely ignores failing tests or lets linters/errors slide during builds, developers get the message that it’s okay to ship sloppy work. This accelerates code decay (also known as software entropy).

Conversely, if a team quickly fixes minor issues and maintains high standards, it creates a culture of quality.

## Examples

Consider a codebase with a few obvious kludges, such as functions with `// TODO: fix this hack` comments that never get fixed. If newcomers see that, they may be more inclined to add their own hacks (“this project is full of hacks anyway…”). Or if there’s a module with no tests (a “broken window” in a test-coverage sense), other modules might start losing tests too as discipline erodes.

On the opposite side, think of a project where maintainers aggressively fix style issues and simplify code whenever they spot a problem. By contributing to such a project, developers quickly learn to match that cleanliness.

Many teams have turned projects around by paying off technical debt and cleaning up code. Once things are polished, they find fewer new bugs are introduced because everyone is more careful.

## Origins

The Broken Windows Theory comes from criminology (James Q. Wilson and George Kelling, 1982). In software, Andy Hunt and Dave Thomas applied it as a metaphor in The Pragmatic Programmer (1999). They argued for fixing minor problems promptly.

Jeff Atwood and others in blogs have also discussed this principle in the context of software project maintenance.

## Further Reading

- [The Broken Window Theory - Coding Horror Jeff Atwood's discussion of applying this theory to software](https://blog.codinghorror.com/the-broken-window-theory/)
- [Broken Windows Theory - Wikipedia The original criminological theory](https://en.wikipedia.org/wiki/Broken_windows_theory)
- [The Pragmatic Programmer The book that popularized this concept in software engineering](https://amzn.to/4qygIq6)
- [Joy of Programming: The Broken Window Theory Practical application of the theory in software development](https://opensourceforu.com/2011/05/joy-of-programming-broken-window-theory/)

## Related Laws

- [Technical Debt](https://lawsofsoftwareengineering.com/laws/technical-debt/) — Technical Debt is everything that slows us down when developing software.
- [The Boy Scout Rule](https://lawsofsoftwareengineering.com/laws/boy-scout-rule/) — Leave the code better than you found it.
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked.
