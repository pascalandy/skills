"""Fixtures shared by the jevlabel behavior suite."""

from __future__ import annotations

from pathlib import Path

import pytest
from labeltest import Harness


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    return Harness(tmp_path)
