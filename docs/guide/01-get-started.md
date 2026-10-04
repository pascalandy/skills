# Paste one sentence and run your first skill

In this page you paste one sentence into your chat app, run a first skill, and keep the skills on for every chat. Setup takes about a minute.

## Paste the sentence

Open a new chat and paste this sentence:

```text
Read https://raw.githubusercontent.com/pascalandy/skills/main/docs/references/remote-skills-general.md and skip `oem`. When a request of mine matches a skill there, open that skill and follow it.
```

The agent opens the page. It lists every skill for non-developers, with one line about each. The agent may answer with a short summary of what it found.

The sentence skips `oem` because that skill holds my personal preferences. Without the skip, your agent would start treating you as me.

## Run your first skill

In the same chat, type a real request. Swap in your own business:

```text
marketing ; write a headline for my bakery in Montreal
```

Watch what happens. The word "marketing" opens `corey-mode`, my marketing mode. The mode reads the rest of your request and picks the playbook that fits, here `copywriting`. The agent opens that playbook and follows it. Some agents start the reply with a line such as `Route: copywriting`, which names the playbook they followed.

You get headline options, the reason behind each one, and questions such as "What's your signature item?" Answer them. The next round fits your bakery instead of any bakery.

## Keep the skills on in every chat

Pasting the sentence in each chat gets old. Put it where your app reads it every time:

- In your app's custom instructions, so every chat uses the skills
- In a project's instructions, so only the chats in that project use them

Then start a new chat and type a request. You no longer need the sentence.

## If your app can't open the page

Some apps, or some plans, can't open web pages. Others refuse a link that the agent builds by itself. You can tell when the agent answers from memory, says it can't browse, or names a skill that isn't on the list.

To fix it, try these in order:

1. Turn on web search or browsing in your app, then paste the sentence again.
2. Try the same sentence in another chat app.
3. Open the skill yourself. Every skill lives in the [`skills/` folder on GitHub](https://github.com/pascalandy/skills/tree/main/skills). Open the skill's `SKILL.md`, copy its text, and paste it into the chat after the words "Follow these instructions". For a route, copy the route's playbook from the mode's `playbooks/` folder instead. This works in every app.

**Pitfall:** don't trust an answer that never names a skill. Ask the agent "Which skill did you open, and what is its first step?" An agent that read the skill can answer. An agent that guessed can't.

Next: [Name a mode, then the task](./02-modes.md).
