# Sets up pantry-search at v5.3 (blue pool slow since the 5.3 release) with the exported alert and a read-only probe.
set -euo pipefail
fixture="$(cd "$(dirname "$0")/pantry" && pwd)"

commit() {
  local when="$1" name="$2" email="$3"
  shift 3
  local args=()
  for paragraph in "$@"; do
    args+=(-m "$paragraph")
  done
  git add -A
  GIT_AUTHOR_NAME="$name" GIT_AUTHOR_EMAIL="$email" GIT_AUTHOR_DATE="$when" GIT_COMMITTER_DATE="$when" \
    git -c commit.gpgsign=false commit -q --no-verify "${args[@]}"
}

tag() {
  GIT_COMMITTER_DATE="$2" git -c tag.gpgsign=false tag -a "$1" -m "$3"
}

cp -R "$fixture/repo-v5.2/." .
printf '__pycache__/\n' > .gitignore
commit 2026-09-21T15:42:00Z "Teodor Lind" teodor.lind@pantry.example \
  "Import pantry-search 5.2.0" \
  "History before 5.2 stays in the old monorepo."
tag v5.2 2026-09-22T09:05:00Z "pantry-search 5.2.0"

cp -R "$fixture/commits/1-rating/." .
commit 2026-10-05T13:18:00Z "Amara Quist" amara.quist@pantry.example \
  "Add rating to search hits" \
  "Each hit carries the recipe's mean stars and review count, for the star
display on search results."

cp -R "$fixture/commits/2-recency/." .
commit 2026-10-06T10:47:00Z "Teodor Lind" teodor.lind@pantry.example \
  "Boost recently updated recipes in ranking" \
  "Recipes edited this month were buried under older ones with more saves.
The boost is 1.5 at most, less than one title match, so a better match
still wins."

cp -R "$fixture/commits/3-encoder/." .
commit 2026-10-07T16:02:00Z "Nnamdi Oyelaran" nnamdi.oyelaran@pantry.example \
  "Encode responses with sorted keys" \
  "Sorted keys give identical bytes for identical results. Floats are
rounded to two places, which the rating display wants anyway."

cp -R "$fixture/commits/4-access-log/." .
commit 2026-10-08T11:26:00Z "Nnamdi Oyelaran" nnamdi.oyelaran@pantry.example \
  "Log request size and user agent"

cp -R "$fixture/commits/5-base-image/." .
commit 2026-10-12T15:10:00Z "Ilse Brandvold" ilse.brandvold@pantry.example \
  "Move base image to Python 3.12.7" \
  "Picks up the 3.12.7 fixes and sets the 5.3.0 release date."
tag v5.3 2026-10-13T09:12:00Z "pantry-search 5.3.0"
git branch -M main

mkdir -p incident .probe
cp "$fixture/incident/p95.csv" "$fixture/incident/alert.md" incident/
cp "$fixture/probe/probe.py" probe
chmod +x probe
python3 -I - "$fixture/probe/recordings" .probe/data.tgz <<'PY'
import sys
import tarfile
from pathlib import Path

source, target = Path(sys.argv[1]), sys.argv[2]
with tarfile.open(target, "w:gz") as archive:
    for path in sorted(p for p in source.rglob("*") if p.is_file()):
        info = archive.gettarinfo(path, arcname=path.relative_to(source).as_posix())
        info.mtime = 1791987600
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        with path.open("rb") as handle:
            archive.addfile(info, handle)
PY
exclude="$(git rev-parse --git-path info/exclude)"
mkdir -p "$(dirname "$exclude")"
printf '/incident/\n/probe\n/.probe/\n' >> "$exclude"
