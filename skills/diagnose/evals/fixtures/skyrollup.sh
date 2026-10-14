# Sets up skyrollup 0.9.4 (a nightly weather summary job) with its git history, ./probe for wx-1 and the CDN, the incident report, and yesterday's case file.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/skyrollup" && pwd)"

repo="$fixture/repo"
old="$fixture/history"
state="${XDG_STATE_HOME:-$HOME/.local/state}/diagnose-cases/skyrollup/2026-10-13-summary-stuck"

export GIT_AUTHOR_NAME="Odile Brannock" GIT_AUTHOR_EMAIL="odile@fernlowwx.example"
export GIT_COMMITTER_NAME="Odile Brannock" GIT_COMMITTER_EMAIL="odile@fernlowwx.example"

commit() {
  git add -A
  GIT_AUTHOR_DATE="$1" GIT_COMMITTER_DATE="$1" \
    git -c commit.gpgsign=false commit -q --no-verify -m "$2"
}

put() {
  mkdir -p "$(dirname "$2")"
  cp "$1/$2" "$2"
}

version() {
  printf '__version__ = "%s"\n' "$1" > skyrollup/__init__.py
}

changelog_upto() {
  awk -v head="## $1 " 'NR <= 2 { print; next } index($0, head) == 1 { on = 1 } on' "$repo/CHANGELOG.md" > CHANGELOG.md
}

# 0.9.0
printf '__pycache__/\n' > .gitignore
for f in skyrollup/__main__.py skyrollup/config.py skyrollup/job.py skyrollup/publish.py skyrollup/status.py config.toml; do
  put "$repo" "$f"
done
for f in skyrollup/cli.py skyrollup/fetch.py skyrollup/summarize.py README.md; do
  put "$old/0.9.0" "$f"
done
version 0.9.0
commit "2026-01-10T16:24:05-05:00" "Nightly summary job for the station network"

put "$repo" systemd/skyrollup.service
put "$repo" systemd/skyrollup.timer
commit "2026-01-17T14:51:37-05:00" "Add systemd service and timer for wx-1"

changelog_upto 0.9.0
commit "2026-01-17T15:40:12-05:00" "Release 0.9.0"
git tag v0.9.0

# 0.9.1
put "$repo" tests/helpers.py
put "$repo" tests/test_job.py
commit "2026-02-07T11:03:12-05:00" "Add tests with a fake station source"

put "$repo" skyrollup/cli.py
put "$repo" tests/test_cli.py
put "$repo" README.md
commit "2026-03-21T10:40:02-04:00" "Add logs command to read the job's log file"

version 0.9.1
changelog_upto 0.9.1
commit "2026-03-21T10:52:47-04:00" "Release 0.9.1"
git tag v0.9.1

# 0.9.2
put "$repo" skyrollup/summarize.py
put "$repo" tests/test_summarize.py
commit "2026-04-29T21:15:09-04:00" "Leave out stations with fewer than 12 readings"

version 0.9.2
changelog_upto 0.9.2
commit "2026-04-30T08:02:55-04:00" "Release 0.9.2"
git tag v0.9.2

# 0.9.3
put "$old/0.9.3" skyrollup/fetch.py
GIT_AUTHOR_NAME="Rafe Linwood" GIT_AUTHOR_EMAIL="rafe.linwood@fernlowwx.example" \
  commit "2026-06-27T14:31:20-04:00" "Retry a station once before marking it offline"

version 0.9.3
changelog_upto 0.9.3
commit "2026-06-27T15:05:44-04:00" "Release 0.9.3"
git tag v0.9.3

# 0.9.4
put "$repo" skyrollup/fetch.py
put "$repo" tests/test_fetch.py
commit "2026-08-18T19:47:31-04:00" "Log offline stations at warning level"

version 0.9.4
changelog_upto 0.9.4
commit "2026-08-18T19:58:02-04:00" "Release 0.9.4"
git tag v0.9.4

git branch -M main

# Evidence and the read-only probe, kept out of git.
cp -R "$fixture/incident" incident
cp "$fixture/probe/probe.py" probe
chmod +x probe
mkdir -p .probe
tar -czf .probe/data.tgz -C "$fixture/probe/recordings" .
printf 'incident/\nprobe\n.probe/\n' >> .git/info/exclude
TZ=UTC touch -t 202610121150.00 incident/report.md

# Yesterday's case file.
mkdir -p "$state/artifacts"
cp "$fixture/case/case.md" "$state/case.md"
cp "$fixture/case/artifacts/"* "$state/artifacts/"
cp "$fixture/incident/report.md" "$state/artifacts/report.md"
TZ=UTC touch -t 202610131004.00 "$state/case.md" "$state/artifacts/"*
