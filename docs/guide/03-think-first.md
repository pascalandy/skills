# Think before the agent acts

A vague request gets a vague answer, and a rushed decision costs more than the minutes it saved. In this page you use three skills and two `andy-mode` routes. They make the agent understand the goal first, or make your own thinking sharper before you decide.

## Agree before doing with `consensus`

```text
I want to move my team's weekly status report from email to a shared dashboard.

consensus
```

The agent changes nothing yet. It restates your goal and the problem in its own words. For each point to settle, it shows the CMO, how things work today, and the FMO, the change it suggests. Then it asks its questions, at most four per round, each with lettered choices and its recommendation marked 🟢, so you can reply "1a, 2b".

It applies your answers, rethinks its proposals, and asks again until nothing is left to decide. Then it says "👍 Je n'ai plus de question.", French for "I have no questions left". Read its proposals, and say `go` only when they're right.

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

**Pitfall:** don't write "agree on it and do it" in one request. `consensus` stops before doing on purpose, so you can catch a wrong idea while it's still cheap. Say `go` once its proposals are right.

Next: [Write and edit with the agent](./04-write.md).
