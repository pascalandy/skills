# The Law of Leaky Abstractions

Architecture Mid-Level

All non-trivial abstractions, to some degree, are leaky.

## Takeaways

- No matter how well-designed, abstractions (libraries, frameworks, etc.) have edge cases that depend on internal details.
- Developers should understand that using a high-level tool doesn’t absolve them from knowing what’s happening underneath, at least at a basic level.
- “Leaky” means you might encounter performance issues, bugs, or behavior that force you to consider the underlying system (e.g., networking, OS) on which the abstraction sits.
- When creating abstractions, strive to minimize leakage and document the cases in which it might break.

## Overview

This law observes that in complex systems, the abstractions we create, meant to hide complexity, *inevitably fail in some scenarios*, revealing the underlying complexity to the programmer.

For example, consider an ORM (object-relational mapper) that lets you treat database entries as objects. Most of the time it works, but occasionally you hit a case where performance is terrible and you have to think about the SQL queries being generated. The abstraction “leaks” details of the database.

The law isn’t saying abstractions are bad. They are essential. But it reminds us that **one must be prepared for when they break**.

![The Law of Leaky Abstractions illustration](/images/laws/leaky-abstractions.png)

Leaky Abstractions

## Examples

A good example is **memory management in high-level languages**. Languages like Java and Python abstract away manual memory allocation thanks to garbage collection. Yet leaks still happen (objects not being freed due to lingering references), or you encounter the abstraction’s limits (such as GC pauses affecting performance). Suddenly, the developer needs to know how garbage collection works internally, and the abstraction of “infinite memory” has leaked.

Web developers often treat an HTTP request as something fast, abstracting away the network. However, when latency spikes or packets drop, the network’s reality leaks into your application.

## Origins

Joel Spolsky introduced this law in a 2002 blog post. He gave examples such as TCP (which abstracts reliable connections over IP, but on a bad network the abstraction leaks, causing timeouts) or the virtual memory abstraction.

The concept resonates with many earlier thoughts in computing, essentially a restatement of “there’s no free lunch” with abstractions.

## All Models Are Wrong (George Box's Law)

George Box said, “*All models are wrong, but some are useful.*” Every abstraction you build, whether a class hierarchy, an API contract, or a data model, is a lie. It’s basically **a simplified version of reality that ignores inconvenient details**. The question isn’t whether your model is wrong. It’s whether it’s wrong in ways that matter.

Your database schema assumes users have one email address, until they don’t. Your payment model treats refunds like reversed payments, until chargebacks arrive. Accept that every model will leak, and design for the leak, not against it.

## Further Reading

- [The Law of Leaky Abstractions Joel Spolsky's original blog post](https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/)
- [A Note on Distributed Computing Fallacies of Distributed Systems](https://scholar.harvard.edu/waldo/publications/note-distributed-computing)
- [Towards a New Model of Abstraction in Software Engineering Gregor Kiczales' foundational paper on open implementations and abstraction leakage](https://web.archive.org/web/20110604013045/http://www2.parc.com/csl/groups/sda/publications/papers/Kiczales-IMSA92/for-web.pdf)

## Related Laws

- [Hyrum's Law](https://lawsofsoftwareengineering.com/laws/hyrums-law/) — With a sufficient number of API users, all observable behaviors of your system will be depended on by somebody.
- [Gall's Law](https://lawsofsoftwareengineering.com/laws/galls-law/) — A complex system that works is invariably found to have evolved from a simple system that worked.
