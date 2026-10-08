# Recipes and pitfalls

Prompts worth copying, then the mistakes everyone makes once. Swap in your own business and details. The recipes are informal on purpose. That's how people type, and the skills read intent well.

## Prepare a hard meeting

```text
grill me on my proposal to cut our software budget by 20 percent
```

Then, in the same chat:

```text
html-mode ; slides. Turn what we settled into a 5-slide deck for the meeting.
```

The interview finds the questions your audience will ask. The deck answers them.

## Go from an idea to a launch email

```text
andy-mode ; sparring. Restaurant owners will pay for monthly bookkeeping by text message.
```

If the idea survives, plan the launch, then write the emails:

```text
marketing ; launch. Plan the launch of bookkeeping by text message.
```

```text
marketing ; emails. Write the announcement sequence from that launch plan.
```

## Write a LinkedIn post

```text
marketing ; social. Write a LinkedIn post about what I learned from our first 100 clients.
```

Then:

```text
unslop that
```

## Turn a long answer into something you can use

```text
concise
```

```text
2nd-pass. Is anything missing before I send this to my team?
```

## Steer the agent in one line

Short replies redirect a run:

```text
I asked for options, not a final version.
```

```text
Which skill did you open, and what is its first step?
```

```text
new task. Forget the earlier topic.
```

For a truly new topic, a new chat works better than "new task". Long chats carry old details that leak into new answers.

## The pitfalls

- **Listing several skills in one request.** "Use sparring, then storytelling, then copywriting" makes the agent rush each step. State the goal, and run one route at a time.
- **A vague goal.** "Make it better" gives the agent nothing to aim at. Say who reads the result and what they should do next.
- **Skills that need a computer.** Some skills work on files on a computer or call outside services: `image-creator`, `transcript`, `html-publish`, `tavily`, and the `andy-mode` routes `cass`, `qmd`, and `trello`, among others. In a chat app they fail, or the agent improvises. Every skill this guide names works in a chat app.
- **An agent that skipped the skill.** If the answer names no skill and never asks the playbook's questions, the agent may have guessed. Ask which skill it opened. If it can't say, paste the sentence from [page 1](./01-get-started.md) again.
- **Saying `go` too early.** `consensus` changes nothing until no question is left, so you can catch a wrong idea while it's cheap. Read its proposals first.
- **Trusting a number without a source.** Ask for sources, and open at least one.

That's the guide. If you skipped ahead, go back to [page 1](./01-get-started.md) and run one real task. The habit sticks from use, not from reading.

Back to the [guide index](./README.md).
