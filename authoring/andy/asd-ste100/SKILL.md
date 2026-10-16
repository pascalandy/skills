---
name: "asd-ste100"
description: "Use when writing, rewriting, or reviewing an English spec, GitHub issue, or idea with ASD-STE100 Simplified Technical English (STE), or when a request cites an `STE_NN` checklist ID."
kind: "general"
---

# ASD-STE100

Make an English spec, GitHub issue, or idea readable in one pass by a person or an agent.
Use the writing rules of Issue 9, adapted to software work.
The checklist guides writing and sets the acceptance criteria for a review.

## Terms

- **Target text**: the English spec, GitHub issue, or idea that you write or review
- **Item**: one checklist entry with a fixed `STE_NN` identifier
- **Issue 9**: the January 2025 edition of ASD-STE100 Simplified Technical English
- **Project glossary**: the project's names and their plain meanings. See [words](references/words.md)
- **Step**: one marked unit in an ordered set of instructions. See [structure](references/structure.md)
- **Instruction**: a sentence that directs the reader to act. See [structure](references/structure.md)
- **Descriptive sentence**: a sentence that explains a fact or behavior. See [sentences](references/sentences.md)
- **Note**: extra information that the reader can skip. See [structure](references/structure.md)
- **Risk note**: a labeled message that states a safe action or condition and the harm if the reader ignores the precaution. See [structure](references/structure.md)
- **Noun group**: words that together name one thing. See [words](references/words.md)
- **Word count**: a sentence's length under the conventions in [sentences](references/sentences.md)

## Pick the branch

Choose the branch that matches the request:

- Write or rewrite: follow **Write**
- Review: follow **Review**
- Fix named items, such as `fix STE_06`: apply those items to the specified lines. Then report through Review step 3

## Write

Copy the checklist below to track the applicable items.

1. Collect the project glossary from the repository, request, and user.
   Done when each thing named in the target text has one name.
2. Sort the content into descriptive text, steps, and risk notes.
   Done when each block belongs to one of these three types.
3. Draft or rewrite the target text against the checklist.
   For a rewrite, change the wording only.
   Preserve every source detail, including:

   - Facts
   - Numbers
   - Conditions
   - Actors
   - Scope limits
   - Open questions

   Done when the draft preserves the source meaning and covers every applicable item.
4. Run the Review branch on the draft.
   Fix each finding and repeat the review.
   Done when a pass finds nothing new and each kept finding has a reason stated in the reply.
5. Reply with the target text, followed by `STE: Pass: <IDs>`.
   Include each kept finding and its reason.
   Done when the reply contains the text, the result, and any kept findings.

## Review

1. Mark descriptive text, steps, and risk notes in the target text.
   Use the applicability table below. Done when each block has a type.
2. Check each applicable item.
   If an item's condition is unclear for a sentence, read that item's reference entry.
   Done when each item has findings, passes, or does not apply.
3. Report findings by item, with a count for each item.
   Give each finding's location and proposed fix.
   Then give a `Pass:` line for checked items without findings, including items marked `n/a`.
   End with the fixed scope line shown below.
   Done when every checked item has a result and the report states its scope.

Example report for descriptive text:

```text
STE_06 One referent per pronoun: 1
- issue.md:12 "It retries failed jobs." Fix: "The scheduler retries failed jobs."
Pass: STE_01–STE_05, STE_07–STE_13, STE_14–STE_17 (n/a)
Scope: Issue 9 writing rules, adapted to software. Dictionary not checked.
```

## Applicability

Use each item for the text types in this table:

| Items | Text types |
|---|---|
| STE_01–STE_13 | All text |
| STE_14–STE_16 | Steps |
| STE_17 | A step that carries a risk |

In the Pass line, mark an item that does not apply as `n/a`.

## Priority

When time is short, check STE_01, STE_07, STE_15, STE_02, STE_06, and STE_12 first. Most extra review rounds come from one label with two meanings, a missing actor, a missing condition, or an unexplained name. Long sentences are common but rarely the cause, so treat STE_11 as a target.

## Checklist

### Words

