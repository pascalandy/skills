# cod-implement

COD runs this SOP from its launch to its merge. Each section starts when MAIN asks for it.

## Implement

- Use 🧰 poteto-mode to implement everything in your card, commit as you go, and open the PRs
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- Note each out-of-scope gap you find for MAIN. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Done when every item is implemented and checks are green, or each remaining item is reported as blocked, with the reason

## Fix

- Fix each finding MAIN relays. Commit each fix to the layer it belongs to, restack, and push
- Done when each finding is pushed to its layer, or reported with the reason it could not be

## Merge

- Land your stack with 🧰 poteto-mode ; shipping, through the project's merge command and any deploy it runs. The merge command can exit 0 after a failed deploy, so read its output
- Remove your worktrees
- Done when each PR is merged and its deploy succeeded, or you reported the failure

## Retros

- Run your retros as `main-closing`, step 3, says, then report your issue links to MAIN
- Done when MAIN has your issue links, or knows that no finding passed
