# Structure

These entries explain STE_12–STE_17 for software text. Each Before example shows wording to change.

## STE_12 Point first

Open each section and paragraph with its problem, answer, or decision. Add details about that one topic in an order the reader can follow.
Permits: Issue 9 sets no fixed pace for new information. A paragraph can contain up to six sentences.
Rules: 6.1, 6.4, 6.5, 6.6.
Before: "Users can open the history page. Each page requests all records. Large accounts exhaust the server's memory."
After: "The history page exhausts the server's memory for large accounts. Users can open the history page. Each page requests all records."
Edge case: Start a new paragraph when the topic changes, even before six sentences.

## STE_13 Lists for complex text

Use a vertical list for at least three parallel items or for dependent actions. Give the list an introductory sentence and keep the items grammatically parallel.
Permits: Issue 9 allows sentence fragments or complete sentences in lists. A publication can choose the list markers.
Rules: 4.3.
Before: "The issue needs the failing command, the expected result, and the actual result."
After:
> The issue needs these details:
>
> - The failing command
> - The expected result
> - The actual result

Edge cases:
- Use a colon after the introductory sentence.
- Give facts and instructions separate lists.
- Repeat a safety restriction in each affected item if a reader could act on that item alone.

## STE_14 One instruction per step

Start each step's action with a command verb. Give sequential actions separate steps so that the reader can follow their order.
Permits: Simultaneous actions can share a sentence or step. An immediate result or limit can follow the action in the same step.
Rules: 5.2, 5.3.
Before: "The operator checks the backup and resets the test database."
After:
> 1. Check the backup.
> 2. Reset the test database.

Edge cases:
- A critical risk condition can use "must". Ordinary actions use command verbs.
- A step can have several sentences when they describe simultaneous actions or an immediate result.
- A condition may precede the command verb, as STE_15 requires.

## STE_15 Condition before command

Put a condition before the command that depends on it. Put a comma between the condition and the command to make the boundary clear.
Permits: When no condition applies, the command starts the step.
Rules: 5.4.
Before: "Restart the worker if the health check fails."
After: "If the health check fails, restart the worker."
Edge case: Put a purpose or prerequisite first when the reader needs it before acting.

## STE_16 Notes hold no instructions

Use a note for extra information only. Move required work into a step and move risk controls into a risk note.
Permits: A note can contain several descriptive sentences. In descriptive text, Issue 9 reserves notes for information about a table or illustration.
Rules: 5.5.
Before: "Note: Stop the worker before the migration."
After: "Before the migration, stop the worker."
Edge cases:
- Read the steps without their notes. The reader must still have everything needed to complete the work.
- Put requirements, limits, and expected test results in the applicable step.
- A note sentence uses the descriptive length target.

## STE_17 Risk note before the risky step

Place the risk note before the step that can cause harm. After its label, give the safe action or condition, then state the consequence.
Permits: Software risks can use the project's own labels. Issue 9 requires a consequence when the consequence can be identified.
Rules: 7.1, 7.2, 7.3.
Before: "1. Confirm that the selected database is the disposable test database, then reset the selected database. Note: The reset deletes all rows."
After:
> DATA LOSS: Confirm that the selected database is the disposable test database. The reset deletes all rows.
> 1. Reset the selected database.

Edge cases:
- Cover data loss, production failure, secret exposure, and irreversible actions.
- A label alone is insufficient. Name the safe action or condition.
- If the consequence is uncertain, report that uncertainty for the publisher to resolve.
