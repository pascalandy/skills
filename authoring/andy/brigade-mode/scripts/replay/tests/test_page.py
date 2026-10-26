"""The replay page built from a recording, opened in a real browser by html-mode's check_page.py (#808)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pipeline
import pytest
import t3

HERE = Path(__file__).resolve().parent
CHECKER = "authoring/andy/html-mode/scripts/check_page.py"
# The checkout's html-mode; an installed skill has no sibling package to run
CHECK_PAGE = next((p / CHECKER for p in HERE.parents if (p / CHECKER).is_file()), None)


@pytest.mark.skipif(CHECK_PAGE is None, reason=f"no {CHECKER} above this copy")
def test_recorded_page_passes_the_browser_check(tmp_path: Path) -> None:
    data = pipeline.recording_data(
        t3.load_recording(HERE / "recordings" / "66ab.json.gz")
    )
    page = tmp_path / "replay.html"
    page.write_text(pipeline.render_page(data, {}), encoding="utf-8")
    # One desktop and one touch screen in light: the check waits a fixed time per screen
    done = subprocess.run(
        [
            "uv",
            "run",
            str(CHECK_PAGE),
            str(page),
            *("--screen", "laptop", "--screen", "phone", "--scheme", "light"),
            *("--output-dir", str(tmp_path / "evidence")),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    answer = json.loads((done.stdout or done.stderr).strip().splitlines()[-1])
    errors = answer.get("errors", [])
    if any(error.startswith("cannot start chromium") for error in errors):
        pytest.skip(
            f"Chromium is missing, so the replay page was not opened: {errors[0]}"
        )
    assert done.returncode == 0, errors
