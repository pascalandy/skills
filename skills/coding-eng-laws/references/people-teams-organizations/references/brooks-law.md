# Brooks's Law

Teams Mid-Level

Adding manpower to a late software project makes it later.

## Takeaways

- Simply throwing more developers at a project that’s running behind schedule usually slows it down further initially.
- New people take time to get up to speed, consuming existing team members’ time for training and coordination, which reduces overall productivity.
- Instead of hoping manpower will solve slippage, adjust the scope or timeline. Be wary of ‘just hire more coders’ as a solution to lateness.

## Overview

Brooks’s Law challenges the belief that a software development effort is perfectly divisible among people. In reality, adding a person to a project incurs training costs and increases the number of communication paths. This can outweigh that person’s contribution for a while.

If a project is already late, adding new developers can cause further delays as they learn the system and may introduce new bugs. Brooks illustrated this with the analogy: “You cannot get a baby in one month by impregnating nine women.” The law doesn’t say adding people never helps, but as a response to lateness, it’s usually counterproductive.

Brooks’s Law

## Examples

A project is one month behind schedule, so management adds 3 new developers to a 5-person team. Over the next few weeks, progress slows. The original developers spend much of their time explaining the design and code to newcomers, and merging their work causes integration headaches. The project slips further, now two months late.

A complex bug required deep knowledge of the system. Adding more people didn’t help because only the original dev understood it, and more debuggers only made things worse. Scaling a software team isn’t linear. After a point, more members yield less and less output per person.

## Origins

**Frederick P. Brooks Jr.**, who managed the IBM OS/360 project, formulated this law based on painful experience. His book *The Mythical Man-Month* (1975) explores why software projects fail and where management assumptions break down.

The book famously challenged the notion that “man-months” are interchangeable. Brooks demonstrated through real-world examples why the assumption that 12 programmers can do in one month what one programmer does in 12 months fails in software development.

## Further Reading

- [The Mythical Man-Month Fred Brooks's classic book on software engineering](https://amzn.to/4peJbjC)
- [Brooks's Law - Wikipedia Wikipedia article on Brooks's Law](https://en.wikipedia.org/wiki/Brooks%27s_law)
- [No Silver Bullet Fred Brooks's essay on essential vs accidental complexity](https://en.wikipedia.org/wiki/No_Silver_Bullet)

## Related Laws

- [Conway's Law](https://lawsofsoftwareengineering.com/laws/conways-law/) — Organizations design systems that mirror their own communication structure.
- [Second-System Effect](https://lawsofsoftwareengineering.com/laws/second-system-effect/) — Small, successful systems tend to be followed by overengineered, bloated replacements.
- [Law of Unintended Consequences](https://lawsofsoftwareengineering.com/laws/law-of-unintended-consequences/) — Whenever you change a complex system, expect surprise.
