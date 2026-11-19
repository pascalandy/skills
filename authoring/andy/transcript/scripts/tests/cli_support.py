"""Run the public CLI without mixing uv setup messages into its output."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT_PATH = Path(__file__).parent.parent / "transcript.py"


def run_script(*args: str) -> tuple[str, str, int]:
    cache = subprocess.check_output(["uv", "cache", "dir"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="transcript-test-home-") as home:
        # The machine's fnox would read a store the empty home lacks and fail; this
        # one lists an empty vault, so YouTube runs anonymously as in-process tests do
        stub = Path(home) / "bin"
        stub.mkdir()
        (stub / "fnox").write_text("#!/bin/sh\nexit 0\n")
        (stub / "fnox").chmod(0o755)
        path = f"{stub}{os.pathsep}{os.environ.get('PATH', '')}"
        result = subprocess.run(
            ["uv", "--quiet", "run", str(SCRIPT_PATH), *args],
            env={**os.environ, "HOME": home, "UV_CACHE_DIR": cache, "PATH": path},
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    return result.stdout, result.stderr, result.returncode
