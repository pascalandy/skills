"""End-to-end tests: check_page.py run on real pages in a real browser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_page


@pytest.fixture(scope="session")
def browser_ready() -> None:
    try:
        with check_page.sync_playwright() as playwright:
            check_page.launch(playwright, "chromium").close()
    except check_page.ScriptError as error:
        pytest.fail(str(error))


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
  .pin:focus-visible { outline: none; }
  .pin:focus-visible .ring { stroke: var(--brand); stroke-width: 3; }
  label { display: flex; align-items: center; min-height: 44px; padding: 0 24px; }
</style>
</head>
<body>
<main>
  <h1>Readable</h1>
  <p>Body text with a <a href="#more">link inside the sentence</a>, which needs no 44 pixel box.</p>
  <button type="button">Next</button>
  <label><input type="checkbox"> Wrapped checkbox</label>
  <input id="choice" type="radio" name="choice"><label for="choice">Linked radio</label>
  <p tabindex="0" style="font-size: 12px; line-height: 1.5">Focusable reading text.</p>
  <svg width="320" height="80" viewBox="0 0 320 80">
    <g class="pin" role="button" tabindex="0" aria-label="First stop">
      <circle class="ring" cx="30" cy="40" r="24" fill="transparent"/>
      <circle cx="30" cy="40" r="8" fill="currentColor"/>
      <text x="150" y="46" fill="currentColor">A label far to the right</text>
    </g>
    <text x="300" y="10" transform="rotate(90 300 10)" fill="currentColor">Rotated</text>
    <text x="70" y="8" transform="scale(1 2)" font-size="8" fill="currentColor">Stretched</text>
  </svg>
  <p id="more">More text.</p>
  <details>
    <summary style="min-height: 44px">Optional details</summary>
    <p style="font-size: 10px; color: #bbb">Hidden detail text.</p>
    <span style="display: contents; font-size: 10px; color: #bbb">Hidden boxless detail text.</span>
    <button type="button">Hidden detail button</button>
  </details>
  <details inert style="opacity: 0">
    <summary style="font-size: 10px; color: #bbb">Hidden summary text.</summary>
  </details>
  <div style="display: contents; background: #111"><p>Visible through a boxless parent.</p></div>
  <div style="display: contents">Direct text in a boxless parent.</div>
  <div hidden><span style="display: contents; font-size: 10px">Hidden boxless text</span></div>
  <div style="opacity: 0"><span style="display: contents; font-size: 10px">Transparent boxless text</span></div>
  <span style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); font-size: 10px; color: #bbb">Visually hidden text</span>
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
  html { scroll-behavior: smooth; }
  body { margin: 0; background: #fff; color: #111; font: 16px/1.5 system-ui, sans-serif; }
  .wide { width: 1200px; }
  .tiny { font-size: 10px; }
  .pale { color: #bbb; }
  .cut { width: 60px; overflow: hidden; white-space: nowrap; }
  .cut-y { height: 24px; overflow: hidden; }
  .small { width: 24px; height: 24px; margin-top: 4000px; outline: none; border: 0; background: #ddd; }
  .spin { width: 10px; height: 10px; animation: spin 1s linear infinite; }
  @keyframes spin { to { transform: rotate(1turn); } }
</style>
</head>
<body>
  <div class="wide">wide content</div>
  <p class="tiny">tiny text</p>
  <div style="display: contents"><p class="tiny">tiny boxless text</p></div>
  <div style="display: contents; font-size: 10px">tiny direct boxless text</div>
  <div class="pale" style="display: contents">pale direct boxless text</div>
  <div style="visibility: hidden; background: #000"><p class="pale" style="visibility: visible">visible child text</p></div>
  <p>repeated label</p>
  <p class="pale">repeated label</p>
  <p style="opacity: .1">faded text</p>
  <div style="background: #000; opacity: .5"><p style="color: #fff">grouped text</p></div>
  <div class="cut"><span>a label far too long for its box</span></div>
  <div class="cut-y">First line<br>Second line clipped below the box</div>
  <svg width="100" height="40"><text x="10" y="30" transform="scale(1 .5)">compressed text</text></svg>
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

# Focus shows in light only: a dark-mode run must catch it
LIGHT_FOCUS = GOOD.replace(
    ":focus-visible { outline: 3px solid var(--brand); outline-offset: 2px; }",
    ":focus-visible { outline: none; }"
    " @media (prefers-color-scheme: light) { :focus-visible { outline: 3px solid var(--brand); } }",
)
LONGER = GOOD.replace("</main>", '<div style="height: 900px"></div></main>')
DARK_MOTION = GOOD.replace(
    "</style>",
    "@media (prefers-color-scheme: dark) { h1 { animation: fade 60s linear; } }"
    " @keyframes fade { to { transform: translateX(5px); } }</style>",
)
LATE_EVENTS = GOOD.replace(
    "</body>",
    "<script>document.querySelector('button').addEventListener('focus', () => {"
    "console.error('focus broke');"
    "const image = new Image(); image.src = 'http://example.invalid/focus.png';"
    "new WebSocket('ws://example.invalid/focus');"
    "});</script></body>",
)


@pytest.fixture
def pages(tmp_path: Path) -> Path:
    folder = tmp_path / "pages"
    folder.mkdir()
    for name, html in (
        ("good", GOOD),
        ("bad", BAD),
        ("light-focus", LIGHT_FOCUS),
        ("longer", LONGER),
        ("dark-motion", DARK_MOTION),
        ("late-events", LATE_EVENTS),
    ):
        (folder / f"{name}.html").write_text(html, encoding="utf-8")
    return folder


def run(
    capsys: pytest.CaptureFixture[str], *argv: str
) -> tuple[int, dict[str, object]]:
    code = check_page.main(list(argv))
    out, err = capsys.readouterr()
    line = out.strip() if code == 0 else err.strip().splitlines()[-1]
    return code, json.loads(line)


def errors_of(answer: dict[str, object]) -> str:
    return "\n".join(str(error) for error in answer["errors"])  # type: ignore[union-attr]


@pytest.mark.usefixtures("browser_ready")
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


@pytest.mark.usefixtures("browser_ready")
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
    errors = errors_of(answer)
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
    assert '"repeated label" at' in errors, "a pale copy of a repeated label"
    assert '"faded text" at' in errors, "text faded by opacity"
    assert '"grouped text" at' in errors, "text in a half-transparent panel"
    assert "clipped: div.cut" in errors, "text clipped inside a nested span"
    assert "clipped: div.cut-y" in errors, "text clipped below its box"
    assert "infinite CSS animations running at rest" in errors
    assert "animation frames in 2 s at rest" in errors
    assert '"tiny boxless text" at 10.0px' in errors
    assert '"tiny direct boxless text" at 10.0px' in errors
    assert '"pale direct boxless text" at' in errors
    assert '"compressed text" at 8.0px' in errors
    assert '"visible child text" at' in errors
    assert "targets: button.small" in errors
    assert answer["evidence"] == str(evidence.resolve())


@pytest.mark.usefixtures("browser_ready")
def test_a_phone_only_run_still_checks_focus_and_motion(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    code, answer = run(
        capsys,
        str(pages / "bad.html"),
        "-s",
        "phone",
        "--scheme",
        "light",
        "--output-dir",
        str(tmp_path / "evidence"),
    )
    assert code == 1
    assert "phone/light: focus: " in errors_of(answer)
    assert "phone/light: motion: " in errors_of(answer)


@pytest.mark.usefixtures("browser_ready")
def test_focus_is_checked_in_dark_mode(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    code, answer = run(
        capsys,
        str(pages / "light-focus.html"),
        "-s",
        "desktop",
        "--scheme",
        "dark",
        "--output-dir",
        str(tmp_path / "evidence"),
    )
    assert code == 1
    assert "desktop/dark: focus: " in errors_of(answer)
    code, answer = run(
        capsys,
        str(pages / "light-focus.html"),
        "-s",
        "desktop",
        "--scheme",
        "light",
        "--output-dir",
        str(tmp_path / "evidence-light"),
    )
    assert code == 0, answer


@pytest.mark.usefixtures("browser_ready")
def test_baseline_counts_a_region_present_in_one_version_only(
    capsys: pytest.CaptureFixture[str], pages: Path, tmp_path: Path
) -> None:
    evidence = tmp_path / "evidence"
    code, answer = run(
        capsys,
        str(pages / "good.html"),
        "-s",
        "desktop",
        "--scheme",
        "both",
        "--baseline",
        str(pages / "longer.html"),
        "--output-dir",
        str(evidence),
    )
    assert code == 0, answer
    for scheme in ("light", "dark"):
        measured = answer["metrics"]["baseline"][f"desktop/{scheme}"]  # type: ignore[index]
        assert measured["heights"][0] > measured["heights"][1]
        assert measured["changed_pixels"] > 0
        assert (evidence / f"baseline-desktop-{scheme}.png").is_file()


@pytest.mark.usefixtures("browser_ready")
@pytest.mark.parametrize(
    ("name", "expected"),
    (
        (
            "dark-motion",
            ("desktop/dark/reduced-motion: motion: ", "CSS animations running at rest"),
        ),
        (
            "late-events",
            (
                "console: focus broke",
                "network: http://example.invalid/focus.png",
                "network: ws://example.invalid/focus",
            ),
        ),
    ),
)
def test_dark_motion_and_late_interaction_events_are_reported(
    capsys: pytest.CaptureFixture[str],
    pages: Path,
    tmp_path: Path,
    name: str,
    expected: tuple[str, ...],
) -> None:
    code, answer = run(
        capsys,
        str(pages / f"{name}.html"),
        "-s",
        "desktop",
        "--scheme",
        "dark",
        "--output-dir",
        str(tmp_path / name),
    )
    assert code == 1, answer
    errors = errors_of(answer)
    for finding in expected:
        assert finding in errors


def test_a_missing_page_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    code, answer = run(capsys, "no-such-page.html")
    assert code == 2
    assert "no page at no-such-page.html" in str(answer["errors"])
