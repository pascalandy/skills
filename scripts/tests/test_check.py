"""Behavior checks for the CI verdict runner."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import check
from check import Check

FAIL = (sys.executable, "-c", "print('boom'); raise SystemExit(3)")
MARK = (sys.executable, "-c", "open('ran', 'w').close()")


class CheckTests(unittest.TestCase):
    def verdict(self, checks: list[Check], *argv: str) -> tuple[int, str, str, Path]:
        """Run main() over `checks` in a scratch root; return exit, stdout, stderr, root."""
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch.object(check, "ROOT", root),
            patch.object(check, "CHECKS", checks),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            code = check.main(list(argv))
        return code, stdout.getvalue(), stderr.getvalue(), root

    def test_a_failure_reports_its_output_and_rerun_without_stopping_later_checks(
        self,
    ) -> None:
        code, _, stderr, root = self.verdict(
            [Check("broken", FAIL, MARK), Check("later", MARK)]
        )

        self.assertEqual(code, 1)
        self.assertIn("boom", stderr)
        self.assertIn("error: broken failed; rerun: just check --only broken", stderr)
        self.assertTrue((root / "ran").exists(), "the later check must still run")

    def test_a_check_whose_package_is_absent_is_skipped(self) -> None:
        code, stdout, _, _ = self.verdict(
            [Check("public", MARK), Check("private", FAIL, requires="private/SKILL.md")]
        )

        self.assertEqual(code, 0)
        self.assertEqual(stdout, "ok: 1 passed, 1 skipped (package absent): private\n")

    def test_only_runs_the_named_checks(self) -> None:
        code, stdout, _, _ = self.verdict(
            [Check("broken", FAIL), Check("fine", MARK)], "--only", "fine"
        )

        self.assertEqual((code, stdout), (0, "ok: 1 passed\n"))


if __name__ == "__main__":
    unittest.main()
