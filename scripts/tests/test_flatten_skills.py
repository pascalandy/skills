"""Failure recovery checks for the skill flattener."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import flatten_skills


class FlattenSkillsTests(unittest.TestCase):
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
                flatten_skills.flatten()

            self.assertEqual(
                (output / "existing.txt").read_text(encoding="utf-8"), "keep me\n"
            )


if __name__ == "__main__":
    unittest.main()
