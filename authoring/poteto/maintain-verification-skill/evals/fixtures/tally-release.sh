# Sets up tally one commit before 2.3: main at v2.2 with the verify-tally loop, branch occurrence-key checked out.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/tally-release" && pwd)"

apply() {
  cp -R "$fixture/history/$1/." .
}

commit() {
  git add -A
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" git commit -q -m "$2"
}

tag() {
  GIT_COMMITTER_DATE="$1" git tag -a "$2" -m "tally ${2#v}"
}

apply 01-sqlite-ledger
printf '__pycache__/\n' > .gitignore
commit "2026-04-20T20:41:12-04:00" "rewrite on a sqlite ledger, with Birchwood and Fernhill importers"
git branch -M main

apply 02-release-2.1
commit "2026-05-12T21:05:33-04:00" "2.1"
tag "2026-05-12T21:05:33-04:00" v2.1

apply 03-dry-run
commit "2026-06-02T19:48:20-04:00" "import --dry-run answers without writing to the ledger"

apply 04-balance-check
commit "2026-06-16T22:10:57-04:00" "import: check the inserted rows against the statement's own total"

mkdir -p skills/verify-tally
cp -R "$fixture/verify-tally/." skills/verify-tally/
mv skills/verify-tally/skill-md.txt skills/verify-tally/SKILL.md
chmod +x skills/verify-tally/scripts/smoke.py
cp "$fixture/agents-md.md" AGENTS.md
cp "$fixture/claude-md.md" CLAUDE.md
commit "2026-06-23T19:20:14-04:00" "add verify-tally: smoke import of the samples before merge"

apply 05-release-2.2
commit "2026-06-23T20:02:41-04:00" "2.2"
tag "2026-06-23T20:02:41-04:00" v2.2

git checkout -q -b occurrence-key
apply 06-occurrence-key
commit "2026-10-12T21:37:05-04:00" "dedupe on occurrence within the file so identical purchases stay separate (#41)"
