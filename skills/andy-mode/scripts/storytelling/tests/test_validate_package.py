"""Exercise package links and agent invocation through the validator CLI."""

import subprocess
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parent.parent / "validate-package.py"


def run_validator(package: Path, *options: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", str(VALIDATOR), *options, str(package)],
        capture_output=True,
        text=True,
        check=False,
    )


def make_package(
    directory: str,
    *,
    extra_frontmatter: str = "",
    codex_policy: str | None = None,
) -> Path:
    package = Path(directory) / "sample-style"
    package.mkdir()
    (package / "profile.md").write_text("# Rules\n", encoding="utf-8")
    (package / "SKILL.md").write_text(
        '---\nname: "sample-style"\n'
        'description: "Use only when invoked."\n'
        f"{extra_frontmatter}"
        "---\n[Profile](profile.md#rules)\n",
        encoding="utf-8",
    )
    if codex_policy is not None:
        agents = package / "agents"
        agents.mkdir()
        (agents / "openai.yaml").write_text(codex_policy, encoding="utf-8")
    return package


class PackageLinksTest(unittest.TestCase):
    def test_portable_links_and_local_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "sample-style"
            package.mkdir()
            (package / "profile.md").write_text("# Rules\n", encoding="utf-8")
            cases = (
                ("[Profile](profile.md#rules)", 0),
                ("[Source](https://example.com/source)", 0),
                ("[Profile](missing.md)", 2),
                ("[Profile](profile.md#missing)", 2),
                ("[Profile](../outside.md)", 2),
                ("[Profile](file:///outside/profile.md)", 2),
                ("[Profile](skill://outside/profile)", 2),
            )
            for link, expected_status in cases:
                with self.subTest(link=link):
                    (package / "SKILL.md").write_text(
                        '---\nname: "sample-style"\n'
                        'description: "Use only when invoked."\n---\n'
                        f"{link}\n",
                        encoding="utf-8",
                    )
                    result = run_validator(package)
                    self.assertEqual(
                        result.returncode,
                        expected_status,
                        result.stdout + result.stderr,
                    )
                    if expected_status:
                        self.assertIn("FAIL", result.stderr)
                    else:
                        self.assertIn("PASS sample-style", result.stdout)


class AgentInvocationTest(unittest.TestCase):
    def test_rejects_disabled_invocation(self) -> None:
        cases = (
            ("", None, 0),
            ("disable-model-invocation: true\n", None, 2),
            ("", "policy:\n  allow_implicit_invocation: false\n", 2),
        )
        for frontmatter, policy, expected_status in cases:
            with (
                self.subTest(frontmatter=frontmatter, policy=policy),
                tempfile.TemporaryDirectory() as directory,
            ):
                package = make_package(
                    directory,
                    extra_frontmatter=frontmatter,
                    codex_policy=policy,
                )
                result = run_validator(package)
                self.assertEqual(result.returncode, expected_status, result.stderr)
                if expected_status:
                    self.assertIn("agent invocation must stay enabled", result.stderr)


if __name__ == "__main__":
    unittest.main()
