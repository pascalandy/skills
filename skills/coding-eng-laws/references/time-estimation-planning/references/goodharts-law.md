# Goodhart's Law

Planning Senior

When a measure becomes a target, it ceases to be a good measure.

## Takeaways

- If you set a particular metric as a goal (e.g., lines of code written, number of features closed), people will find ways to optimize for that metric.
- Metrics are proxies for what you value (productivity, quality, etc.). Once they’re targets, people meet the metric even if it undermines the original intent.
- Metrics are useful for insight, but they must be used in context and balanced with qualitative judgment.
- Combine multiple metrics to avoid a singular focus that can be gamed.

## Overview

Goodhart’s Law comes from economics and is very relevant to software teams. For instance, a manager might set a target that “we must close 100 bug tickets this month.” Developers, feeling pressure, might start closing tickets that are not truly resolved or splitting a single bug into multiple tickets to inflate numbers.

The metric (tickets closed) goes up, but software quality might not. Making the metric a goal distorts the process, so it loses its correlation with actual success. This is why experienced leaders use metrics as indicators rather than targets, and always consider the broader context.

Goodhart’s Law

## Examples

A software team was rewarded based on the lines of code written. Developers start writing verbose code and copying and pasting into multiple places (violating DRY) to increase the line count. The software becomes bloated while the metric looks great.

Another example: a QA team measured by the number of test cases executed favored running many easy tests rather than doing proper testing. They met objectives but missed critical bugs.

Similarly, when teams focus on **code coverage percentage** as a primary target, developers write trivial unit tests that do not assert meaningful behavior, while necessary integration tests are skipped.

In today’s world we see something similar with AI tokens consumed per engineer (a practice sometimes called **tokenmaxxing**), where more tokens is considered better, and even become one of the goals that people need to fulfill for their performance reviews.

## Origins

Named after economist Charles Goodhart, who originally described this phenomenon in the context of monetary policy metrics. Marilyn Strathern later provided the commonly cited phrasing: “When a measure becomes a target, it ceases to be a good measure.”

This concept has been discussed extensively in education and business KPIs, and certainly applies to software engineering metrics where velocity, code coverage, and bug counts are often used as targets.

## Further Reading

- [Goodhart's Law: How Measuring The Wrong Things Drive Immoral Behaviour Deep dive into Goodhart's Law and its implications for organizations](https://coffeeandjunk.com/goodharts-campbells-law/)
- [Goodhart's Law - Wikipedia Overview of the law's origins and applications](https://en.wikipedia.org/wiki/Goodhart%27s_law)
- [The Tyranny of Metrics Jerry Muller's book on the unintended consequences of metric fixation](https://amzn.to/4ji7rzY)
- [Enshittification - Wikipedia How platforms degrade quality once metrics replace user value as the goal](https://en.wikipedia.org/wiki/Enshittification)

## Related Laws

- [Dilbert Principle](https://lawsofsoftwareengineering.com/laws/dilbert-principle/) — Companies tend to promote incompetent employees to management to limit the damage they can do.
- [Parkinson's Law](https://lawsofsoftwareengineering.com/laws/parkinsons-law/) — Work expands to fill the time available for its completion.
