# Sentences

These entries explain STE_07–STE_11 for software text. Each Before example shows wording to change.

## STE_07 The actor is named

Make the actor the subject of an action sentence. In a command, the reader is the actor even when "you" is implicit.
Permits: Issue 9 permits descriptive passive voice when the actor is unknown. This software adaptation also permits it when the actor does not matter.
Rules: 3.6.
Before: "The settings are loaded by the worker."
After: "The worker loads the settings."
Edge case: "The backup was deleted" can remain if the evidence does not identify who deleted it.

## STE_08 Actions in simple verbs

Name the action with a verb and keep its tense simple. A phrasal verb combines a verb with another short word, sometimes with an idiomatic meaning.
Permits: Issue 9 allows commands, infinitives, and simple present, past, and future forms. A past participle can describe a state.
Issue 9 limits -ing forms to technical names and a few modifier uses. This skill rewrites an -ing form only when it reads two ways, and keeps technical names.
Rules: 3.2, 3.3, 3.4, 3.5, 3.7, 9.3.
Before: "The worker will carry out validation of the payload."
After: "The worker will validate the payload."
Edge cases:
- Keep "can" for active capability and "will" for future actions. Preserve the source's time and certainty.
- Keep a real name such as "connection pooling". Rewrite an "-ing" form when its meaning is unclear.
- Issue 9 permits listed phrasal verbs. This skill has no such list, so prefer an equally precise single verb.

## STE_09 One idea per complete sentence

Give each sentence one complete idea. When a word replacement damages grammar or meaning, rebuild the sentence around the same facts. Use words instead of arrows or slashes for prose relationships.
Permits: General plurals and abstract qualities need no article. "That" can be absent when the sentence remains clear. Literal code keeps its required punctuation.
Rules: 4.1, 4.2, 4.5, 6.1, 8.1, 9.1, GR-1, GR-2.
Before: "Worker reads cache / worker doesn't retry."
After: "The worker reads the cache. The worker does not retry."
Edge cases:
- A command can omit "you". A list can use fragments that fit its introductory sentence.
- A table cell can be a fragment that fits its column header. A line that opens with a fixed label, such as "Done when", can be a fragment that completes that label.
- Repeat "the" when one shared article could make two things look like one.
- "With" can name a tool, companion, or relationship. If two readings fit, name the relationship explicitly.

## STE_10 Linked sentences

Show how a sentence relates to the preceding sentence. Use a connecting word that states the actual sequence, cause, or contrast.
Permits: A clear repeated term or a demonstrative with its noun can connect sentences. An unrelated new topic needs no invented link.
Rules: 4.4, 6.2.
Before: "The worker reads the cache first. The worker reads the database next."
After: "The worker reads the cache first. Then the worker reads the database."
Edge case: A rewrite keeps the source's causal claims. A connector must not invent a cause.

## STE_11 Sentence length limits

Give each sentence the limit of the block that holds it. If a sentence exceeds its limit and carries two ideas, split it while keeping its full meaning.
Permits: Issue 9 sets hard limits. This skill splits a long sentence that carries two ideas and reports the rest as a count.
Rules: 5.1, 6.3, 8.4, 8.5, 8.6, 8.7.
Before: "The worker writes each accepted event to the database before it sends a receipt to the client that submitted the event for processing through the public endpoint."
After: "The worker writes each accepted event to the database. Then the worker sends a receipt to the client that submitted the event for processing through the public endpoint."
Edge cases:
- Each instruction and each sentence in a step has a 20-word limit, such as a sentence that states the expected result. Descriptive text and notes have a 25-word limit.
- Count every sentence of a risk note as an instruction.

## Word count conventions

Count ordinary prose words separately, with these exceptions:

- Count a number as one word
- Count a number with its unit as one word
- Count an abbreviation as one word
- Count an identifier as one word
- Count a hyphenated word as one word
- Count a quoted string as one word
- Count a title, heading, or label as one word
- Count a proper name as one word
- Count an inline code span as one word if it contains one literal symbol, path, identifier, or complete command

Prose in code font still counts as prose. For example, `pnpm run lint` is one word because it is a complete command.

A list's introductory text before its colon is one sentence. Each list item is its own sentence under the limit of its block.
A group in parentheses counts as one word in the outer sentence. Check the group's contents as a separate sentence too.
List markers and step numbers add no words to the sentence.
