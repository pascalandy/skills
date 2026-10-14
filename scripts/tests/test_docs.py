"""Keep the hand-written docs in step with the files they describe.

docs/INDEX.md lists and counts every page (#521).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INDEX_ROW = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
TOTAL_PAGES = re.compile(r"\*\*Total pages:\*\* (\d+)")


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
