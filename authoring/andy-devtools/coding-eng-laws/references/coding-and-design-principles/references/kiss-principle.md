# KISS (Keep It Simple, Stupid)

Design Junior

Designs and systems should be as simple as possible.

## Takeaways

- KISS primarily refers to avoiding complexity in solution designs. A solution that satisfies the requirement and is simple in design is better than a complex one.
- Code that is coded is easier and faster to understand and debug. It’s even easier to understand and fix if you’re your own future self. Smarter code may look impressive at first, but it often masks problems.
- The code solution should be as simple as possible. Anything that adds complexity unnecessarily is counter to the KISS Principle.

## Overview

The KISS principle is a reminder that simplicity should be a key goal. If you can solve a problem with a 50-line script versus a complex 500-line solution, KISS favors the 50-line solution because each line of code has the potential to cause an error.

Why is simplicity so important? Software has to be understood by humans. A simple design is much easier to maintain: new team members can get up to speed faster, bugs are easier to localize, and modifications cause fewer ripple effects.

The KISS principle encourages developers to resist “clever” code that does too much at once, and to avoid architecting solutions that address future problems at the cost of current complexity.

## Examples

A web application needs to generate reports. A KISS approach would use a simple script or existing library to query the database and output a CSV. A non-KISS approach would design a complete plug-in architecture “just in case” you need it more generically later. If requirements are small, the latter is overkill.

When writing a function to parse a file, a KISS implementation uses simple logic: open the file, read line by line, split fields, handle errors. A complex approach might implement a fully generic parser-combinator framework. Unless you truly need that generality, the simpler approach will be easier to get right and maintain.

Many experienced engineers advise: “First make it work, then make it right, then make it fast (if needed).”

## Origins

The phrase “Keep It Simple, Stupid” came from the U.S. military. It’s attributed to Kelly Johnson, a lead engineer at Lockheed’s Skunk Works in the 1960s. Johnson challenged his team: design an aircraft that could be repaired with basic tools by an average mechanic in the field.

Influential programmers such as Edsger Dijkstra and C.A.R. Hoare often discussed complexity. Hoare said, “There are two ways of constructing a software design: One way is to make it so simple that there are obviously no deficiencies, and the other way is to make it so complicated that there are no obvious deficiencies. The first method is far more difficult.”

The KISS principle has since become a cornerstone of software engineering best practices.

## Further Reading

- [A Philosophy of Software Design John Ousterhout's book on managing complexity in software](https://amzn.to/3N1uR0f)
- [KISS Principle - Wikipedia Overview of the principle and its origins](https://en.wikipedia.org/wiki/KISS_principle)
- [Code Complete Steve McConnell's practical handbook emphasizing simplicity in code](https://amzn.to/3N57T8t)

## Related Laws

- [YAGNI (You Aren't Gonna Need It)](https://lawsofsoftwareengineering.com/laws/yagni/) — Don't add functionality until it is necessary
- [Principle of Least Astonishment](https://lawsofsoftwareengineering.com/laws/principle-of-least-astonishment/) — Software and interfaces should behave in a way that least surprises users and other developers.
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked.
