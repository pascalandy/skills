"""Exercise package links and invocation controls through the validator CLI."""

import subprocess
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).with_name("validate-package.py")


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


class ExplicitInvocationTest(unittest.TestCase):
    def test_multiple_target_runtimes_must_all_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = make_package(
                directory,
                extra_frontmatter="disable-model-invocation: true\n",
                codex_policy="policy:\n  allow_implicit_invocation: false\n",
            )
            result = run_validator(
                package,
                "--explicit-runtime",
                "pi",
                "--explicit-runtime",
                "codex",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("explicit invocation for pi, codex", result.stdout)

    def test_pi_requires_boolean_true(self) -> None:
        cases = (
            ("disable-model-invocation: true\n", 0),
            ("", 2),
            ("disable-model-invocation: false\n", 2),
            ('disable-model-invocation: "true"\n', 2),
            ("disable-model-invocation: 1\n", 2),
        )
        for metadata, expected_status in cases:
            with (
                self.subTest(metadata=metadata),
                tempfile.TemporaryDirectory() as directory,
            ):
                package = make_package(directory, extra_frontmatter=metadata)
                result = run_validator(package, "--explicit-runtime", "pi")
                self.assertEqual(
                    result.returncode,
                    expected_status,
                    result.stdout + result.stderr,
                )
                if expected_status:
                    self.assertIn("boolean true", result.stderr)

    def test_codex_requires_boolean_false(self) -> None:
        cases = (
            ("policy:\n  allow_implicit_invocation: false\n", 0),
            (None, 2),
            ("policy: {}\n", 2),
            ("policy:\n  allow_implicit_invocation: true\n", 2),
            ('policy:\n  allow_implicit_invocation: "false"\n', 2),
            ("policy:\n  allow_implicit_invocation: 0\n", 2),
        )
        for policy, expected_status in cases:
            with (
                self.subTest(policy=policy),
                tempfile.TemporaryDirectory() as directory,
            ):
                package = make_package(directory, codex_policy=policy)
                result = run_validator(package, "--explicit-runtime", "codex")
                self.assertEqual(
                    result.returncode,
                    expected_status,
                    result.stdout + result.stderr,
                )
                if expected_status:
                    self.assertIn("boolean false", result.stderr)


if __name__ == "__main__":
    unittest.main()
