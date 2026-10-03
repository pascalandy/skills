# A branch whose diff against main changes only README prose
set -euo pipefail
printf '# widgets\n\nWidgets formats prices.\n' > README.md
printf 'def label(cents):\n    return "$" + format(cents / 100, ",.2f")\n' > prices.py
git add -A && git commit -qm "Add prices" && git branch -M main
git switch -q -c readme-intro
printf '# widgets\n\nWidgets turns cents into price labels, such as $4.50.\n' > README.md
git commit -qam "Explain what widgets does"
