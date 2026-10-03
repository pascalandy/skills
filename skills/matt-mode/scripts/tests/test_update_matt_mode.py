from __future__ import annotations

import sys
from pathlib import Path, PurePosixPath

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import update_matt_mode as updater

SOURCE = PurePosixPath("skills/engineering/to-spec/SKILL.md")
UPSTREAM = (
    b"---\nname: to-spec\n"
    b'description: "Turn talk into a spec: no interview."\n'
    b"disable-model-invocation: true\n---\n\n# To Spec\n"
)


def test_a_route_keeps_only_its_description_and_a_shared_skill_keeps_none() -> None:
    assert updater.strip_frontmatter(UPSTREAM, SOURCE, keep_description=True) == (
        b'---\ndescription: "Turn talk into a spec: no interview."\n---\n\n# To Spec\n'
    )
    assert updater.strip_frontmatter(UPSTREAM, SOURCE, keep_description=False) == (
        b"\n# To Spec\n"
    )


@pytest.mark.parametrize(
    "frontmatter",
    [
        b"name: to-spec\n",
        b"description:\n",
        b"description: >\n  Turn talk into a spec.\n",
        b"description: Turn talk\n  into a spec.\n",
    ],
)
def test_a_route_without_a_one_line_description_fails(frontmatter: bytes) -> None:
    content = b"---\n" + frontmatter + b"---\n# To Spec\n"
    with pytest.raises(updater.ImportError, match="needs a one-line description"):
        updater.strip_frontmatter(content, SOURCE, keep_description=True)
