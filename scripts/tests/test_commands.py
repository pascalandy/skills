"""Keep every shared command expanding the same way in each agent that installs it."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from test_skill_invocation import packages

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = ROOT / "commands"

# Pi and OpenCode read `$2` in `$2nd-pass` as the second argument, so the agent
# receives `nd-pass`; Claude Code leaves it alone, which hides the break there
GLUED_ARGUMENT = re.compile(r"\$\d+[^\W\d]")


class CommandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.commands = sorted(COMMANDS.glob("*.md"))

    def test_no_word_starts_with_a_positional_argument(self) -> None:
        self.assertTrue(self.commands, "no commands found")
        glued = [
            f"{path.name}:{number}: {match.group()}"
            for path in self.commands
            for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            )
            for match in GLUED_ARGUMENT.finditer(line)
        ]
        self.assertEqual(glued, [])

    def test_no_command_shares_a_skill_name(self) -> None:
        # Claude Code hides a command behind a skill of the same name
        names = {path.stem for path in self.commands}
        self.assertEqual(sorted(names & packages().keys()), [])


if __name__ == "__main__":
    unittest.main()
