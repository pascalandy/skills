"""Behavior tests for render_diagrams.py against a real pele install; pnpm downloads it once."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "render_diagrams.py"
PELE = "pele@1.6.0"


@pytest.fixture(scope="session")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A folder with pele installed, as a project that uses it would have."""
    if shutil.which("pnpm") is None:
        pytest.fail(
            "pnpm not found; install it, then rerun: https://pnpm.io/installation"
        )
    folder = tmp_path_factory.mktemp("project")
    subprocess.run(["pnpm", "add", PELE], cwd=folder, check=True, capture_output=True)
    return folder


def run(
    cwd: Path, *args: str, stdin: str = "", cache: Path | None = None
) -> tuple[int, str, dict]:
    env = {**os.environ, "XDG_CACHE_HOME": str(cache or cwd / "no-cache")}
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        input=stdin,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    answer = done.stdout or done.stderr.splitlines()[-1]
    return done.returncode, done.stdout, json.loads(answer)


def test_an_error_points_at_its_line_in_the_markdown_file(project: Path) -> None:
    notes = project / "notes.md"
    notes.write_text(
        "# Notes\n\n```mermaid\nflowchart LR\n  A --> B\n```\n\n```mermaid\nflowchart LR\n  A --> B[[[\n```\n"
    )
    code, stdout, answer = run(project, str(notes), "--output", str(project / "out"))
    assert code == 1
    assert stdout == ""
    assert answer["errors"][0].startswith(f"{notes}:10:12: syntax:")
    assert [d["source"] for d in answer["diagrams"]] == [f"{notes}:4"]
    assert Path(answer["diagrams"][0]["svg"]).is_file()


@pytest.mark.parametrize(("flag", "styled"), [((), True), (("--no-theme",), False)])
def test_the_bundled_theme_styles_each_svg_unless_turned_off(
    project: Path, flag: tuple[str, ...], styled: bool
) -> None:
    out = project / f"out-{styled}"
    code, _, answer = run(
        project, "-", "--output", str(out), *flag, stdin='pie\n  "A" : 1\n'
    )
    assert code == 0
    assert answer["pele"]["version"] == "1.6.0"
    assert answer["diagrams"][0]["type"] == "pie"
    svg = Path(answer["diagrams"][0]["svg"]).read_text()
    assert ("--pele-bg: #000000" in svg) is styled


def test_a_check_without_output_writes_nothing(project: Path) -> None:
    diagram = project / "check.mmd"
    diagram.write_text("sequenceDiagram\n  A->>B: Hi\n")
    before = set(project.iterdir())
    code, _, answer = run(project, str(diagram))
    assert code == 0
    assert "svg" not in answer["diagrams"][0]
    assert set(project.iterdir()) == before


def test_pele_in_the_cache_serves_a_folder_without_it(
    project: Path, tmp_path: Path
) -> None:
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "pele").symlink_to(project)
    code, _, answer = run(tmp_path, "-", stdin="flowchart LR\n  A --> B\n", cache=cache)
    assert code == 0
    assert answer["pele"]["version"] == "1.6.0"


def test_missing_pele_names_the_install_command(tmp_path: Path) -> None:
    code, _, answer = run(tmp_path, "-", stdin="flowchart LR\n  A --> B\n")
    assert code == 1
    assert "pnpm --dir" in answer["errors"][0]
