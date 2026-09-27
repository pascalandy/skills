"""Keep every authored skill available for agent invocation."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (ROOT / "authoring", ROOT / "_skills_private")

HIDDEN = re.compile(r"^disable-model-invocation:\s*true\s*$", re.MULTILINE)
CODEX_HIDDEN = re.compile(r"^\s*allow_implicit_invocation:\s*false\s*$", re.MULTILINE)


def packages() -> dict[str, Path]:
    """Map each skill name to its outermost package directory."""
    found: dict[str, Path] = {}
    for source in SOURCES:
        for entry in sorted(source.rglob("SKILL.md")):
            package = entry.parent
            if any(
                (parent / "SKILL.md").is_file()
                for parent in package.parents
                if source in parent.parents
            ):
                continue
            found[package.name] = package
    return found


def frontmatter(package: Path) -> str:
    text = (package / "SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, re.DOTALL)
    if match is None:
        raise AssertionError(f"{package / 'SKILL.md'}: missing frontmatter")
    return match.group(1)


def codex_policy(package: Path) -> str:
    policy = package / "agents" / "openai.yaml"
    return policy.read_text(encoding="utf-8") if policy.is_file() else ""


class SkillInvocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packages = packages()

    def test_all_skills_remain_agent_invocable(self) -> None:
        self.assertTrue(self.packages, "no authored skills found")
        for name, package in sorted(self.packages.items()):
            with self.subTest(name=name):
                self.assertNotRegex(frontmatter(package), HIDDEN)
                self.assertNotRegex(codex_policy(package), CODEX_HIDDEN)


if __name__ == "__main__":
    unittest.main()
