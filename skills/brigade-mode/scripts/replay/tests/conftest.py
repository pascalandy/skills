"""Shared module path and browser fixture for the replay and live page tests."""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from playwright.sync_api import Browser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def chromium() -> Iterator[Browser]:
    sync_api = pytest.importorskip("playwright.sync_api")
    executable = os.environ.get("CHECK_PAGE_BROWSER") or next(
        (
            p
            for p in map(
                shutil.which, ("chromium", "chromium-browser", "google-chrome")
            )
            if p
        ),
        None,
    )
    with sync_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(executable_path=executable)
        except sync_api.Error as error:
            first = str(error).strip().splitlines()[0]
            pytest.skip(
                f"Chromium is missing, so the live page was not opened: {first}; run: uv run --with playwright==1.63.0 playwright install chromium"
            )
        yield browser
        browser.close()
