# DRY (Don't Repeat Yourself)

Design Junior

Every piece of knowledge must have a single, unambiguous, authoritative representation.

## Takeaways

- The DRY principle is about avoiding duplication of knowledge in code. If the same idea or logic is in multiple places, it’s a signal to refactor.
- When requirements change, you should update logic in only one place. Repeated code increases the risk of inconsistencies and bugs (you might fix a bug in one copy and forget about the others).
- Be careful to apply DRY wisely. It’s about knowledge repetition, not just duplication. Sometimes two pieces of code look alike but do different jobs; merging them could over-complicate things.

## Overview

The idea of DRY is simple: each fact or piece of logic in your system should be expressed once and only once. If you find the same code, formula, or rule in multiple modules, you’re violating DRY. Such repetition creates hidden maintenance cost. When the business rule changes, you must hunt down every duplicate instance.

By following DRY, developers strive for a single, unique implementation of any given behavior. This often means abstracting common code into a function or class, or consolidating configuration into a single file.

DRY also applies to database schemas, tests, and documentation.

However, remember that DRY is about duplicated intent, not just similar-looking code. Two pieces of code can look identical but serve different purposes in an application.

DRY (Don’t Repeat Yourself)

## Examples

An application has a database connection URL in five different source files. If the database host changes, you’d have to edit all five places. The DRY approach keeps that URL in a single configuration variable that all modules read.

If two parts of an app both format dates the same way, create a single `formatDate()` utility function and call it from both places. Now if the date format needs to change, there’s precisely one function to modify.

Large codebases benefit from DRY through shared libraries. If multiple applications need the same security logic, create a shared library instead of copying code across applications.

## Origins

The term “DRY” was coined in 1999 by Andy Hunt and Dave Thomas in their book The Pragmatic Programmer. They defined it as: “Every piece of knowledge must have a single, unambiguous, authoritative representation within a system.”

Even earlier, avoiding code duplication was part of structured programming and the Unix philosophy. In Extreme Programming, a similar idea was known as “Once and Only Once.” Hunt and Thomas gave it a catchy name and expanded its scope beyond just code to all information.

## Further Reading

- [The Pragmatic Programmer, 20th Anniversary Edition The original source of the DRY principle by Hunt and Thomas](https://amzn.to/4piJutH)
- [DRY - Wikipedia Overview of the principle and related concepts](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself)
- [Code Complete Steve McConnell's guide covering code duplication and abstraction](https://amzn.to/3N57T8t)

## Related Laws

- [SOLID Principles](https://lawsofsoftwareengineering.com/laws/solid-principles/) — Five main guidelines that enhance software design, making code more maintainable and scalable.
- [Law of Demeter](https://lawsofsoftwareengineering.com/laws/law-of-demeter/) — An object should only interact with its immediate friends, not strangers.
