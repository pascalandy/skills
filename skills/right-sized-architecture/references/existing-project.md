# Existing project

Compare the current structure of the code with the smallest structure that fits, and report each gap. Leave the code unchanged. The user decides what to do with the findings, so write no change plan.

A gap has one of three types:

- **Over**: the code has more structure than its business rules justify
- **Under**: a named pain shows that the structure is too small
- **Boundary**: a module boundary is in the wrong place

## Steps

1. Gather the Step 1 inputs of `SKILL.md` from the code, its documents, and the conversation. Add these two inputs:
   - Current structure: the deployables, the modules or the folders that act as modules, and the external services
   - Pains that the user or the history names, such as bugs that cluster in one area, tests that are hard to write, or changes that touch many folders

   Done when each input is known or listed as an open question.
2. Run Steps 2 to 6 of `SKILL.md` on the product as it is today. The result is the right-sized structure.
   Done when the done criterion of each of those steps holds.
3. Record the current state of each module: its level, its ports, its events, and its queues.
   Done when each module or folder from step 1 has a current level.
4. Compare the current state with the right-sized structure, and list each gap as a finding. Use the examples below to recognize a gap.
   Done when each finding has a type, a location, the current state, the right-sized state, and its evidence.
5. Write the report from the template below. Put the report in the reply, unless the user names another output.
   Done when each Under finding names a pain from step 1 and the report contains no change plan.

## Examples of gaps

Over:

- A level 3 module that holds only reads and writes
- A port with one adapter and no test that uses the port
- An event that no second module consumes
- A queue for work that the response waits for

Under:

- Business rules in routes, pages, or UI components, in an area where bugs cluster
- A module that reads the tables of another module, where changes break both modules

Boundary:

- One module that holds two meanings of the same business word
- Two modules that always change together

Report an Under finding only when a pain from step 1 supports it. Without a pain, the smaller structure is correct.

## Report template

Keep every heading. If a heading has no content, write `none` there. The two module rows are examples of the format, so replace them.

```markdown
## Architecture assessment

### Summary
<two or three sentences: the structure is right-sized, over, or under, and where>

### Modules
| Module or folder | Current level | Right-sized level and reason | Gap |
|---|---|---|---|
| billing | 1 | 3: proration and refund rules, bugs cluster here | under |
| settings | 3 | 0: reads and writes only | over |

### Findings
1. <Over, Under, or Boundary>: <location>. Current: <state>. Right-sized: <state>. Evidence: <pain, file, or business rule>

### Right-sized today
- <module, port, or decision that needs no change>

### Open questions
1. <question>
```
