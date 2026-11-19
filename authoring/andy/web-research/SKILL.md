---
name: "web-research"
description: "Use for any web research or web scout: « délègue une recherche », « délègue un scout », « fais une recherche », or a named web tool such as « avec Tavily », « avec Firecrawl », « avec Exa », including dictated spellings like « ta vidéo », « Tavilly », « fire crawl », « exact » or « exa ». Not for reading local files or the codebase."
kind: "general"
---

Delegate each web task through a 4-level ladder, starting at the level the task needs and climbing only when a result falls short.

## Steps

```
Web research progress:
- [ ] Step 1: Routes confirmed
- [ ] Step 2: Starting level chosen
- [ ] Step 3: Delegate briefed
- [ ] Step 4: Result checked
- [ ] Step 5: Climbed or done
```

**Step 1: Routes confirmed.** In T3 Code, call `orchestrator_capabilities` once and confirm the Codex models and the Pi Terra route. Done when you know which routes exist. When you cannot delegate, go to [Run the levels yourself](#run-the-levels-yourself).

**Step 2: Starting level chosen.** When the request names a tool, start at that tool's level (see [Named tool](#named-tool)). Otherwise pick by depth:

| Task | Start at |
|---|---|
| A quick fact | Level 1 |
| A search that needs official sources or several results | Level 2 |
| Read, extract, or crawl a known page or site | Level 3 |
| Semantic discovery ("find things like X") or deep research | Level 4 |

Done when one level is chosen.

**Step 3: Delegate briefed.** Delegate to the level's agent from [The ladder](#the-ladder) with this brief, filled in:

```
Web task, collect facts only. Do not delegate. Do not analyze.
Tool: <level tool>. Do not use any other web tool.
Task: <one page or one topic>.
Return: each raw fact with its source URL; the exact tools or commands called, in order; any error, block, or empty result, word for word.
If the required tool fails, stop and report the failure. Do not switch tools.
```

Done when the delegate is running with one page or one topic.

**Step 4: Result checked.** When the delegate returns:

1. Check the returned provider, model, and options match the level
2. Read the child thread with `t3_thread_read` and `view: "activity"`. Confirm the real tool calls used the level's tool; the summary alone is not proof
3. Check every fact carries a source URL

Done when each check passes or you name the one that failed.

**Step 5: Climbed or done.** When the result is blocked, empty, without sources, or too thin for the question, go up one level and return to Step 3. Done when the facts answer the question, or level 4 fails and you report its error.

## The ladder

1. Codex Luna high (`gpt-6-luna`) with its native web tools. When Luna is blocked, returns no result, or returns facts without sources, try Haiku 5.5 high with its native web tools (WebSearch, WebFetch) before level 2
2. Codex Terra high (`gpt-6.1-terra`) with `$tavily`
3. Codex Terra high (`gpt-6.1-terra`) with `$firecrawl`
4. Pi Terra with the `exa` extension (`exa_search`, `exa_fetch`, `exa_answer`). Take the model ID for "Pi Terra" from the Pi delegation list in `$oem` "## Tools and utilities"; the Mini uses different IDs

- **Codex delegation**: `delegate_task` with `target.options` `reasoningEffort: "high"` and `serviceTier: "default"`
- **Pi delegation**: `delegate_task` with `target.providerInstanceId: "pi"`, the Pi Terra model, and `target.options.thinking: "high"`
- **Codex unavailable** (provider off, usage limit reached, or delegation fails): use Haiku 5.5 high at the same level, with that level's tool
- **Level 4 has no fallback**: report the error

## Named tool

Tavily is level 2, Firecrawl level 3, Exa level 4. Start at the named tool's level directly. When it fails, report the exact error and name the next level; do not switch tools silently.

## Run the levels yourself

Do not use web tools yourself while you can delegate. When you cannot delegate, because you are a delegated agent, in a headless run, or outside T3 Code, run the levels yourself in order, each with its level's tool, and apply the checks of Step 4 to your own results.

## Known limits

- Luna's native web tool cannot read npm hosts: `www.npmjs.com` returns 403 and `registry.npmjs.org` refuses it. Haiku reads `registry.npmjs.org`
- Firecrawl was the most precise page reader in tests
