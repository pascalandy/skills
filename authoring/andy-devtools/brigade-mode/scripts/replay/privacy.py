"""The privacy check every page and recording passes before it leaves the machine."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

LOCAL_PATH = re.compile(
    r"/home/|/Users/|[A-Za-z]:[\\/]Users[\\/]|~[\\/]|\.worktrees",
    re.IGNORECASE,
)


def strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)


def leaks(data: Any, private: Iterable[str]) -> list[str]:
    """Strings in `data` that name a private repository or hold a local path.

    `private` holds owner/name repository names; the bare name matches too, as
    a whole word only: a private repository named "do" must not match "todo".
    """
    names = {name for repo in private for name in (repo, repo.rsplit("/", 1)[-1])}
    private_name = re.compile(
        "|".join(rf"(?<![\w.-]){re.escape(name)}(?![\w.-])" for name in names)
        or "(?!)",
        re.IGNORECASE,
    )
    home = str(Path.home()).casefold()
    return [
        value
        for value in strings(data)
        if private_name.search(value)
        or LOCAL_PATH.search(value)
        or home in value.casefold()
    ]
