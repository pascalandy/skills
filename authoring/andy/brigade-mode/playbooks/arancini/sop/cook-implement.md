# cook-implement

Run the section the Chef requests.

## Implement

- Use 🧰 poteto-mode to implement everything in your card, commit as you go, and open the PRs
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- Note each out-of-scope gap you find for the Chef. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Done when every item is implemented and checks are green, or each remaining item is reported to the Chef as blocked, with the reason

## Fix

- Fix each finding the Chef relays and commit each fix to the layer it belongs to. Run 🧰 2nd-pass on the fixes, then restack and push
- Done when each finding is pushed to its layer, or reported to the Chef with the reason it could not be

## Retros

- Run the retros the Chef requests, then report your issue links to the Chef
- Done when the Chef has your issue links, or knows that no finding passed
