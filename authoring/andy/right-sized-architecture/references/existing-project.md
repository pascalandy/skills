# Existing project

Compare the current structure of the code with the structure that the requirements justify. Report each gap. Leave the code unchanged. The user decides what to do with the findings, so write no change plan.

A gap has one of three types:

- **Over**: the code has more structure than a current requirement justifies
- **Under**: a current problem shows that the structure is too small
- **Boundary**: a module boundary is in the wrong place

## Steps

1. Gather the Step 1 inputs of `SKILL.md` from the code, its documents, and the conversation. Add these two inputs:
   - **Current structure**: the deployables, the modules or the folders that act as modules, and the external services
   - **Problems**: the problems that the user reports, or that the Git history or the issue tracker shows. Examples are recurring bugs, tests that are hard to write, and changes that touch many folders

   Done when you know each input or list it as an open question.
2. Run Steps 2 to 6 of `SKILL.md` on the current product, without the 7-module limit. The result is the justified structure.
   Done when each of those steps meets its done criterion.
3. Record the current state of each module: its level, ports, events, and queues. When one module holds more than one level, write `mixed` and name the paths. When a folder holds no single business domain, write `none`.
   Done when each module or folder of the current structure has a level, `mixed`, or `none`.
4. List each gap between the current state and the justified structure as a finding. Apply the rules below.
   Done when each finding has a type, a location, the current state, the justified state, and its evidence.
5. Use the format and the destination that the user requests. By default, put the findings in the reply, in the format below.
   Done when each finding follows the rules below, and the output lists each open question and contains no change plan.

## Rules for a finding

- When no current requirement justifies an item of the current structure, report an Over finding
- When the current structure is smaller than the justified structure, look for a problem that the smaller structure causes. If the Problems input shows one, report an Under finding. If the Problems input shows none, report no gap
- A Boundary finding that divides a module needs the same evidence as an Under finding

Examples of an Over finding:

- A level 3 module that holds only reads and writes
- A port that meets no Step 5 condition of `SKILL.md`
- An event that no second module consumes
- A queue for work that the response waits for

Examples of an Under finding:

- Business rules in routes, pages, or UI components, in an area where bugs recur
- A module that reads the tables of another module, where one change breaks both modules

Examples of a Boundary finding:

- One module that holds two meanings of the same business word, where changes for one meaning break the other
- Two modules that always change together

## Format

```markdown
## Architecture findings

1. <Over, Under, or Boundary>: <location>. Current: <state>. Justified: <state>. Evidence: <problem, file, or business rule>
```

When the comparison finds no gap, say so in the output language. After the findings, list each open question from step 1.
