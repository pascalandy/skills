"""Release candidate checks against small git repositories."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import release_check

CHANGELOG = """# Changelog

## [0.1.0] - 2026-09-26

### Added

- Initial snapshot
"""


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=True, timeout=10
    ).stdout.strip()


class ReleaseCheckTests(unittest.TestCase):
    @contextmanager
    def repository(self, *, with_beta: bool = False) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            root.mkdir()
            git(root, "init", "-q", "-b", "main")
            git(root, "config", "user.name", "Test Agent")
            git(root, "config", "user.email", "test@example.com")
            (root / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            alpha = root / "skills" / "alpha" / "SKILL.md"
            alpha.parent.mkdir(parents=True)
            alpha.write_text("# Alpha\n", encoding="utf-8")
            if with_beta:
                beta = root / "skills" / "beta" / "SKILL.md"
                beta.parent.mkdir(parents=True)
                beta.write_text("# Beta\n", encoding="utf-8")
            git(root, "add", ".")
            git(root, "commit", "-qm", "baseline")
            git(root, "update-ref", "refs/remotes/origin/main", "HEAD")
            with patch.object(release_check, "ROOT", root):
                yield root

    def run_check(self, *args: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = release_check.main(list(args))
        return result, stdout.getvalue(), stderr.getvalue()

    def commit(self, root: Path, message: str) -> None:
        git(root, "add", "-A")
        git(root, "commit", "-qm", message)
        git(root, "update-ref", "refs/remotes/origin/main", "HEAD")

    def test_valid_first_release_with_existing_tag_at_head(self) -> None:
        with self.repository() as root:
            git(root, "tag", "v0.1.0")
            result, stdout, stderr = self.run_check("v0.1.0")

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "ok: v0.1.0: 1 skill total\n")
        self.assertEqual(stderr, "")

    def test_invalid_version(self) -> None:
        with self.repository():
            result, stdout, stderr = self.run_check("v01.0.0")

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn("error: version must be vMAJOR.MINOR.PATCH", stderr)

    def test_version_must_exceed_other_tags(self) -> None:
        with self.repository() as root:
            git(root, "tag", "v0.2.0")
            result, stdout, stderr = self.run_check("v0.1.0")

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn(
            "error: version must be greater than the latest release tag v0.2.0", stderr
        )

    def test_stray_v_tags_neither_block_nor_count_as_previous(self) -> None:
        with self.repository() as root:
            git(root, "tag", "v9.9.9-rc1")
            git(root, "tag", "vendor-x")
            result, stdout, stderr = self.run_check("v0.1.0", "--verbose")

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "ok: v0.1.0: 1 skill total\n")
        self.assertIn("ignored non-release tags: v9.9.9-rc1, vendor-x\n", stderr)

    def test_missing_duplicated_and_empty_changelog_sections(self) -> None:
        cases = {
            "missing": ("# Changelog\n", "has no [0.1.0] section"),
            "duplicated": (
                CHANGELOG + "\n## [0.1.0] - 2026-09-25\n\n- Again\n",
                "duplicate [0.1.0] sections",
            ),
            "empty": (
                "# Changelog\n\n## [0.1.0] - 2026-09-26\n\n",
                "[0.1.0] section is empty",
            ),
        }
        for name, (contents, reason) in cases.items():
            with self.subTest(name=name), self.repository() as root:
                (root / "CHANGELOG.md").write_text(contents, encoding="utf-8")
                self.commit(root, name)
                result, stdout, stderr = self.run_check("v0.1.0")
                self.assertEqual(result, 1)
                self.assertEqual(stdout, "")
                self.assertIn(reason, stderr)

    def test_branch_not_on_origin_main_still_lists_skills(self) -> None:
        with self.repository() as root:
            (root / "README.md").write_text("branch\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-qm", "branch only")
            result, stdout, stderr = self.run_check("v0.1.0", "--verbose")

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn("skills (1): alpha\n", stderr)
        self.assertIn(
            "error: HEAD is not an ancestor of origin/main; "
            "run git fetch --tags origin main",
            stderr,
        )
        self.assertEqual(stderr.count("error:"), 1)

    def test_tag_at_another_commit_fails(self) -> None:
        with self.repository() as root:
            git(root, "tag", "v0.1.0")
            (root / "README.md").write_text("later\n", encoding="utf-8")
            self.commit(root, "later commit")
            result, stdout, stderr = self.run_check("v0.1.0")

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn("error: tag v0.1.0 points to a different commit", stderr)

    def test_dirty_tree_fails_without_writing_notes(self) -> None:
        with self.repository() as root:
            notes = root.parent / "notes.md"
            (root / "untracked.txt").write_text("dirty\n", encoding="utf-8")
            result, stdout, stderr = self.run_check("v0.1.0", "--notes", str(notes))
            self.assertFalse(notes.exists())

        self.assertEqual(result, 1)
        self.assertEqual(stdout, "")
        self.assertIn("error: working tree is dirty", stderr)

    def test_notes_are_exact_section_body(self) -> None:
        with self.repository() as root:
            notes = root.parent / "notes.md"
            result, stdout, stderr = self.run_check("v0.1.0", "--notes", str(notes))
            contents = notes.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "ok: v0.1.0: 1 skill total\n")
        self.assertEqual(stderr, "")
        self.assertEqual(contents, "### Added\n\n- Initial snapshot\n")

    def test_changed_skill_summary_since_previous_tag(self) -> None:
        with self.repository(with_beta=True) as root:
            git(root, "tag", "v0.1.0")
            (root / "skills/alpha/SKILL.md").write_text(
                "# Alpha changed\n", encoding="utf-8"
            )
            (root / "skills/beta/SKILL.md").unlink()
            gamma = root / "skills/gamma/SKILL.md"
            gamma.parent.mkdir()
            gamma.write_text("# Gamma\n", encoding="utf-8")
            (root / "CHANGELOG.md").write_text(
                CHANGELOG.replace("## [0.1.0]", "## [0.1.1]"), encoding="utf-8"
            )
            self.commit(root, "change skills")
            result, stdout, stderr = self.run_check("v0.1.1", "--verbose")

        self.assertEqual(result, 0)
        self.assertEqual(stdout, "ok: v0.1.1: 1 added, 1 changed, 1 removed\n")
        self.assertIn("added (1): gamma\n", stderr)
        self.assertIn("changed (1): alpha\n", stderr)
        self.assertIn("removed (1): beta\n", stderr)


if __name__ == "__main__":
    unittest.main()
