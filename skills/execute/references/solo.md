# Solo route

## Who runs each step

| Step | Who and how |
|---|---|
| Execute, Self-check | You |
| Blast-radius impacts | 🧰 headless `--review-only` on the stack's PR URLs |
| Code review across the whole stack | 🧰 headless `--review-fix` in a sandbox (`.git` read-only, no network) within the stack's checkout |
| Docs | You. Commit each edit to the layer it belongs to |
| Final review | 🧰 headless `--review-fix` in the same sandbox, with the **fix** ending |
| Report, Merge, Closing | You |

## Headless runs

- Show the command in a code block before you run it
- Skip the sandbox when the reviewer's CLI has none
- When the reviewer's CLI isn't installed, as in a cloud environment, give the same brief to your own subagent tool, as 🧰 headless describes
