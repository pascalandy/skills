"""Failure recovery checks for the skill flattener."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import flatten_skills


class FlattenSkillsTests(unittest.TestCase):
    @contextmanager
    def repository(self) -> Iterator[tuple[Path, Path, Path]]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authoring = root / "authoring"
            source = authoring / "devtools" / "example" / "SKILL.md"
            source.parent.mkdir(parents=True)
            source.write_text("# Example\n", encoding="utf-8")
            output = root / "skills"
            destination = output / "example" / "SKILL.md"
            destination.parent.mkdir(parents=True)
            destination.write_text("# Example\n", encoding="utf-8")
            (root / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
            subprocess.run(
                ["git", "init", "-q", str(root)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "add", "authoring", "skills", ".gitignore"],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=10,
            )
            with (
                patch.object(flatten_skills, "ROOT", root),
                patch.object(flatten_skills, "AUTHORING", authoring),
                patch.object(flatten_skills, "OUTPUT", output),
            ):
                yield root, source, destination

    def check(self, *, verbose: bool = False) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = flatten_skills.main(
                ["--check", *(["--verbose"] if verbose else [])]
            )
        return result, stdout.getvalue(), stderr.getvalue()

    def test_check_accepts_synchronized_tree_and_ignored_runtime_files(self) -> None:
        with self.repository() as (root, _, _):
            cache = root / "skills" / "example" / "__pycache__"
            cache.mkdir()
            (cache / "junk.pyc").write_bytes(b"runtime cache")
            result, stdout, stderr = self.check()

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "ok: 1 skills, 1 files match skills/\n")
        self.assertEqual(stderr, "")

    def test_check_reports_content_missing_extra_and_mode_drift(self) -> None:
        cases = {
            "content": (
                lambda root, source, destination: source.write_text("# Changed\n"),
                "changed content",
            ),
            "missing": (
                lambda root, source, destination: destination.unlink(),
                "missing file",
            ),
            "extra": (
                lambda root, source, destination: (
                    root / "skills/example/extra.md"
                ).write_text("extra\n"),
                "extra file",
            ),
            "mode": (
                lambda root, source, destination: source.chmod(0o755),
                "executable bit changed",
            ),
            "symlink": (
                lambda root, source, destination: (
                    destination.unlink(),
                    destination.symlink_to(source),
                ),
                "symlink",
            ),
        }
        for name, (change, reason) in cases.items():
            with (
                self.subTest(name=name),
                self.repository() as (root, source, destination),
            ):
                change(root, source, destination)
                result, stdout, stderr = self.check(verbose=True)
                self.assertEqual(result, 1)
                self.assertEqual(stdout, "")
                self.assertIn(reason, stderr)
                self.assertIn("just flatten-skills", stderr)

    def test_check_default_error_names_skill_and_fix_once(self) -> None:
        with self.repository() as (_, source, _):
            source.write_text("# Changed\n", encoding="utf-8")
            result, stdout, stderr = self.check()

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr.count("error:"), 1)
        self.assertIn("example; run just flatten-skills", stderr)

    def test_interrupt_after_moving_output_restores_previous_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authoring = root / "authoring"
            package = authoring / "devtools" / "example"
            package.mkdir(parents=True)
            (package / "SKILL.md").write_text("# Example\n", encoding="utf-8")

            output = root / "skills"
            output.mkdir()
            (output / "existing.txt").write_text("keep me\n", encoding="utf-8")

            subprocess.run(
                ["git", "init", "-q", str(root)],
                check=True,
                capture_output=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "add", "authoring/devtools/example/SKILL.md"],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=10,
            )

            original_rename = Path.rename

            def interrupt_after_move(path: Path, target: Path) -> Path:
                moved = original_rename(path, target)
                if path == output:
                    raise KeyboardInterrupt
                return moved

            with (
                patch.object(flatten_skills, "ROOT", root),
                patch.object(flatten_skills, "AUTHORING", authoring),
                patch.object(flatten_skills, "OUTPUT", output),
                patch.object(Path, "rename", interrupt_after_move),
                self.assertRaises(KeyboardInterrupt),
            ):
                flatten_skills.flatten(dry_run=False)

            self.assertEqual(
                (output / "existing.txt").read_text(encoding="utf-8"), "keep me\n"
            )


if __name__ == "__main__":
    unittest.main()
