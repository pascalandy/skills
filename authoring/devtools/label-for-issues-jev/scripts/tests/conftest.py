"""Fixtures shared by the jevlabel behavior suite."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from labeltest import FakeTypeSafe, Harness


@pytest.fixture
def fake() -> Iterator[FakeTypeSafe]:
    server = FakeTypeSafe()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def harness(tmp_path: Path, fake: FakeTypeSafe) -> Harness:
    return Harness(tmp_path, fake)
