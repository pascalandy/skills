# A branch with one README fix, in a repository whose AGENTS.md sets the PR title format; pushes go to a local copy
set -euo pipefail
run=$(cd .. && pwd)
git init -q --bare -b main "$run/origin.git"
git remote add origin https://github.com/acme/widgets.git
git remote set-url --push origin "$run/origin.git"
cp "$EVALS/fixtures/agents-md.md" AGENTS.md
printf '# widgets\n\nInstal with `make install`.\n' > README.md
git add -A && git commit -qm "Add README" && git branch -M main && git push -q origin main
git switch -q -c fix-readme-typo
printf '# widgets\n\nInstall with `make install`.\n' > README.md
git commit -qam "Fix the install typo in README"
