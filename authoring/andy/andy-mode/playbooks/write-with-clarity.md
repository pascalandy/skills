---
description: "Edit prose for clarity and concision, following Strunk's rules and removing AI writing patterns."
---

# Writing Clearly and Concisely

## Overview

Write with clarity and force. This skill covers what to do (Strunk) and what not to do (AI patterns).

## When to Use This Skill

Use this skill whenever you write prose for humans:

- Documentation, README files, technical explanations
- Error messages, UI copy, help text, comments
- Reports, summaries, or any explanation
- Editing to improve clarity

**If you're writing sentences for a human to read, use this skill.**

## Limited Context Strategy

When context is tight:

1. Write your draft using judgment
2. Dispatch a subagent with your draft and the relevant section file
3. Have the subagent copyedit and return the revision

Loading a single section (~1,000-4,500 tokens) instead of everything saves significant context.

## Elements of Style

William Strunk Jr.'s *The Elements of Style* (1918) teaches you to write clearly and cut ruthlessly.

### Rules

**Elementary Rules of Usage (Grammar/Punctuation)**:

1. Form possessive singular by adding 's
2. Use comma after each term in series except last
3. Enclose parenthetic expressions between commas
4. Comma before conjunction introducing co-ordinate clause
5. Don't join independent clauses by comma
6. Don't break sentences in two
7. Participial phrase at beginning refers to grammatical subject

**Elementary Principles of Composition**:

8. One paragraph per topic
9. Begin paragraph with topic sentence
10. **Use active voice**
11. **Put statements in positive form**
12. **Use definite, specific, concrete language**
13. **Omit needless words**
14. Avoid succession of loose sentences
15. Express co-ordinate ideas in similar form
16. **Keep related words together**
17. Keep to one tense in summaries
18. **Place emphatic words at end of sentence**

## Reference map

Load only what you need.

- **Default for most tasks:** `references/write-with-clarity/03-elementary-principles-of-composition.md`
  - Best for active voice, positive form, concrete language, concision, and sentence flow.
- **Grammar and punctuation:** `references/write-with-clarity/02-elementary-rules-of-usage.md`
- **Headings, quotations, and form:** `references/write-with-clarity/04-a-few-matters-of-form.md`
- **Word choice and common misuses:** `references/write-with-clarity/05-words-and-expressions-commonly-misused.md`
- **Diagnosing synthetic or overly generic prose:** `references/write-with-clarity/signs-of-ai-writing.md`

Use `references/write-with-clarity/signs-of-ai-writing.md` to spot patterns, not to enforce a mechanical ban list.

## AI Writing Patterns to Avoid

LLMs regress to statistical means, producing generic, puffy prose. Avoid:

- **Puffery:** pivotal, crucial, vital, testament, enduring legacy
- **Empty "-ing" phrases:** ensuring reliability, showcasing features, highlighting capabilities
- **Promotional adjectives:** groundbreaking, seamless, robust, cutting-edge
- **Overused AI vocabulary:** delve, leverage, multifaceted, foster, realm, tapestry
- **Formatting overuse:** excessive bullets, emoji decorations, bold on every other word

Be specific, not grandiose. Say what it actually does.

## Bottom Line

Writing for humans? Load the relevant section from `references/write-with-clarity/` and apply the rules. For most tasks, `references/write-with-clarity/03-elementary-principles-of-composition.md` covers what matters most.

## Guardrails

- Do **not** change facts, requirements, or technical meaning.
- Do **not** simplify away important nuance.
- Do **not** make specialized writing vague just to make it shorter.
- Do **not** inject marketing tone unless the user wants it.
- Do **not** flatten the author's voice into generic corporate prose.
- Do **not** explain every edit unless the user asks.
