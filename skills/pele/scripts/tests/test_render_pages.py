"""Behavior tests for render_pages.py against a real pele install and a real browser."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SCRIPT = Path(__file__).parents[1] / "render_pages.py"
ASSETS = Path(__file__).parents[2] / "assets"

PROCESS = """\
---
config:
  themeVariables:
    noteBkgColor: "#123456"
title: "Handle a request"
---

sequenceDiagram
    autonumber
    participant CLI as Client
    participant OPS as Operations
    Note over CLI,OPS: PHASE 1 — Receive the request
    CLI->>OPS: Send<br/>the request
    OPS->>OPS: Check the request<br/>against the rules<br/>of the team
    Note over OPS: ✅ Oui — Request accepted
"""


def run(cwd: Path, *args: str) -> tuple[int, str, dict]:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    answer = done.stdout or done.stderr.splitlines()[-1]
    return done.returncode, done.stdout, json.loads(answer)


def test_a_process_becomes_a_light_and_a_dark_page_with_a_retina_image_each(
    project: Path, tmp_path: Path
) -> None:
    source = tmp_path / "process.mmd"
    source.write_text(PROCESS, encoding="utf-8")
    code, _, answer = run(project, str(source), "--actor", "CLI")
    assert code == 0
    names = ("claire.html", "sombre.html", "claire.jpg", "sombre.jpg")
    assert answer["files"] == [str(tmp_path / f"process-{name}") for name in names]
    light, dark = (
        Path(page).read_text(encoding="utf-8") for page in answer["files"][:2]
    )
    assert "<h1>Handle a request</h1>" in light
    assert "#123456" not in light
    assert "actor CLI as Client" in light
    assert "OPS->>OPS: Check the request against<br/>the rules of the team" in light
    assert "chaque flèche numérotée est une étape" in light
    assert "Bandeau de phase" in light
    assert "✅ Oui : le parcours continue" in light
    assert "Point de décision" not in light
    assert "⛔ Non" not in light
    assert (ASSETS / "theme-light.css").read_text(encoding="utf-8") in light
    assert (ASSETS / "theme-dark.css").read_text(encoding="utf-8") in dark
    for image in answer["files"][2:]:
        with Image.open(image) as jpeg:
            assert (jpeg.format, jpeg.width) == ("JPEG", 3840)


def test_a_diagram_of_another_type_is_refused_before_any_file_is_written(
    project: Path, tmp_path: Path
) -> None:
    source = tmp_path / "flow.mmd"
    source.write_text("flowchart LR\n  A --> B\n", encoding="utf-8")
    code, stdout, answer = run(project, str(source))
    assert code == 1
    assert stdout == ""
    assert "sequence diagrams only" in answer["errors"][0]
    assert list(tmp_path.iterdir()) == [source]


def test_a_diagram_error_names_its_file_and_line(project: Path, tmp_path: Path) -> None:
    source = tmp_path / "broken.mmd"
    source.write_text("sequenceDiagram\n  A-->>>B[[: x\n", encoding="utf-8")
    code, _, answer = run(project, str(source))
    assert code == 1
    assert answer["errors"][0].startswith(f"{source}:2:")
    assert list(tmp_path.iterdir()) == [source]


def test_an_actor_the_diagram_does_not_declare_is_a_usage_error(
    project: Path, tmp_path: Path
) -> None:
    source = tmp_path / "process.mmd"
    source.write_text(PROCESS, encoding="utf-8")
    code, _, answer = run(project, str(source), "--actor", "NOPE")
    assert code == 2
    assert answer["errors"][0].startswith("--actor NOPE:")
    assert answer["help"] == "render_pages.py --help"
