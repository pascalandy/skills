"""Keep the hand-written docs in step with the files they describe.

docs/INDEX.md lists and counts every page (#521), and the pages a reader
follows to pick a skill name no deleted one (#575).
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Iterator
from pathlib import Path

from conftest import commit

ROOT = Path(__file__).resolve().parents[2]

INDEX_ROW = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
TOTAL_PAGES = re.compile(r"\*\*Total pages:\*\* (\d+)")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
# The pages a reader follows to pick a skill
SKILL_GUIDES = ("README.md", "docs/guide", "docs/guide-fr-ca", ".agents")
# A fence opens on three or more backticks or tildes, and only a run of the
# same character, at least as long and with nothing after it, closes it
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
ROUTE_WORD = re.compile(r"\b(?:routes?|playbooks?)\b", re.IGNORECASE)


def markdown(root: Path, *places: str) -> list[Path]:
    """Each Markdown file a place names: the file itself, or every one under the folder."""
    found: list[Path] = []
    for place in places:
        path = root / place
        found += [path] if path.is_file() else sorted(path.rglob("*.md"))
    return found


def lines(path: Path) -> Iterator[tuple[int, str, bool]]:
    """Each line with its number and whether a fenced code block holds it; fences are skipped."""
    fence = ""
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = FENCE.match(line)
        if match and not fence:
            fence = match.group(1)
            continue
        if (
            match
            and match.group(1)[0] == fence[0]
            and len(match.group(1)) >= len(fence)
            and not match.group(2).strip()
        ):
            fence = ""
            continue
        yield number, line, bool(fence)


def pages(docs: Path) -> list[str]:
    """Each page the index counts, relative to docs/: every Markdown file but the
    index, the AGENTS.md files, and the copied inputs a sources/ folder keeps."""
    return sorted(
        path.relative_to(docs).as_posix()
        for path in docs.rglob("*.md")
        if path != docs / "INDEX.md"
        and path.name != "AGENTS.md"
        and "sources" not in path.relative_to(docs).parts
    )


def needs_row(page: Path) -> bool:
    """A page beside a README.md, such as a guide page, counts under that README's row."""
    return page.name == "README.md" or not (page.parent / "README.md").is_file()


def index_problems(docs: Path) -> list[str]:
    index = (docs / "INDEX.md").read_text(encoding="utf-8")
    rows = INDEX_ROW.findall(index)
    found = pages(docs)
    problems = [
        f"docs/INDEX.md has no row for {page}; add one to its kind/* table"
        for page in found
        if page not in rows and needs_row(docs / page)
    ]
    problems += [
        f"docs/INDEX.md lists {row}, which docs/ does not hold; remove the row or restore the page"
        for row in rows
        if not (docs / row).is_file()
    ]
    total = TOTAL_PAGES.search(index)
    said = total.group(1) if total else "missing"
    if said != str(len(found)):
        problems.append(
            f"docs/INDEX.md says Total pages: {said}, but docs/ holds {len(found)} pages; set it to {len(found)}"
        )
    return problems


