"""Run the public CLI without mixing uv setup messages into its output."""

from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "transcript.py"


def run_script(*args: str) -> tuple[str, str, int]:
    result = subprocess.run(
        ["uv", "--quiet", "run", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return result.stdout, result.stderr, result.returncode
