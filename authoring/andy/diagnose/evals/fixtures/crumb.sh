# Sets up crumb, Crumb & Co.'s order export (history to v1.6), with the kitchen's incident notes and the ops probe.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/crumb" && pwd)"

repo="$fixture/repo"
hist="$fixture/history"

put() { # put <source file> <path in repo>
  mkdir -p "$(dirname "$2")"
  cp "$1" "$2"
}

changelog() { # changelog <version>: CHANGELOG.md as it stood at that release
  awk -v v="## $1 " 'index($0, v) == 1 { keep = 1 } NR <= 2 || keep' \
    "$repo/CHANGELOG.md" > CHANGELOG.md
}

commit() { # commit <date> <author> <email> <message> [tag]
  git add -A
  GIT_AUTHOR_NAME="$2" GIT_AUTHOR_EMAIL="$3" GIT_AUTHOR_DATE="$1" \
    GIT_COMMITTER_NAME="$2" GIT_COMMITTER_EMAIL="$3" GIT_COMMITTER_DATE="$1" \
    git commit -q -m "$4"
  if [ -n "${5:-}" ]; then
    GIT_COMMITTER_NAME="$2" GIT_COMMITTER_EMAIL="$3" GIT_COMMITTER_DATE="$1" \
      git tag -a "$5" -m "crumb $5"
  fi
}

jo=("Jo Lindqvist" "jo@crumbandco.example")
priya=("Priya Nadeau" "priya@crumbandco.example")

printf '__pycache__/\ndev/*.db\n' > .gitignore
put "$repo/crumb/__init__.py" crumb/__init__.py
put "$hist/01/crumb/db.py" crumb/db.py
put "$hist/01/README.md" README.md
commit "2026-02-16T10:12:44-05:00" "${jo[@]}" "Read preorders from the orders database"

put "$hist/02/crumb/sheet.py" crumb/sheet.py
put "$hist/02/crumb/export.py" crumb/export.py
put "$repo/crumb/mail.py" crumb/mail.py
changelog 1.0
commit "2026-02-17T16:40:09-05:00" "${jo[@]}" "Add the evening export that mails the kitchen tomorrow's sheet" v1.0

put "$hist/03/crumb/db.py" crumb/db.py
put "$hist/03/tests/test_sheet.py" tests/test_sheet.py
changelog 1.1
commit "2026-03-11T11:05:31-04:00" "${priya[@]}" "Sort the sheet by pickup time, add first tests" v1.1

put "$hist/04/crumb/export.py" crumb/export.py
changelog 1.2
commit "2026-04-22T15:18:02-04:00" "${jo[@]}" "Add --dry-run to print the sheet instead of mailing it" v1.2

put "$repo/crumb/db.py" crumb/db.py
put "$repo/dev/orders.sql" dev/orders.sql
sed 's/ Either way the job logs the target date and the order count to stderr\.//' \
  "$repo/README.md" > README.md
changelog 1.3
commit "2026-05-27T10:47:55-04:00" "${priya[@]}" "Name the prod and staging databases, add sample orders for local runs" v1.3

put "$repo/crumb/sheet.py" crumb/sheet.py
put "$repo/tests/test_sheet.py" tests/test_sheet.py
changelog 1.4
commit "2026-06-30T14:22:18-04:00" "${jo[@]}" "Show order notes on the sheet" v1.4

put "$hist/07/crumb/export.py" crumb/export.py
put "$repo/README.md" README.md
changelog 1.5
commit "2026-07-21T09:58:40-04:00" "${priya[@]}" "Log the target date and order count, report unreadable databases" v1.5

put "$repo/crumb/export.py" crumb/export.py
put "$repo/tests/test_export.py" tests/test_export.py
put "$repo/CHANGELOG.md" CHANGELOG.md
commit "2026-08-12T16:31:27-04:00" "${jo[@]}" "Add --now so tests can pin the clock" v1.6

git branch -M main

mkdir -p incident .probe
cp -R "$fixture/incident/." incident/
cp "$fixture/probe/probe.py" probe
chmod +x probe
tar -czf .probe/data.tgz -C "$fixture/probe/recordings" .

mkdir -p .git/info
printf 'incident/\nprobe\n.probe/\n' >> .git/info/exclude
