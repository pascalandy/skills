# Current implementation notes

Observed in version 2.0 code and tests, dated 2026-02-10:

- A cache key includes input contents, configuration, and tool version
- A matching key returns the stored command result
- Changing any key input causes a miss
- The cache is local to one machine
- No test measures team adoption, time saved, cost saved, or delivery outcomes
