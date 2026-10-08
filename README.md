# Skills

**Your AI chat, with a method. Paste one sentence, install nothing.**

En français : [le guide](docs/guide-fr-ca/README.md).

Ask an AI chat something vague and you get something generic. Then comes the back-and-forth: you explain, it guesses, you explain again. A skill ends that loop. It's a written method the agent reads and follows step by step, so the first answer is already structured.

I'm Pascal Andy, a business analyst. I've worked at Bell, National Bank, Desjardins, and BDC, so I know the corporate world and the traps worth avoiding. I like to organize things and to get leverage from technology, and skills are the natural next step. I spend my days thinking about how things work today so they work better tomorrow, and I spot the back-and-forth that an agent can take over. My goal is skills that feel almost like magic.

These are the skills I use every day. They work in ChatGPT, Claude, and other chat apps that can open a web page, on your phone or your computer. You never open a terminal.

## Get started

Two steps:

1. Paste this sentence into your chat app:

   ```text
   Read https://raw.githubusercontent.com/pascalandy/skills/main/docs/references/remote-skills-general.md and skip `oem`. When a request of mine matches a skill there, open that skill and follow it.
   ```

2. Ask for something, the way you normally would:

   ```text
   marketing ; write a headline for my bakery in Montreal
   ```

The agent reads the list, opens the marketing mode, picks its copywriting playbook, and follows it. You get headline options, the reason behind each one, and the questions that would sharpen them.

To keep the skills on in every chat, put the sentence in your app's custom instructions or in a project's instructions. The sentence skips `oem` because that skill holds my personal preferences.

New here? **[Start the guide](docs/guide/README.md).** It walks you through a first real task, then shows you how to think, write, market, and present with the skills.

## Three modes do most of the work

A mode is a skill that opens a family of tasks, each with its own playbook. Name the mode, then the task after a semicolon. Or describe the task, and the mode picks the playbook for you.

| Mode | What it's for | Try |
|---|---|---|
| `corey-mode` | Marketing work such as positioning, web pages, emails, and launches, in 50 playbooks by Corey Haines. Any request with the word "marketing" starts it | `marketing ; write the homepage for my accounting firm` |
| `andy-mode` | My thinking and writing tools: challenge an idea, think a decision through, write clearly, tell a story | `andy-mode ; sparring. Remote work hurts junior staff.` |
| `html-mode` | Visual documents: a one-page summary, a diagram, a slide deck | `html-mode ; slides. Turn these notes into a 5-slide pitch.` |

## Skills you call by name

| Skill | Use it when |
|---|---|
| `consensus` | you want the agent to restate your goal and ask the right questions before it starts the work |
| `grilling` | you want a plan or an idea stress-tested through an interview. Say "grill me" |
| `research` | you want a topic researched, with its sources |
| `unslop` | a text sounds like a robot wrote it |
| `concise` | you want shorter answers, in note form |
| `2nd-pass` | you want a fresh-eyes check before you send something |

[`remote-skills-general.md`](docs/references/remote-skills-general.md) lists every skill for non-developers on one page, with each mode's playbooks. A few of them need a computer set up for them, and the guide points those out.

<details>
<summary>More prompts to copy</summary>

```text
consensus:  I want to move my team's weekly report to a shared dashboard. consensus
grilling:   grill me on my plan to open a second location
think:      andy-mode ; think. Should I hire a junior or a senior first?
clarity:    andy-mode ; write-with-clarity. [paste your text]
story:      andy-mode ; storytelling. Help me tell how we lost and won back our biggest client.
cold email: marketing ; write a cold email to restaurant owners about my catering service
pricing:    marketing ; pricing. I charge 80 dollars an hour. Should I sell packages instead?
slides:     html-mode ; slides. Turn this report into a 6-slide summary for my director.
cleanup:    unslop that
```

</details>

## Why a skill beats a prompt

A prompt is one message. A skill is a method someone already tested: the questions to ask first, the steps to follow, and the checks before the answer. You don't retype it, and the agent doesn't improvise it.

## Is it safe?

Every skill is a plain text file on GitHub. Read one before you use it. The agent reads the same file. Nothing gets installed on your phone or your computer.

## For developers

Each skill is maintained in a package at `authoring/<category>/<skill>/` or `authoring/<skill>/` and published in [`skills/`](skills/). Contributors read [`AGENTS.md`](AGENTS.md) before changing the source. [`remote-skills.md`](docs/references/remote-skills.md) lists every skill, and [`remote-skills-dev.md`](docs/references/remote-skills-dev.md) only the coding ones, such as `commit`, `gh-stack`, and `poteto-mode`.

An agent loads a skill when your request matches its `description`. A few descriptions say the skill runs only when you name it, as `$name` in Codex or `/name` in Claude Code.

### Install one skill with the third-party Skills CLI

Replace `<name>` with a folder name from [`skills/`](skills/):

```sh
npx skills add pascalandy/skills --skill <name>
npx skills update
```

The third-party CLI writes to agent skill directories and sends telemetry. Check its prompts and options before using it with your daily agent setup.

### Install one skill with git and a copy

This route needs only git and standard shell tools. Set `skill` to the folder you want and `agent_skills` to your agent's skills directory:

```sh
skill=concise
agent_skills="$HOME/.agents/skills"
destination="$agent_skills/$skill"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  echo "Refusing to overwrite $destination" >&2
else
  checkout=$(mktemp -d)
  git clone --quiet --depth 1 https://github.com/pascalandy/skills.git "$checkout" &&
    mkdir -p "$agent_skills" &&
    cp -R "$checkout/skills/$skill" "$destination"
  rm -rf "$checkout"
fi
```

To update, repeat with a fresh clone after moving or removing your previous copy yourself. The command above refuses to overwrite it.

### Maintainer bulk install

The repository's installer handles multiple agent directories. Preview its work before running it; both commands answer in one JSON line that lists each change, such as `{"ok":true,"changes":[["add","~/.claude/skills/concise"]]}`:

```sh
just install-skills --dry-run
just install-skills
```

Run `just install-skills --help` for the current targets and ownership rules.

## Releases

See [`CHANGELOG.md`](CHANGELOG.md) for version notes and [GitHub Releases](https://github.com/pascalandy/skills/releases) for published snapshots.

## Reuse

[`LICENSE`](LICENSE) covers Pascal's original work under MIT. Shared upstream notices are kept with [`poteto-mode` for PStack](skills/poteto-mode/references/LICENSE), [`matt-mode` for Matt Pocock](skills/matt-mode/references/LICENSE), and [`corey-mode` for Corey Haines](skills/corey-mode/references/LICENSE). The [`gh-stack`](skills/gh-stack/references/LICENSE) notice sits with that skill, and the [`test-audit`](skills/code-review-mode/references/test-audit/LICENSE) and [`architecture-review`](skills/code-review-mode/references/architecture-review/LICENSE) notices sit with their playbooks in `code-review-mode`. See [`html-mode`](skills/html-mode/references/attribution.md), [`grill-for-unknowns`](skills/grill-for-unknowns/LICENSE), and the [`matt-mode` lineage](skills/matt-mode/references/lineage.md) for more provenance. When redistributing an adapted skill alone, include its applicable upstream notice.
