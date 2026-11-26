---
name: "web-research"
description: "Use for any web research, web scout, or delegated research agents: « délègue une recherche », « délègue un scout », « fais une recherche », « THEN ; Research », or a named web tool such as « avec Tavily », « avec Firecrawl », « avec Exa », including dictated spellings like « ta vidéo », « Tavilly », « fire crawl », « exact » or « exa ». Not for reading local files or the codebase."
kind: "general"
configuration-is-needed: true
---

Delegate each web task through a 4-level ladder, starting at the level the task needs and climbing only when a result falls short. When `$tool-call-delegation` is also active in the thread, `$web-research` owns all public web scouts; keep local shell, file, and git operations on `$tool-call-delegation`.

## Steps

```
Web research progress:
- [ ] Step 1: Starting level chosen
- [ ] Step 2: Route confirmed
- [ ] Step 3: Delegate briefed
- [ ] Step 4: Result checked
- [ ] Step 5: Climbed or done
```

**Step 1: Starting level chosen.** When the request names a tool, start at that tool's level (see [Named tool](#named-tool)). Otherwise pick by depth, defaulting to Level 1 for general web searches:

| Task | Start at |
|---|---|
| Quick fact, general web search, or official docs lookup | Level 1 |
| Structured multi-URL extraction or site map | Level 2 |
| Read, extract, or crawl a blocked or JS-rendered page or site | Level 3 |
| Semantic discovery ("find things like X") or deep research | Level 4 |

Done when one level is chosen.

**Step 2: Route confirmed.** In T3 Code, load `$t3-runtime`. Reuse an earlier `orchestrator_capabilities` answer that lists the level's model. Otherwise call it, with `search` set to that model when the short list omits it, and note the provider instance that lists it and can run a child task. A model missing from both answers has no route. When the Codex route is missing, confirm the Haiku route instead (see [The ladder](#the-ladder)). Done when the route exists; no route counts as a failed attempt in Step 5. When you cannot delegate, go to [Run the levels yourself](#run-the-levels-yourself).

**Step 3: Delegate briefed.** Delegate to the level's agent from [The ladder](#the-ladder) with this brief, filled in. For multiple independent web subtasks, launch parallel delegates on that same ladder model (Codex Terra high at levels 1 to 3) rather than spreading web scouts across unrelated models or `$tool-call-delegation` candidates:

```
Web task, collect facts only. Do not delegate. Do not analyze.
Tool: <level tool>. Do not use any other web tool.
Task: <one page or one topic>.
Return: each raw fact with its source URL; the exact tools or commands called, in order; any error, block, or empty result, word for word.
If the required tool fails, stop and report the failure. Do not switch tools.
```

Done when each delegate is running with one page or one topic.

**Step 4: Result checked.** When a delegate returns:

1. Check the returned provider, model, and options match the level
2. Read the child thread with `t3_thread_read` and `view: "activity"` (or the `acp-mcp-call t3_thread_read` shell fallback when a harness hides `t3_thread_read` from direct tools). Confirm the real tool calls used the level's tool; the summary alone is not proof
3. Check every fact carries a source URL
4. Record one check line per scout (`<scout> -> <model> -> <tool observed in activity>`) before citing its facts

Done when each check passes or you name the one that failed. A failed check counts as a failed attempt in Step 5.

**Step 5: Climbed or done.** When an attempt is blocked, empty, without sources, too thin for the question, or failed a Step 4 check, go up one level and return to Step 2. At level 1, when Terra made the failed attempt, run the Haiku attempt from [The ladder](#the-ladder) once, through Steps 2 to 4, before level 2. At level 4, report its error, or the shortfall when no error came back. On a [named tool](#named-tool), report and stop instead. Done when the facts answer the question, or you report the failure.

## The ladder

1. Codex Terra high with its native web tools. When Terra's attempt fails (Step 5), try Haiku high with its native web tools (WebSearch, WebFetch) before level 2
2. Codex Terra high with `$tavily`
3. Codex Terra high with `$firecrawl`
4. Pi Terra with the `exa` extension (`exa_search`, `exa_fetch`, `exa_answer`)

Each level names the aliases `terra` and `haiku`. Read `fleet/references/active-models.toml` and resolve each one: its `id` for Codex and Claude, and for Pi Terra its Pi ID on this machine. Without the fleet skill, take the newest Terra or Haiku that `orchestrator_capabilities` lists.

- **Codex delegation**: `delegate_task` with the Codex provider instance from Step 2, the Terra ID, and `target.options` `reasoningEffort: "high"` and `serviceTier: "default"`
- **Haiku delegation**: `delegate_task` with the Claude provider instance from Step 2, the Haiku ID, and `target.options.effort: "high"`
- **Pi delegation**: `delegate_task` with `target.providerInstanceId: "pi"`, the Pi Terra ID, and `target.options.thinking: "high"`
- **Codex unavailable** (provider off, usage limit reached, or delegation fails): use Haiku high at the same level, with that level's tool
- **Level 4 has no fallback** (see Step 5)

## Named tool

Tavily is level 2, Firecrawl level 3, Exa level 4. Start at the named tool's level directly. When it fails or falls short, report the exact error, or the shortfall when no error came back, name the next level when one exists, and stop. Climb only when the user says so. A Haiku swap at the same level keeps the named tool and is not a climb.

## Run the levels yourself

Do not use web tools yourself while you can delegate. When you cannot delegate, because you are a delegated agent, in a headless run, or outside T3 Code, run the current level yourself with its level's tool. Check the tool you actually used and each fact's source URL; a level whose tool is unavailable counts as a failed attempt. Then apply Step 5, including its named-tool stop, but skip the level 1 Haiku attempt; when it climbs, run the next level the same way.

## Known limits

- Terra's native web tool cannot read npm hosts: `www.npmjs.com` returns 403 and `registry.npmjs.org` refuses it (checked with Terra 6.1 on 2026-11-19). For a fact on an npm host, start level 1 with Haiku, which reads `registry.npmjs.org`
