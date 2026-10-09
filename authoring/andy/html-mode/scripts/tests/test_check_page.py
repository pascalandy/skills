"""End-to-end tests: check_page.py run on real pages in a real browser."""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_page

BROWSER = (
    os.environ.get("CHECK_PAGE_BROWSER")
    or shutil.which("chromium")
    or shutil.which("google-chrome")
)
needs_browser = pytest.mark.skipif(
    BROWSER is None, reason="no Chromium on PATH; set CHECK_PAGE_BROWSER"
)

# The package bundles one HTML file, the slides template, so the test pages live here
GOOD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>A page that passes</title>
<style>
  :root { --paper: light-dark(#fbfaf7, #131210); --ink: light-dark(#15171c, #eeeae1); --brand: light-dark(#1d4fb0, #8db0ff); }
  body { margin: 0; background: var(--paper); color: var(--ink); font: 1rem/1.6 system-ui, sans-serif; }
  main { max-width: 40rem; margin: 0 auto; padding: 24px; }
  button { min-width: 44px; min-height: 44px; font: inherit; color: var(--ink); background: none; border: 1px solid var(--brand); border-radius: 12px; }
  :focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }
  a { color: var(--brand); }
</style>
</head>
<body>
<main>
  <h1>Readable</h1>
  <p>Body text with a <a href="#more">link inside the sentence</a>, which needs no 44 pixel box.</p>
  <button type="button">Next</button>
  <p id="more">More text.</p>
</main>
</body>
</html>
"""

BAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A page with one defect per check</title>
<style>
  body { margin: 0; background: #fff; color: #111; font: 16px/1.5 system-ui, sans-serif; }
  .wide { width: 1200px; }
  .tiny { font-size: 10px; }
  .pale { color: #bbb; }
  .cut { width: 60px; overflow: hidden; white-space: nowrap; }
  .small { width: 24px; height: 24px; outline: none; border: 0; background: #ddd; }
  .spin { width: 10px; height: 10px; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(1turn); } }
</style>
</head>
<body>
  <div class="wide">wide content</div>
  <p class="tiny">tiny text</p>
  <p class="pale">pale text</p>
  <div class="cut">a label far too long for its box</div>
  <button class="small" type="button">x</button>
  <div class="spin"></div>
  <img src="http://example.invalid/pixel.png" alt="">
  <script>
    console.error('boom');
    const loop = () => requestAnimationFrame(loop);
    loop();
  </script>
</body>
</html>
"""


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    folder = tmp_path / "pages"
    folder.mkdir()
    (folder / "good.html").write_text(GOOD, encoding="utf-8")
    (folder / "bad.html").write_text(BAD, encoding="utf-8")
    return folder


def run(
    capsys: pytest.CaptureFixture[str], *argv: str
) -> tuple[int, dict[str, object]]:
    code = check_page.main(list(argv))
    out, err = capsys.readouterr()
    line = out.strip() if code == 0 else err.strip().splitlines()[-1]
    return code, json.loads(line)


@needs_browser
def test_a_compliant_page_passes_on_phone_and_desktop(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    evidence = tmp_path / "evidence"
    code, answer = run(
        capsys,
        str(pages / "good.html"),
        "-s",
        "phone",
        "-s",
        "desktop",
        "--output-dir",
        str(evidence),
    )
    assert code == 0, answer
    assert answer["ok"] is True
    assert (evidence / "phone-light.png").is_file()
    assert (evidence / "desktop-dark.png").is_file()


@needs_browser
def test_each_defect_is_reported_with_its_check(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    evidence = tmp_path / "evidence"
    code, answer = run(
        capsys,
        str(pages / "bad.html"),
        "-s",
        "phone",
        "-s",
        "desktop",
        "--scheme",
        "light",
        "--output-dir",
        str(evidence),
    )
    assert code == 1
    errors = "\n".join(str(error) for error in answer["errors"])  # type: ignore[union-attr]
    checks = (
        "overflow",
        "small-text",
        "contrast",
        "clipped",
        "targets",
        "console",
        "network",
        "focus",
        "motion",
    )
    for check in checks:
        assert f": {check}: " in errors, check
    assert answer["evidence"] == str(evidence.resolve())


@needs_browser
def test_baseline_counts_changed_pixels(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    evidence = tmp_path / "evidence"
    code, answer = run(
        capsys,
        str(pages / "good.html"),
        "-s",
        "desktop",
        "--scheme",
        "light",
        "--baseline",
        str(pages / "bad.html"),
        "--output-dir",
        str(evidence),
    )
    assert code == 0, answer
    changed = answer["metrics"]["baseline"]["desktop"]["changed_pixels"]  # type: ignore[index]
    assert changed > 0
    assert (evidence / "baseline-desktop.png").is_file()


def test_a_missing_page_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, answer = run(capsys, "no-such-page.html")
    assert code == 2
    assert "no page at no-such-page.html" in str(answer["errors"])
