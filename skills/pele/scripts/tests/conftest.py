"""Fixtures shared by the pele script tests."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

PELE = "pele@1.6.0"


@pytest.fixture(scope="session")
def project(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A folder with pele installed, as a project that uses it would have; pnpm downloads it once."""
    if shutil.which("pnpm") is None:
        pytest.fail(
            "pnpm not found; install it, then rerun: https://pnpm.io/installation"
        )
    folder = tmp_path_factory.mktemp("project")
    subprocess.run(["pnpm", "add", PELE], cwd=folder, check=True, capture_output=True)
    return folder
