# Words

These entries explain STE_01–STE_06 for software text. Each Before example shows wording to change.

## STE_01 One name per thing

Use the name that the repository or user gives each thing. Repeat that name and the same wording for the same action.
Permits: Different things can have different names. A different action can need different wording.
Rules: 1.8, 1.11, 6.2, 9.4.
Before: "The retry queue holds failed jobs. The backlog keeps jobs for an hour."
After: If the glossary says the backlog is the retry queue: "The retry queue holds failed jobs. The retry queue keeps jobs for an hour."
Edge cases:
- Keep the exact spelling of code symbols, paths, commands, and interface labels.
- One label for two states is a finding, such as one status icon that means both waiting for review and not merged.

## STE_02 New terms explained at first use

Explain an unfamiliar term where the reader first meets it. Use the project glossary to connect the term to its meaning.
Permits: An established software term can remain when it names a real concept. A familiar term needs no extra explanation.
Rules: 2.2.
Issue 9 asks to explain long technical names. This skill explains every unfamiliar term, as a software adaptation.
Before: "The scheduler checks the lease before each job."
After: If the glossary defines the lease: "The lease grants one worker temporary control of a job. The scheduler checks the lease before each job."
Edge case: Explain an acronym before later uses of that acronym.

## STE_03 Plain words, one meaning each

Choose a familiar English word for general prose. Keep specialized words for the actual software concept that needs them.
Permits: The same spelling can have distinct valid meanings in separate contexts. A precise software verb can be clearer than a general verb.
Rules: 1.1, 1.3, 1.5, 1.6, 1.10, 1.12, 9.2, GR-5, GR-6.
Before: "Actualize the issue's estimate."
After: "Update the issue's estimate."
Edge cases:
- A false friend resembles a word in another language but has a different English meaning. Check the English meaning.
- Expand Latin abbreviations into English, or remove them when they add nothing.
- Keep an exact project term. Explain the term instead of replacing it with team slang.

## STE_04 Each word keeps its role

Use a noun to name a thing and a verb to describe an action. Keep normal verb endings and adjective forms.
Permits: One spelling can serve both roles when each role independently fits the context. A verb form can describe a state, as in "archived record".
Rules: 1.2, 1.4, 1.7, 1.13.
Before: "PR the fix after the verify."
After: "Verify the fix. Then open a pull request for the fix."
Edge case: A technical noun does not become a verb merely because the team uses it as one.

## STE_05 Short noun groups

Keep a noun group that you create to three words or fewer. Explain a longer official name in full, then preserve its exact form.
Permits: A short form defined at first use can replace the full name after that point, such as "Issue 9" for the full title of the standard. The short form then becomes the one name under STE_01.
Rules: 1.9, 2.1, 2.2, 8.2.
Before: "Change the background task retry delay setting."
After: "Change the setting for the delay between retries of background tasks."
Edge cases:
- A preposition such as "for" can separate a long group into shorter groups.
- A hyphen can join words that form one unit. Preserve established project spelling.
- Extra hyphens do not make unrelated words a valid term.

## STE_06 One referent per pronoun

A referent is the thing that a pronoun points to. Repeat the noun when a pronoun or shortened reference could point to two things.
Permits: A pronoun can remain when its referent is clear. General plurals and abstract qualities can omit articles. A noun followed by an identifier can omit "the", as in "field B2".
Rules: 4.5, GR-3, GR-4.
Before: "The client sends the token to the server. It checks the expiry date."
After: If the design says the server checks it: "The client sends the token to the server. The server checks the expiry date."
Edge cases:
- Issue 9 permits a clear "this" reference. This checklist always puts a noun after "this".
- "The skill" is unclear when the text names two skills. Use the skill's name.
- When the source does not show the referent, report an open question instead of choosing one.
