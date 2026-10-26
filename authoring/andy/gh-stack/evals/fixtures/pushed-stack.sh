# A two-layer stack, main <- parser <- cli, pushed to a remote that refuses non-fast-forward pushes
set -euo pipefail
run=$(cd .. && pwd)
git init -q --bare -b main "$run/origin.git"
git -C "$run/origin.git" config receive.denyNonFastForwards true
git remote add origin "$run/origin.git"
cp "$EVALS/fixtures/agents-md.md" AGENTS.md
printf '# widgets\n' > README.md
printf '__pycache__/\n' > .gitignore
git add -A && git commit -qm "Add README" && git branch -M main && git push -q origin main
git switch -q -c parser
printf 'def parse(line):\n    """Parse one line of the config fiel."""\n    return line.split("=", 1)\n' > parser.py
git add parser.py && git commit -qm "Add parser"
git switch -q -c cli
printf 'from parser import parse\n\nprint(parse("a=b"))\n' > cli.py
git add cli.py && git commit -qm "Add CLI"
gh stack init parser cli > /dev/null 2>&1
git push -q origin parser cli