- [ ] **STE_01 One name per thing**: Each thing and action keeps its real project name or the user's term throughout the target text. _(Issue 9: 1.8, 1.11, 6.2, 9.4)_
- [ ] **STE_02 New terms explained at first use**: Each unfamiliar name, acronym, or project term has a plain explanation at first use. _(Issue 9: 1.6, 1.10, 2.2)_
- [ ] **STE_03 Plain words, one meaning each**: General prose uses everyday words in their usual senses. Specialized words name real software concepts. Replace team slang, Latin abbreviations, and words mistaken for similar words in another language. _(Issue 9: 1.1, 1.3, 1.5, 1.12, 9.2, GR-5, GR-6)_
- [ ] **STE_04 Each word keeps its role**: Nouns stay nouns and verbs stay verbs. Use ordinary word forms. _(Issue 9: 1.2, 1.4, 1.7, 1.13)_
- [ ] **STE_05 Short noun groups**: A noun group that the writer creates has at most three words. A longer official name appears in full with an explanation at first use. Later uses keep that exact name, or a short form defined at first use. _(Issue 9: 1.9, 2.1, 2.2, 8.2)_
- [ ] **STE_06 One referent per pronoun**: Each pronoun or shortened reference, such as "the skill", points to one thing. A noun follows "this". _(Issue 9: 4.5, GR-3, GR-4)_

### Sentences

- [ ] **STE_07 The actor is named**: A sentence about an action names the actor. Descriptive text permits passive voice when the actor is unknown or does not matter. _(Issue 9: 3.6)_
- [ ] **STE_08 Actions in simple verbs**: An action uses a verb in a simple tense. Replace a verb phrase when one verb says the same thing. Rewrite an ambiguous "-ing" form. _(Issue 9: 3.2, 3.3, 3.4, 3.5, 3.7, 9.3)_
- [ ] **STE_09 One idea per complete sentence**: Each sentence keeps one idea and its needed words, including articles and "that". Spell out contractions. Use complete prose instead of arrows, slashes, semicolons, or missing words. _(Issue 9: 4.1, 4.2, 4.5, 8.1, 9.1, GR-1, GR-2)_
- [ ] **STE_10 Linked sentences**: A sentence that continues, explains, or contrasts the preceding sentence states that link with a connecting word. _(Issue 9: 4.4, 6.2)_
- [ ] **STE_11 Length within target**: An instruction has at most 20 words. A descriptive sentence has at most 25. A longer sentence has a stated reason. _(Issue 9: 5.1, 6.3, 8.4, 8.5, 8.6, 8.7)_

### Structure

- [ ] **STE_12 Point first**: Each section and paragraph opens with its problem, answer, or decision, then gives the details. Each paragraph covers one topic. _(Issue 9: 6.1, 6.4, 6.5, 6.6)_
- [ ] **STE_13 Lists for complex text**: Three or more parallel items, or dependent actions, form a vertical list after a sentence that introduces them. List items use parallel forms. A list separates facts from instructions. _(Issue 9: 4.3)_
- [ ] **STE_14 One instruction per step**: Each step starts with a command verb and gives one action. Sequential actions have separate steps. Simultaneous actions may share a step. _(Issue 9: 5.2, 5.3)_
- [ ] **STE_15 Condition before command**: A condition, prerequisite, or purpose precedes the command that it governs. _(Issue 9: 5.4)_
- [ ] **STE_16 Notes hold no instructions**: A note contains information only. Steps or risk notes hold actions, requirements, and risks. The steps work without the notes. _(Issue 9: 5.5)_
- [ ] **STE_17 Risk note before the risky step**: Before a risky step, a risk note gives a label, a safe action or condition, and the consequence. Risks include data loss, production failure, secret exposure, and irreversible changes. _(Issue 9: 7.1, 7.2, 7.3)_

IDs never change and are never reused. To change an item, move its line under `### Voided` with `void <date>, replaced by STE_NN`, and give the new item the next free ID.

## References

Read the file for an item's details when its condition is unclear:

- [Words](references/words.md): STE_01–STE_06, with permitted cases and examples
- [Sentences](references/sentences.md): STE_07–STE_11, with permitted cases, examples, and word count conventions
- [Structure](references/structure.md): STE_12–STE_17, with permitted cases and examples
- [Coverage](references/coverage.md): read when tracing a rule number to an item or checking a rule left out

## Limits and source

This skill checks writing rules only. It ships no dictionary, so a review never declares a target text STE compliant. Use the fixed scope line in Review.

The person who publishes the target text remains accountable for its facts and risk notes.

This independent skill refers by rule number to ASD-STE100 Simplified Technical English, Issue 9, January 2025.
The name ASD-STE100 Simplified Technical English is a registered trademark of ASD in the European Union.
This skill has no affiliation with or endorsement from ASD or STEMG, the group that maintains the standard.
Get the official text free from the [ASD-STE100 website](https://www.asd-ste100.org).
