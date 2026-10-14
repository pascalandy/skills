# Brief: one clean workflow for "a feature is requested" and "a bug arrives"

You are one of two independent designers. Another agent, from a different model family, gets this same brief. Do not coordinate. Give your own best answer.

## Who asked

Pascal owns a skill system for coding agents: the public repo at `/home/pascal/projects/.worktrees/skills-docs-debug-mode-design/` (a git worktree of `pascalandy/skills`; source lives under `authoring/<category>/<skill>/`). He read Cindy Sridharan's post "How to effectively debug when you no longer understand the code" (full text: `/tmp/debug-post/post.txt`) and wants its ideas turned into skills.

His original request, verbatim:

> I read that post carefully and there are many things to learn in there. It was so dense that I feel we could create many skills out of it. The first thing it started with was how to do Adversarial Review. There were a lot of principles packed in there, along the full workflow, and all the thinking about finding the root cause and avoiding the traps of getting, I would say, the first answer for the real answer, and managing all hypotheses as a matrix. So there was that.
>
> And then she talked about the software factory: how do you actually build the whole solution so that it is easy to debug. For me, that's another skill. And there's probably more in there.
>
> The two goals that come to mind are, first, when I'm actually building software, each feature or group of features should consider hooks, adding to the verification loop. So each new feature per se should be easy to test and trace back, if I'm trying to say this simply.
>
> The second goal is that the code is already there. It's on prod and we receive a bug, something that is not working as expected. So we should follow the same principle: we gather all this information, the signal from the bug, and then we apply the framework to it.
>
> Think deeply about how to make this entire system as agent-intuitive, agent-ergonomic, and agent-accretive as you can possibly imagine. Put yourself in the driver's seat and imagine that YOU are the one using this system and driving it. [...] Don't just think of the project as an assemblage of various parts or components: really try to profoundly and deeply conceptualize it as a synthetic SYSTEM that is maximally coherent, cohesive, modular, and interconnected, forming a tower of linked abstractions that are maximally legible to you as an agent.

His standing preferences: simple systems, the smallest model that makes correct behavior unsurprising, YAGNI, DRY, prevent drift, no machinery for its own sake.

## What has already been decided with Pascal

A first design exists at `docs/ideas/references/2026-10-13-debug-mode/design.md` in the worktree. It proposed one new mode, `debug-mode`, with routes `diagnose` and `instrument`. Pascal rejected that shape: he will not call a "debug" skill while building a feature, and the team would not understand it. Its method content (principles, vocabulary, case file, the diagnose steps, the reviewer rules) still stands. The decisions below override it.

1. **One new skill: `diagnose`.** It runs when a bug arrives: facts before code, a working case to compare against, hypotheses in a matrix, elimination by facts, a fix proven by the reading that exposed the bug returning to normal. No `debug-mode`, no `instrument` route
2. **`interrogate` owns adversarial review** (`authoring/poteto/interrogate/`). It takes the post's rules: a reviewer can eliminate a claim but never confirm one, reviewers get facts rather than the author's story, agreement between reviewers is not proof, a clean report says what was checked. `diagnose` calls it to knock out wrong causes, with one reviewer from another model family
3. **Brigade barrages call `interrogate`.** Brigade (`authoring/andy-devtools/brigade-mode/playbooks/arancini/`) is Pascal's multi-thread build workflow: a Chef thread launches a Cook thread that implements a card with poteto-mode, then review threads called barrages (manic-1 overkill check, manic-2 blast radius and premortem, manic-3 docs review, manic-5 polish), then the Chef merges and asks threads for two retros. The barrage step stays, but manic-1, 2, and 5 now call `interrogate` with their angle instead of hard-coded review instructions, with `reviewers = 2` (one Claude, one Codex) set per barrage in `config.toml`. manic-3 stays on `technical-writing`
4. **The verify loop is each project's `verify-<app>` skill.** It drives the real app and proves behavior, with one feature file per feature. `create-verification-skill` creates it. The agent offers creation the first time a project needs one; a line in the project's `AGENTS.md` ("no verify loop, CI is enough") stops the offer for documentation projects. `maintain-verification-skill` keeps it up to date, and gains an "add a feature" pass: choose the readings the feature records and their normal values, write the feature file, and show a check that fails before the change (a planted bug for a feature; the bug itself for a fix). The Cook writes the product code that records the readings
5. **Checks after implementing: CI first, then the verify loop.** CI (`just check`) runs first because it is cheap. Then the verify loop runs in a delegate agent: a T3 Code child task the calling thread starts with `delegate_task` and tracks by `taskId`. It starts from a fresh context and compares readings with the last good run
6. **Lessons go back through the retros.** `andy-mode ; retro-skill-usage` and `andy-mode ; retro-global` (`authoring/andy/andy-mode/playbooks/`). `retro-global` gains a category that asks what would make the verify loop stronger. Retros file issues; they never edit directly
7. **Connections already identified.** A confirmed cause hands its strongest reading to the build path, where it becomes a verify-loop check that fails before the fix. A verify-loop failure whose cause is unclear turns the build into a diagnosis
8. Remote reads on Pascal's machines go through his `fleet` skill. Evals run on both Claude and Codex

## The diagram Pascal rejected

Source: `/tmp/debug-workflow/workflow-v3-rejected.mmd`. Image: `/tmp/debug-workflow/workflow-v3-rejected.png`. Read both.

His critique, verbatim:

> Something is off with the diagram. I don't understand why sometimes we use the maintain-verify skill to update the loop, and sometimes we update the loop directly. So what's confusing here is that the verification loop appears in many places, and this is not clean to me. I don't like that at all. I should see a clear connection between the two use cases, which are a feature request or a bug arriving. Then connect the two well together, without ever duplicating maintain-verify-loop and verify-loop.

## Your task

Design the workflow that connects "a feature is requested" and "a bug arrives" into one coherent system, in which the verify loop and its maintenance each have one clear place and one clear meaning. Ground every claim in the files: read the skills you name before naming them.

Read at least: the rejected diagram, the post sections on the three-step debugging loop and on adversarial review, `design.md` (method content), `authoring/poteto/maintain-verification-skill/SKILL.md`, `authoring/poteto/create-verification-skill/SKILL.md`, one real loop under `authoring/verify-loops/`, `authoring/poteto/interrogate/SKILL.md`, `authoring/poteto/poteto-mode/playbooks/feature.md` and `bug-fix.md`, brigade's `arancini.md` and `sop/`, and `retro-global.md`.

Deliver, in this order, under 250 lines:

1. **Why the rejected diagram confuses**, in three sentences at most
2. **The workflow** as Mermaid `flowchart` source, readable at a glance by someone who never saw the earlier versions. Each skill appears once. State in one line what each node reads and writes
3. **The connection between the two use cases**: where they merge, where they split, and why the line falls there
4. **What you would change in the decisions above**, if anything, each with the evidence from the files. Changing nothing is a valid answer
5. **At most three questions** only Pascal can answer

Write the result to `/tmp/debug-workflow/proposal-<your-model-family>.md` (for example `proposal-codex.md` or `proposal-claude.md`), with the Mermaid source also saved as `/tmp/debug-workflow/proposal-<your-model-family>.mmd`. Return the full proposal in your final message too. Do not read any other `proposal-*` file. Do not edit anything else: no repo edits, no commits.
