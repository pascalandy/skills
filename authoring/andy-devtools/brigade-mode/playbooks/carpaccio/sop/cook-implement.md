# cook-implement

Run the section the Chef requests.

## Implement

- Use 🧰 poteto-mode to implement every card of your batch, commit as you go, and open the PRs. Link each PR to your thread with `link_pull_request` as you open it
- Order the work by bang for the buck. Wiring in finished code that isn't connected yet is the typical quick win
- Note each out-of-scope gap you find for the Chef. File one as an issue with 🧰 label-for-issues only when it deserves its own fix and no existing issue covers it
- Send a question you cannot settle to the Chef, with the default you would apply, and keep working on what it does not block
- On Claude Code, delegate side work with `delegate_task` to the `delegate-on-claude` target of `[cook]` in `config.toml`, never to a native subagent, which runs on your own Claude quota
- Done when every card is implemented and checks are green, or each remaining card is reported to the Chef as blocked, with the reason

## Fix

- Fix each finding the Chef relays and commit each fix to the layer it belongs to. Run 🧰 2nd-pass on the fixes, then restack and push
- Done when each finding is pushed to its layer, or reported to the Chef with the reason it could not be

## Stop

- Stop at a clean, pushed checkout. Report your branches and their heads to the Chef, then settle yourself as 🧰 t3-runtime says
- Done when the Chef has your branches and heads, and you are settled

## Retros

- Run the retros the Chef requests, report your issue links to the Chef, then settle yourself as 🧰 t3-runtime says
- Done when the Chef has your issue links, or knows that no finding passed, and you are settled
