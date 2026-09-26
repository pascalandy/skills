"""Pin the invocation mode of skills whose routing must not drift.

Add a skill here when a routing decision about it should survive later edits.
`writing-great-skills` owns the rules; these lists record the decisions.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCES = (ROOT / "authoring", ROOT / "_skills_private")

# The agent may load these from a matching request
MODEL_INVOKED = {
    "architect",
    "automate-me",
    "blast-radius",
    "handoff",
    "interrogate",
    "maintain-verification-skill",
    "make-bot-ui",
    "show-me-your-work",
    "teach",
    "technical-writing",
    "typescript-best-practices",
    "why",
}

# Model-invoked skills whose triggers describe the user's intent
INTENT_TRIGGERS = {"automate-me", "interrogate", "teach"}

# These run only when named; every `principle-*` skill joins them
USER_INVOKED = {
    "arena",
    "bro",
    "create-verification-skill",
    "game-theory-corpus",
    "matt-mode",
    "meta-sc",
    "no-comments",
    "pa-great-books",
    "qmd",
    "recall",
    "reflect",
    "swarm",
    "think",
    "tdd",
}

# Codex reads `agents/openai.yaml` instead of `disable-model-invocation`
CODEX_USER_INVOKED = {
    "game-theory-corpus",
    "illustration",
    "matt-mode",
    "meta-sc",
    "storytelling",
    "think",
}

# Kept in the ignored `_skills_private/` tree, so a clone may lack them
PRIVATE = {"game-theory-corpus", "pa-great-books"}

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


def description(package: Path) -> str:
    match = re.search(r'^description: "(.+)"$', frontmatter(package), re.MULTILINE)
    if match is None:
        raise AssertionError(f"{package / 'SKILL.md'}: missing description")
    return match.group(1)


def codex_policy(package: Path) -> str:
    policy = package / "agents" / "openai.yaml"
    return policy.read_text(encoding="utf-8") if policy.is_file() else ""


class SkillInvocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.packages = packages()

    def package(self, name: str) -> Path:
        if name in self.packages:
            return self.packages[name]
        if name in PRIVATE:
            self.skipTest(f"private {name} is absent")
        self.fail(f"pinned skill {name} is missing")

    def test_model_invoked_skills_stay_reachable(self) -> None:
        for name in sorted(MODEL_INVOKED):
            with self.subTest(name=name):
                package = self.package(name)
                self.assertNotRegex(frontmatter(package), HIDDEN)
                self.assertNotRegex(codex_policy(package), CODEX_HIDDEN)
                self.assertRegex(description(package), r"^Use (?:for|when) ")

    def test_intent_triggers_do_not_ask_for_explicit_invocation(self) -> None:
        for name in sorted(INTENT_TRIGGERS):
            with self.subTest(name=name):
                self.assertNotRegex(
                    description(self.package(name)),
                    r"\bexplicit(?:ly)?\b|\binvokes?\b",
                )

    def test_user_invoked_skills_stay_hidden(self) -> None:
        principles = {name for name in self.packages if name.startswith("principle-")}
        self.assertTrue(principles, "no principle-* skills found")
        for name in sorted(USER_INVOKED | principles):
            with self.subTest(name=name):
                self.assertRegex(frontmatter(self.package(name)), HIDDEN)

    def test_codex_user_invoked_skills_stay_hidden(self) -> None:
        for name in sorted(CODEX_USER_INVOKED):
            with self.subTest(name=name):
                self.assertRegex(codex_policy(self.package(name)), CODEX_HIDDEN)


if __name__ == "__main__":
    unittest.main()
