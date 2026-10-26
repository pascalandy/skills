# A worktree whose local main lags origin/main, while main is checked out in another worktree
set -euo pipefail
run=$(cd .. && pwd)
git init -q --bare -b main "$run/origin.git"
git remote add origin "$run/origin.git"
printf '# widgets\n' > README.md
git add -A && git commit -qm "Add README" && git branch -M main && git push -q origin main
git clone -q "$run/origin.git" "$run/elsewhere"
printf 'MIT\n' > "$run/elsewhere/LICENSE"
git -C "$run/elsewhere" add LICENSE
git -C "$run/elsewhere" -c user.name=Other -c user.email=other@example.invalid commit -qm "Add LICENSE"
git -C "$run/elsewhere" push -q origin main
git fetch -q origin
git switch -q --detach
git worktree add -q "$run/trunk" main
