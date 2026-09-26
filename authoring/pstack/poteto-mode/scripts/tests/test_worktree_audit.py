"""Exercise chat activity detection against a real temporary Git worktree."""

import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "worktree-audit.sh"


@unittest.skipUnless(shutil.which("rg"), "ripgrep is required by the audit")
class WorktreeAuditTests(unittest.TestCase):
    def test_recent_chat_with_spaces_and_unrelated_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo = root / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(
                    ["git", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            git("init", "-b", "main")
            git(
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "--allow-empty",
                "-m",
                "fixture",
            )
            git("update-ref", "refs/remotes/origin/main", "HEAD")
            worktree = root / "candidate"
            git("worktree", "add", "-b", "candidate", str(worktree))
            chats = root / "chats"
            chats.mkdir()
            old = chats / "old chat.jsonl"
            old.write_text(f'{{"cwd":"{worktree}"}}\n')
            old_time = time.time() - 10 * 86400
            os.utime(old, (old_time, old_time))
            unrelated = chats / "unrelated.jsonl"
            unrelated.write_text(f'{{"cwd":"{worktree}-other"}}\n')

            def audit():
                result = subprocess.run(
                    ["bash", str(SCRIPT), str(repo), str(chats)],
                    check=True,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "GH_HOST": "invalid.example", "GH_TOKEN": ""},
                    timeout=15,
                )
                return dict(
                    zip(
                        result.stdout.splitlines()[0].split("\t"),
                        result.stdout.splitlines()[1].split("\t"),
                    )
                )

            before = audit()
            self.assertEqual(
                before["LAST_CHAT"], time.strftime("%Y-%m-%d", time.localtime(old_time))
            )
            self.assertEqual(before["BUCKET"], "safe")
            recent = chats / "new chat with spaces.jsonl"
            recent.write_text(f'{{"file":"{worktree}/file.txt"}}\n')
            after = audit()
            self.assertEqual(
                after["LAST_CHAT"],
                time.strftime("%Y-%m-%d", time.localtime(recent.stat().st_mtime)),
            )
            self.assertEqual(after["BUCKET"], "verify-recent-chat")


if __name__ == "__main__":
    unittest.main()
