# A one-layer stack on a GitHub repository, before any PR exists; pushes go to a local copy
set -euo pipefail
run=$(cd .. && pwd)
git init -q --bare -b main "$run/origin.git"
git remote add origin https://github.com/acme/widgets.git
git remote set-url --push origin "$run/origin.git"
printf '# widgets\n' > README.md
git add -A && git commit -qm "Add README" && git branch -M main && git push -q origin main
git switch -q -c config
printf 'def load():\n    return {}\n' > config.py
git add config.py && git commit -qm "Add config loader"
gh stack init config > /dev/null 2>&1
