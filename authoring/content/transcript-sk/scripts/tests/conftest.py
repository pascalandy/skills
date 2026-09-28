"""Test configuration -- add scripts/ to sys.path for direct imports."""

from __future__ import annotations

import functools
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import pytest

# Add the scripts directory to sys.path so `from transcript import ...` works
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def no_real_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail an in-process test that would start yt-dlp, pi, or the keyring, or
    call Deepgram; a test that needs one replaces it first."""
    import transcript

    def refuse(command: Any, *_args: Any, **_kwargs: Any) -> Any:
        pytest.fail(f"test reached a real external boundary: {command!r}")

    monkeypatch.setattr(transcript, "run_child", refuse)
    monkeypatch.setattr(transcript.httpx, "post", refuse)


Test = TypeVar("Test", bound=Callable[..., Any])

# Exit codes each test declares with @exits, and the ones the scripts returned
DECLARED: dict[str, set[int]] = {}
OBSERVED: list[tuple[str, int]] = []


def observe(script: str, code: int) -> int:
    """Record that `script`, a file stem such as transcript, exited with `code`."""
    OBSERVED.append((script, code))
    return code


def covers(script: str, *codes: int) -> Callable[[Test], Test]:
    """Declare codes a parametrized test triggers one case at a time; each case
    asserts its own exit code, so no run needs to see them all."""

    def declare(test: Test) -> Test:
        DECLARED.setdefault(script, set()).update(codes)
        return test

    return declare


def exits(script: str, *codes: int) -> Callable[[Test], Test]:
    """Declare that the test makes `script` exit with each of `codes`.

    test_contract.py counts the declarations against each script's exit-code
    table, and the test fails unless it observed every code.
    """

    def declare(test: Test) -> Test:
        DECLARED.setdefault(script, set()).update(codes)

        @functools.wraps(test)
        def checked(*args: Any, **kwargs: Any) -> Any:
            start = len(OBSERVED)
            result = test(*args, **kwargs)
            seen = {code for name, code in OBSERVED[start:] if name == script}
            missing = sorted(set(codes) - seen)
            assert not missing, f"{script} never exited {missing} in this test"
            return result

        return cast("Test", checked)

    return declare
