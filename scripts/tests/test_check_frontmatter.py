"""Behavior checks for the skill frontmatter checker."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_frontmatter


class CheckFrontmatterTests(unittest.TestCase):
    def test_commas_inside_quoted_inline_items_keep_their_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            authoring = root / "authoring"
            skill = authoring / "devtools" / "example" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            skill.write_text(
                '---\nkeywords: ["foo, bar", "baz"]\n'
                'invalid: ["foo, bar", plain]\n---\n',
                encoding="utf-8",
            )

            with (
                patch.object(check_frontmatter, "ROOT", root),
                patch.object(check_frontmatter, "AUTHORING", authoring),
            ):
                count, errors = check_frontmatter.check()

            self.assertEqual(count, 1)
            self.assertEqual(
                errors,
                [
                    (
                        "authoring/devtools/example/SKILL.md:3: invalid "
                        "inline list string items must be double-quoted"
                    )
                ],
            )


if __name__ == "__main__":
    unittest.main()
