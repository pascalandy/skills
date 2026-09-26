# Kernighan's Law

Quality Junior

Debugging is twice as hard as writing the code in the first place.

## Takeaways

- Bug detection and removal is more complex than programming because debugging requires understanding both the code and why it doesn’t work.
- If you write code at the limit of your intelligence, you won’t be able to understand or troubleshoot it later.
- Simple code with good structure and documentation is easier to debug, saving time in the long run.
- Even if your code runs successfully when you write it, it’s fragile if it’s too complex.

## Overview

Kernighan’s Law says that debugging requires understanding what the code *actually* does, which can be twice as hard as writing it. When coding, you operate with a specific mental model and full context. When debugging, you might be dealing with someone else’s code or your own code after that context has faded.

Writing “clever” or complex code is essentially setting a trap for your future self. A maintainable version is usually superior to an optimized version that is difficult to understand. As Kernighan implies, if you make your code too tricky, you’ve essentially outsmarted yourself.

Kernighan’s Law

## Examples

Imagine a developer writing a function in a compressed style, chaining multiple operations in one line:

```
public string GetUserDisplay(User u) => u?.IsActive == true ? (u.Name ?? "").Trim() is var n && n.Length > 0 ? n + (u.Role > 0 ? $" ({(Role)u.Role})" : "") : "Unknown" : "Inactive";
```

The proper, readable version:

```
public string GetUserDisplay(User user) { if (user is null || !user.IsActive) return "Inactive"; var name = user.Name?.Trim(); if (string.IsNullOrEmpty(name)) return "Unknown"; if (user.Role > 0) return $"{name} ({(Role)user.Role})"; return name; }
```

The clever version might have taken 30 minutes to write, but debugging took 3 hours. Had the code been written clearly, it would’ve taken 45 minutes to write, but only 30 minutes to debug later.

## Origins

Brian Kernighan first expressed this idea in *The Elements of Programming Style* (1974, second edition 1978) with P.J. Plauger. Kernighan, famous for co-authoring “The C Programming Language” and “The Elements of Programming Style,” wrote about simplicity in the days of resource-constrained computing.

## Further Reading

- [The C Programming Language The classic 'K&R' book co-authored by Brian Kernighan](https://amzn.to/3YLSFYy)
- [The Elements of Programming Style Kernighan and Plauger's guide to writing clear code](https://www.amazon.com/Elements-Programming-Style-2nd/dp/0070342075)
- [Code Complete Steve McConnell's comprehensive guide to software construction](https://amzn.to/4smkSmE)

## Related Laws

- [KISS (Keep It Simple, Stupid)](https://lawsofsoftwareengineering.com/laws/kiss-principle/) — Designs and systems should be as simple as possible.
- [Premature Optimization (Knuth's Optimization Principle)](https://lawsofsoftwareengineering.com/laws/premature-optimization/) — Premature optimization is the root of all evil.
