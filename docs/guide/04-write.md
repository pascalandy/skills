# Write and edit with the agent

Text an agent writes tends to sound like an agent wrote it. In this page you use three skills and two `andy-mode` routes to remove the robot voice, tighten prose, tell a story, shorten an answer, and check a text before you send it.

## Remove the robot voice with `unslop`

```text
unslop this: [paste your text]
```

The agent rewrites the text without the habits that give AI writing away: filler, hedging, inflated words, and formatting tics. It has an English version and a French version, and it picks the one that matches your text.

After any long answer, two words are enough:

```text
unslop that
```

## Tighten prose with `andy-mode ; write-with-clarity`

```text
andy-mode ; write-with-clarity. [paste your text]
```

The agent edits for clarity and force, following Strunk's classic rules: active voice, concrete words, no needless words. Use it on reports, summaries, and anything a busy person has to read.

## Tell a story with `andy-mode ; storytelling`

```text
andy-mode ; storytelling. Help me tell how we lost our biggest client and won them back, for a 3-minute talk to my team.
```

The agent reads what you gave it, asks only what blocks the work, and keeps your voice. In a true story, it never invents facts, quotes, or feelings. It can also diagnose a story you already wrote, or adapt one for another audience.

## Shorten an answer with `concise`

```text
concise
```

The agent switches to note form: no filler, no pleasantries, short words, and arrows for cause and effect. The meaning stays the same. Use it when you want the facts fast. For a text that other people will read, use `write-with-clarity` instead.

## Check a text before you send it with `2nd-pass`

```text
2nd-pass on this email before I send it to my director: [paste the email]
```

The agent reviews the text against what you asked for. It lists concrete mistakes, missing points, and contradictions, then fixes them or tells you what needs your call.

**Pitfall:** "make it better" gives the agent nothing to aim at. Say who reads the text and what they should do after reading it: "My director reads this in two minutes and approves the budget."

Next: [Do marketing with `corey-mode`](./05-marketing.md).
