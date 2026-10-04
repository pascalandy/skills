# Epic template

Step 4 writes every issue as an issue entry, and Step 5 builds each Epic from the whole template.

## Issue entry

The user reads this entry instead of the issue, so it must stand alone: a plain-words name, then what happens today and what changes after. The number goes in parentheses, for bookkeeping only. Mark the entry `text` when only prose changes and `code + tests` when the fix touches code.

```md
- **<the problem, in plain words>** (#<number>) · <text | code + tests>
  - Today: <what happens now, with the evidence that sizes it: how often, what it cost>
  - After: <what changes once the fix lands>
```

Example:

```md
- **A silent `just check`** (#430) · text
  - Today: when every check passes, `just check` prints nothing. The agent thinks the output got lost and reruns it three or four times. It happened twice
  - After: `AGENTS.md` says that silence means every check passed
```

## Epic issue

Title: `Epic <N> · <the outcome, in plain words>`

```md
## Why this Epic

<Two or three sentences: the system the members touch, and what goes wrong today.>

## Issues

Each issue is marked **text** (only prose changes) or **code + tests**.

### <group: a pipeline step or subsystem>

<issue entries>

## Good to know

<Facts the next planner needs, such as a fix that quotes text that has since changed. Drop this section when it is empty.>

## Done when

<An outcome someone can check.> Each issue is closed, with its fix on the default branch.

## Out of this Epic

- <Neighboring work, and the Epic or issue that owns it>
- How to implement and review these issues: decided when this Epic is planned

<The signature the user sets>
```

Leave out how to work the Epic, such as PR order or review steps.
