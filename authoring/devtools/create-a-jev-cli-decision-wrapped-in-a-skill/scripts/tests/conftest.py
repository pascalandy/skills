"""Fixtures shared by the jevgate behavior suite."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from jevtest import FakeTypeSafe, Project, make_project


@pytest.fixture
def fake() -> Iterator[FakeTypeSafe]:
    server = FakeTypeSafe()
    server.start()
    yield server
    server.stop()


@pytest.fixture
def project(tmp_path: Path, fake: FakeTypeSafe) -> Project:
    return make_project(tmp_path, fake)
