"""Exercise the audit's buckets against a real temporary Git worktree."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "worktree-audit.sh"


def candidate(root):
    """A repo whose main is merged, and its worktree on the branch candidate."""
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
    return repo, worktree


@unittest.skipUnless(shutil.which("rg"), "ripgrep is required by the audit")
class WorktreeAuditTests(unittest.TestCase):
    def audit(self, repo, chats, worktree, **env):
        """The audit's one row; the real gh fails unless a test puts a fake first on PATH."""
        result = subprocess.run(
            ["bash", str(SCRIPT), str(repo), str(chats)],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "GH_HOST": "invalid.example", "GH_TOKEN": "", **env},
            timeout=15,
        )
        self.assertEqual(result.stderr, "")
        answer = json.loads(result.stdout)
        self.assertIs(answer["ok"], True)
        [row] = answer["worktrees"]
        self.assertEqual(row["worktree"], str(worktree))
        return row

    def test_recent_chat_with_spaces_and_unrelated_prefix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo, worktree = candidate(root)
            chats = root / "chats"
            chats.mkdir()
            old = chats / "old chat.jsonl"
            old.write_text(f'{{"cwd":"{worktree}"}}\n')
            old_time = time.time() - 10 * 86400
            os.utime(old, (old_time, old_time))
            unrelated = chats / "unrelated.jsonl"
            unrelated.write_text(f'{{"cwd":"{worktree}-other"}}\n')

            before = self.audit(repo, chats, worktree)
            self.assertEqual(
                before["lastChat"], time.strftime("%Y-%m-%d", time.localtime(old_time))
            )
            self.assertIs(before["merged"], True)
            self.assertEqual(before["bucket"], "safe")
            recent = chats / "new chat with spaces.jsonl"
            recent.write_text(f'{{"file":"{worktree}/file.txt"}}\n')
            after = self.audit(repo, chats, worktree)
            self.assertEqual(
                after["lastChat"],
                time.strftime("%Y-%m-%d", time.localtime(recent.stat().st_mtime)),
            )
            self.assertEqual(after["bucket"], "verify-recent-chat")
            (worktree / "draft.txt").write_text("draft\n")
            subprocess.run(["git", "-C", str(worktree), "add", "draft.txt"], check=True)
            self.assertEqual(self.audit(repo, chats, worktree)["bucket"], "hold-wip")

    def test_open_pr_holds_the_worktree(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            repo, worktree = candidate(root)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            gh = bin_dir / "gh"
            gh.write_text(
                '#!/bin/sh\n[ "$1 $2" = "pr list" ] || exit 1\n'
                'echo \'[{"number":7,"state":"OPEN","baseRefName":"main",'
                '"headRefName":"candidate","headRefOid":"0"}]\'\n'
            )
            gh.chmod(0o755)
            row = self.audit(
                repo,
                root / "chats",
                worktree,
                PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            )
            self.assertEqual(row["pr"], "#7/OPEN")
            self.assertEqual(row["bucket"], "hold-open-pr")

    def test_failures_answer_on_stderr(self):
        with tempfile.TemporaryDirectory() as directory:
            cases = [
                (["--typo"], 2, "worktree-audit.sh --help"),
                ([directory], 1, None),
            ]
            for args, code, hint in cases:
                result = subprocess.run(
                    ["bash", str(SCRIPT), *args],
                    check=False,
                    capture_output=True,
                    text=True,
                    env={
                        **os.environ,
                        "GIT_CEILING_DIRECTORIES": str(Path(directory).parent),
                    },
                    cwd=directory,
                    timeout=15,
                )
                self.assertEqual(result.returncode, code)
                self.assertEqual(result.stdout, "")
                answer = json.loads(result.stderr.splitlines()[-1])
                self.assertIs(answer["ok"], False)
                self.assertEqual(len(answer["errors"]), 1)
                self.assertEqual(answer.get("help"), hint)


if __name__ == "__main__":
    unittest.main()
