# Think before the agent acts

A vague request gets a vague answer, and a rushed decision costs more than the minutes it saved. In this page you use three skills and two `andy-mode` routes. They make the agent understand the goal first, or make your own thinking sharper before you decide.

## Plan before doing with `plan`

```text
plan I want to move my team's weekly status report from email to a shared dashboard
```

The agent restates your goal in its own words, lists the cases to cover, and says what's out of scope. If it needs a decision from you, it stops and asks. Then it describes how things work today, how they'll work after the change, how you'll know it worked, and what could go wrong.

It does nothing until you say `go`. Read the plan, answer the questions, and say `go` only when the plan is right.

## Get grilled with `grilling`

```text
grill me on my plan to open a second location next spring
```

The agent interviews you in rounds. Each round holds the questions you can answer now, numbered, each with the answer it recommends. Your answers open the next round. The interview ends when no decision is left unexamined, and the agent acts on nothing until you confirm you both understand the plan the same way.

Use `grilling` when you already have a plan and want its weak spots found before you commit.

## Challenge an opinion with `andy-mode ; sparring`

```text
andy-mode ; sparring. Every small business needs its own mobile app.
```

The agent acts as a blunt sparring partner. It restates your claim, says whether it agrees and how sure it is, and separates what it knows from what it guesses. Then it names the assumptions hiding in your claim, where you're partly right, and what evidence would change its mind. It doesn't flatter you, and it holds its position unless you bring a better argument.

## Untangle a decision with `andy-mode ; think`

```text
andy-mode ; think. Should I hire a junior or a senior for my first employee?
```

The agent finds the one uncertainty that would change your decision. It picks a single reasoning method to reduce that uncertainty and tells you which one and why. You get a clearer view of the decision, not a list of every possible angle.

## Research a topic with `research`

```text
research how bakeries in Montreal price custom cakes. Cite your sources.
```

The agent follows each claim back to the source that owns it, such as a business's own website or an official page, and cites it. Open at least one source to check the answer instead of trusting it.

**Pitfall:** don't write "plan it and do it" in one request. `plan` stops before doing on purpose, so you can catch a wrong idea while it's still cheap. Say `go` once the plan is right.

Next: [Write and edit with the agent](./04-write.md).
