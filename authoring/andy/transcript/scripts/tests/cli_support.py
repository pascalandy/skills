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
        tools = Path(home) / "bin"
        tools.mkdir()
        fnox = tools / "fnox"
        fnox.write_text('#!/bin/sh\n[ "$1" = list ]\n')
        fnox.chmod(0o700)
        result = subprocess.run(
            ["uv", "--quiet", "run", str(SCRIPT_PATH), *args],
            env={
                **{
                    k: v
                    for k, v in os.environ.items()
                    if k not in {"FLEET_ACTIVE_MODELS", "YOUTUBE_COOKIES_TXT"}
                },
                "HOME": home,
                "PATH": f"{tools}{os.pathsep}{os.environ.get('PATH', '')}",
                "UV_CACHE_DIR": cache,
            },
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    return result.stdout, result.stderr, result.returncode
