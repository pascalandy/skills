"""Failure recovery checks for the skill compiler."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import compile_skills

COUNT_HEAD = (
    "---\nname: skill-count\n"
    "description: How many skills authoring/ holds, by category and kind\n---\n\n"
    "<!-- Generated from authoring/ by `just compile-skills`; do not edit -->\n\n"
    "| Category | General | Dev | Unknown | Total |\n|---|---|---|---|---|\n"
)
OK = '{"ok":true}\n'
COUNT_CHANGED = ["update", "docs/references/skill-count.md"]


STALE = "skills/ or the skill count differs from authoring/; run: just compile-skills"


def failed(error: str, **fields: object) -> str:
    answer = {"ok": False, "errors": [error], **fields}
    return json.dumps(answer, separators=(",", ":")) + "\n"


def changed(*changes: list[str]) -> str:
    return (
        json.dumps({"ok": True, "changes": list(changes)}, separators=(",", ":")) + "\n"
    )


class CompileSkillsTests(unittest.TestCase):
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
            count = root / "docs/references/skill-count.md"
            count.parent.mkdir(parents=True)
            count.write_text(
                COUNT_HEAD + "| devtools | 0 | 0 | 1 | 1 |\n"
                "| **Total** | 0 | 0 | 1 | 1 |\n\nauthoring 1 · skills 1\n",
                encoding="utf-8",
            )
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
                patch.object(compile_skills, "ROOT", root),
                patch.object(compile_skills, "AUTHORING", authoring),
                patch.object(compile_skills, "OUTPUT", output),
            ):
                yield root, source, destination

    def cli(self, *argv: str) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = compile_skills.main(list(argv))
        return result, stdout.getvalue(), stderr.getvalue()

    def check(self, *, verbose: bool = False) -> tuple[int, str, str]:
        return self.cli("--check", *(["--verbose"] if verbose else []))

    def test_check_accepts_synchronized_tree_and_ignored_runtime_files(self) -> None:
        with self.repository() as (root, _, _):
            cache = root / "skills" / "example" / "__pycache__"
            cache.mkdir()
            (cache / "junk.pyc").write_bytes(b"runtime cache")
            result, stdout, stderr = self.check()

        self.assertEqual((result, stdout, stderr), (0, OK, ""))

    def test_dry_run_answers_the_changes_a_real_run_makes_then_a_rerun_has_none(
        self,
    ) -> None:
        with self.repository() as (root, source, _):
            source.write_text("# Changed\n", encoding="utf-8")
            added = root / "authoring/devtools/fresh/SKILL.md"
            added.parent.mkdir()
            added.write_text("# Fresh\n", encoding="utf-8")
            subprocess.run(["git", "add", "authoring"], cwd=root, check=True)
            lines = changed(
                ["update", "skills/example"], ["add", "skills/fresh"], COUNT_CHANGED
            )

            self.assertEqual(self.cli("-vn")[:2], (0, lines))
            self.assertEqual(
                (root / "skills/example/SKILL.md").read_text(), "# Example\n"
            )
            self.assertEqual(self.cli(), (0, lines, ""))
            self.assertEqual((root / "skills/fresh/SKILL.md").read_text(), "# Fresh\n")
            self.assertEqual(self.cli(), (0, OK, ""))

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
                self.assertIn("just compile-skills", stderr)

    def test_check_default_error_names_skill_and_fix_once(self) -> None:
        with self.repository() as (_, source, _):
            source.write_text("# Changed\n", encoding="utf-8")
            result, stdout, stderr = self.check()

        self.assertEqual((result, stdout), (1, ""))
        self.assertEqual(
            json.loads(stderr),
            {
                "ok": False,
                "errors": [STALE],
                "changes": [["update", "skills/example"]],
            },
        )

    def test_the_count_page_tallies_each_category_by_kind(self) -> None:
        with self.repository() as (root, _, _):
            for path, text in {
                "devtools/tagged": 'kind: "dev"',
                "content/writer": 'kind: "general"',
                "content/typo": 'kind: "gneral"',
                "solo": 'name: "solo"',
            }.items():
                source = root / "authoring" / path / "SKILL.md"
                source.parent.mkdir(parents=True)
                source.write_text(f"---\n{text}\n---\n", encoding="utf-8")
            subprocess.run(["git", "add", "authoring"], cwd=root, check=True)
            self.cli()
            page = (root / "docs/references/skill-count.md").read_text()

        self.assertEqual(
            page,
            COUNT_HEAD + "| content | 1 | 0 | 1 | 2 |\n"
            "| devtools | 0 | 1 | 1 | 2 |\n"
            "| (top level) | 0 | 0 | 1 | 1 |\n"
            "| **Total** | 1 | 1 | 3 | 5 |\n\nauthoring 5 · skills 5\n",
        )

    def test_a_category_move_changes_only_the_count_page(self) -> None:
        with self.repository() as (root, source, _):
            moved = root / "authoring/content/example"
            moved.parent.mkdir()
            source.parent.rename(moved)
            subprocess.run(["git", "add", "-A", "authoring"], cwd=root, check=True)

            self.assertEqual(self.cli(), (0, changed(COUNT_CHANGED), ""))
            self.assertEqual(
                (root / "docs/references/skill-count.md").read_text(),
                COUNT_HEAD + "| content | 0 | 0 | 1 | 1 |\n"
                "| **Total** | 0 | 0 | 1 | 1 |\n\nauthoring 1 · skills 1\n",
            )

    def test_check_fails_on_a_hand_edited_count_page_and_a_run_repairs_it(
        self,
    ) -> None:
        with self.repository() as (root, _, _):
            count = root / "docs/references/skill-count.md"
            expected = count.read_text()
            count.write_text(expected.replace("| 1 |", "| 9 |"))

            self.assertEqual(
                self.check(),
                (1, "", failed(STALE, changes=[COUNT_CHANGED])),
            )
            self.assertEqual(self.cli(), (0, changed(COUNT_CHANGED), ""))
            self.assertEqual(count.read_text(), expected)

    def test_check_and_a_run_agree_on_a_stray_skill_in_skills(self) -> None:
        with self.repository() as (root, _, _):
            stray = root / "skills/__pycache__/SKILL.md"
            stray.parent.mkdir()
            stray.write_text("# Stray\n", encoding="utf-8")

            self.assertEqual(self.check()[:2], (1, ""))
            self.assertEqual(self.cli(), (0, changed(COUNT_CHANGED), ""))
            self.assertTrue(
                (root / "docs/references/skill-count.md")
                .read_text()
                .endswith("\nauthoring 1 · skills 2\n")
            )
            self.assertEqual(self.check(), (0, OK, ""))

    def test_a_skill_without_a_kind_publishes_kind_unknown(self) -> None:
        untagged = '---\nname: "example"\ndescription: "Use for x."\n---\n# Example\n'
        with self.repository() as (root, source, _):
            source.write_text(untagged, encoding="utf-8")
            nested = source.parent / "sub" / "SKILL.md"
            nested.parent.mkdir()
            nested.write_text('---\nname: "sub"\n---\n', encoding="utf-8")
            tagged = root / "authoring/devtools/tagged/SKILL.md"
            tagged.parent.mkdir()
            tagged.write_text(
                '---\nname: "tagged"\nkind: "dev"\n---\n', encoding="utf-8"
            )
            crlf = root / "authoring/devtools/crlf/SKILL.md"
            crlf.parent.mkdir()
            crlf.write_bytes(b'---\r\nname: "crlf"\r\n---\r\n# Crlf\r\n')
            solo = root / "authoring/solo/SKILL.md"
            solo.parent.mkdir()
            solo.write_text('---\nname: "solo"\n---\n', encoding="utf-8")
            subprocess.run(["git", "add", "authoring"], cwd=root, check=True)

            self.assertEqual(
                self.cli(),
                (
                    0,
                    changed(
                        ["add", "skills/crlf"],
                        ["update", "skills/example"],
                        ["add", "skills/solo"],
                        ["add", "skills/tagged"],
                        COUNT_CHANGED,
                    ),
                    "",
                ),
            )
            self.assertEqual(
                (root / "skills/solo/SKILL.md").read_text(encoding="utf-8"),
                '---\nname: "solo"\nkind: "unknown"\n---\n',
            )
            self.assertEqual(
                (root / "skills/crlf/SKILL.md").read_bytes(),
                b'---\nname: "crlf"\nkind: "unknown"\n---\n# Crlf\n',
            )
            self.assertEqual(
                (root / "skills/example/SKILL.md").read_text(encoding="utf-8"),
                '---\nname: "example"\ndescription: "Use for x."\n'
                'kind: "unknown"\n---\n# Example\n',
            )
            self.assertEqual(
                (root / "skills/example/sub/SKILL.md").read_text(encoding="utf-8"),
                '---\nname: "sub"\n---\n',
            )
            self.assertEqual(
                (root / "skills/tagged/SKILL.md").read_text(encoding="utf-8"),
                '---\nname: "tagged"\nkind: "dev"\n---\n',
            )
            self.assertEqual(source.read_text(encoding="utf-8"), untagged)
            self.assertEqual(self.check(), (0, OK, ""))

    def test_a_package_inside_another_package_fails(self) -> None:
        with self.repository() as (root, _, _):
            (root / "authoring/devtools/SKILL.md").write_text("# Devtools\n")
            result = self.check()

        self.assertEqual(
            result,
            (
                1,
                "",
                failed(
                    "authoring/devtools/example is a package inside the package "
                    "authoring/devtools; move one of them"
                ),
            ),
        )

    def test_two_categories_with_the_same_skill_name_fail(self) -> None:
        with self.repository() as (root, _, _):
            twin = root / "authoring/content/example/SKILL.md"
            twin.parent.mkdir(parents=True)
            twin.write_text("# Example\n")
            result = self.check()

        self.assertEqual(
            result,
            (
                1,
                "",
                failed(
                    "duplicate skill name 'example': authoring/content/example "
                    "and authoring/devtools/example; rename one package"
                ),
            ),
        )

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
                patch.object(compile_skills, "ROOT", root),
                patch.object(compile_skills, "AUTHORING", authoring),
                patch.object(compile_skills, "OUTPUT", output),
                patch.object(Path, "rename", interrupt_after_move),
                self.assertRaises(KeyboardInterrupt),
            ):
                compile_skills.compile_tree(dry_run=False)

            self.assertEqual(
                (output / "existing.txt").read_text(encoding="utf-8"), "keep me\n"
            )


if __name__ == "__main__":
    unittest.main()
