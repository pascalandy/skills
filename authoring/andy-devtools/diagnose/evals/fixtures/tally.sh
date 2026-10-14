# Sets up the tally repo at 2.3 (tags v2.1, v2.2, v2.3) with Maren's September statements and ledger copy in incident/.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/tally" && pwd)"

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

apply 05-release-2.2
commit "2026-06-23T20:02:41-04:00" "2.2"
tag "2026-06-23T20:02:41-04:00" v2.2

apply 06-occurrence-key
commit "2026-09-28T21:37:05-04:00" "dedupe on occurrence within the file so identical purchases stay separate (#41)"

apply 07-release-2.3
commit "2026-09-30T19:15:48-04:00" "2.3"
tag "2026-09-30T19:15:48-04:00" v2.3

mkdir -p incident/statements
cp "$fixture/incident/report.md" incident/
cp "$fixture/incident/statements/birchwood-2026-09.csv" "$fixture/incident/statements/fernhill-2026-09.csv" incident/statements/
python3 - "$fixture/incident/ledger.sql" incident/ledger.sqlite <<'PY'
import sqlite3
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    script = handle.read()
conn = sqlite3.connect(sys.argv[2])
conn.executescript(script)
conn.close()
PY
printf 'incident/\n' >> .git/info/exclude
