# docwriter-update

Run the section the Chef requests in Cook<n>'s worktree while Cook<n> stays idle.

## Update

1. Run 🧰 andy-mode ; docs on the stack's final diff. Done when each doc that describes a behavior the stack changes matches the new behavior
2. If docs changed, commit them and open the docs PR as the top layer with 🧰 gh-stack. Otherwise report that no doc needed a change. Done when the Chef has the PR link or the no-docs decision

## Fix

1. Fix each finding the Chef relays on the docs PR and commit. Run 🧰 2nd-pass on the fixes, then push. Done when each finding is pushed, or reported to the Chef with the reason it could not be