def deleted_skills(root: Path) -> set[str]:
    """Each name git history held under skills/ that no skill holds now, so a
    rename and an uncommitted deletion count too."""
    log = subprocess.run(
        [
            "git",
            "log",
            "--no-renames",
            "--name-only",
            "--format=",
            "--",
            "skills/*/SKILL.md",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    held = {Path(line).parts[1] for line in log.splitlines() if line.count("/") == 2}
    return {
        name for name in held if not (root / "skills" / name / "SKILL.md").is_file()
    }


def deleted_skill_mentions(root: Path) -> list[str]:
    """Each deleted name alone between backticks, or alone on a code-block line.

    On a line that says route or playbook, a name beside a mode it is a route
    of, as in "the `andy-mode` routes `cass`", names the route, and
    `html-mode ; plan` names a route in full.
    """
    deleted = deleted_skills(root)
    routes = {
        playbooks.parent.name: {
            entry.name.removesuffix(".md")
            for entry in playbooks.iterdir()
            if not entry.name.startswith(".")
        }
        for playbooks in (root / "skills").glob("*/playbooks")
    }
    mentions: list[str] = []
    for path in markdown(root, *SKILL_GUIDES):
        for number, line, fenced in lines(path):
            if fenced:
                names = {line.strip()}
            else:
                spans = {span.strip() for span in CODE_SPAN.findall(line)}
                names = spans
                if ROUTE_WORD.search(CODE_SPAN.sub("", line)):
                    names -= {route for span in spans for route in routes.get(span, ())}
            mentions += [
                f"{path.relative_to(root).as_posix()}:{number}: names `{name}`, a deleted skill;"
                f" name what replaced it, or its route as `<mode> ; {name}`"
                for name in sorted(names & deleted)
            ]
    return mentions


def test_lines_close_a_fence_only_on_its_own_character_and_length(
    tmp_path: Path,
) -> None:
    page = tmp_path / "page.md"
    page.write_text(
        "````markdown\n```\ninside\n````\nafter\n~~~\n```\nstill inside\n~~~\n",
        encoding="utf-8",
    )

    assert [(number, fenced) for number, _, fenced in lines(page)] == [
        (2, True),
        (3, True),
        (5, False),
        (7, True),
        (8, True),
    ]


def test_index_lists_and_counts_every_page() -> None:
    problems = index_problems(ROOT / "docs")
    assert not problems, "\n".join(problems)


def test_index_problems_name_the_missing_row_the_stale_row_and_the_count(
    tmp_path: Path,
) -> None:
    for page in (
        "AGENTS.md",
        "guide/README.md",
        "guide/01-start.md",
        "ideas/plan.md",
        "ideas/sources/brief.md",
        "references/new.md",
    ):
        (tmp_path / page).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / page).touch()
    (tmp_path / "INDEX.md").write_text(
        "> **Total pages:** 3\n\n"
        "| `guide/README.md` | The guide |\n"
        "| `ideas/plan.md` | A plan |\n"
        "| `references/gone.md` | A page since removed |\n",
        encoding="utf-8",
    )

    assert index_problems(tmp_path) == [
        "docs/INDEX.md has no row for references/new.md; add one to its kind/* table",
        "docs/INDEX.md lists references/gone.md, which docs/ does not hold; remove the row or restore the page",
        "docs/INDEX.md says Total pages: 3, but docs/ holds 4 pages; set it to 4",
    ]


def test_no_guide_names_a_deleted_skill() -> None:
    shallow = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert shallow == "false", (
        "a shallow clone hides deleted skills; run: git fetch --unshallow"
    )
    mentions = deleted_skill_mentions(ROOT)
    assert not mentions, "\n".join(mentions)


def test_deleted_skill_mentions_skip_routes_and_plain_words(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    for page in (
        "skills/plan/SKILL.md",
        "skills/cass/SKILL.md",
        "skills/html-mode/playbooks/plan.md",
        "skills/andy-mode/playbooks/cass.md",
    ):
        (tmp_path / page).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / page).touch()
    commit(tmp_path)
    (tmp_path / "skills/plan/SKILL.md").unlink()
    commit(tmp_path)
    # A deletion not yet committed counts too
    (tmp_path / "skills/cass/SKILL.md").unlink()
    (tmp_path / "README.md").write_text(
        "Run `plan` first.\n"
        "Run `html-mode ; plan`, then make a plan.\n"
        "The `andy-mode` routes `cass` and `qmd` need a computer.\n"
        "Run `plan` first, then use `html-mode`.\n"
        "```text\n"
        "plan\n"
        "```\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/guide").mkdir(parents=True)
    (tmp_path / "docs/guide/01-start.md").write_text("Try `cass`.\n", encoding="utf-8")

    assert deleted_skill_mentions(tmp_path) == [
        "README.md:1: names `plan`, a deleted skill; name what replaced it, or its route as `<mode> ; plan`",
        "README.md:4: names `plan`, a deleted skill; name what replaced it, or its route as `<mode> ; plan`",
        "README.md:6: names `plan`, a deleted skill; name what replaced it, or its route as `<mode> ; plan`",
        "docs/guide/01-start.md:1: names `cass`, a deleted skill; name what replaced it, or its route as `<mode> ; cass`",
    ]
