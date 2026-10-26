# Sets up departures-api 3.4 with its git history, the Harbor screens incident files, and a read-only ./probe.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/departures" && pwd)"

TEO=("Teo Brandvold" "teo.brandvold@tamaracktransit.example")
MIRELA=("Mirela Szanto" "mirela.szanto@tamaracktransit.example")
AURELIO=("Aurelio Fenn" "aurelio.fenn@tamaracktransit.example")

apply() {
  cp -R "$fixture/history/$1/." .
}

commit() {
  local when="$1" name="$2" email="$3"
  shift 3
  git add -A
  GIT_AUTHOR_NAME="$name" GIT_AUTHOR_EMAIL="$email" GIT_AUTHOR_DATE="$when" \
  GIT_COMMITTER_NAME="$name" GIT_COMMITTER_EMAIL="$email" GIT_COMMITTER_DATE="$when" \
    git -c commit.gpgsign=false commit -q --no-verify "$@"
}

printf '__pycache__/\n' > .gitignore
apply 01-base
commit "2026-06-29T10:14:02+00:00" "${TEO[@]}" -m "departures-api 3.2, moved out of the transit-tools repo" \
  -m "Same code as transit-tools/departures at 3.2.0, with its tests and sample feed. History stays in transit-tools."

apply 02-weekend-tests
commit "2026-07-21T15:40:37+00:00" "${AURELIO[@]}" -m "tests: Saturday and Sunday timetables"

apply 03-client-field
commit "2026-08-12T13:05:51+00:00" "${MIRELA[@]}" -m "request log: client type from the X-Client header" \
  -m "Screens send X-Client: screen and the website sends X-Client: web, so the dashboards can split the two."

apply 04-release-3.3
commit "2026-08-13T09:22:10+00:00" "${MIRELA[@]}" -m "3.3"
git tag v3.3

apply 05-cache
commit "2026-10-08T14:48:26+00:00" "${AURELIO[@]}" -m "response cache for departures" \
  -m "Screens poll every 30 seconds, and timetable departures only change on the minute, so most polls repeat work done earlier in the same minute. Keep each stop's departures for the minute they were computed in, per process. The request log gains a cache field: hit, miss, or off (--no-cache)."

apply 06-release-3.4
commit "2026-10-13T16:31:09+00:00" "${TEO[@]}" -m "3.4"
git tag v3.4
git branch -M main

mkdir -p incident .probe
cp "$fixture/incident/report.md" "$fixture/incident/deploy.log" "$fixture/incident/alerts.txt" incident/
cp "$fixture/probe/probe.py" probe
chmod +x probe

staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT
cp "$fixture/probe/recordings/"* "$staging/"
python3 "$fixture/probe/feedgen.py" "$staging/feeds"
COPYFILE_DISABLE=1 tar -czf .probe/data.tgz -C "$staging" .

exclude="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude")"
printf 'incident/\nprobe\n.probe/\n' >> "$exclude"
