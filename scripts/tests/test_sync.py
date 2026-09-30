"""Published local sync through its CLI and real isolated Git repositories."""

from __future__ import annotations

import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from conftest import GIT_IDENTITY, commit, private_remote, skill


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def run(
    repo: Path, home: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", str(repo / "scripts/_launch_sync.py"), "sync", *args],
        cwd=repo,
        check=False,
        env={
            **os.environ,
            **GIT_IDENTITY,
            "HOME": str(home),
            "UV_CACHE_DIR": str(home.parent / "uv-cache"),
            **(env or {}),
        },
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture
def deployed(sandbox: tuple[Path, Path], tmp_path: Path) -> tuple[Path, Path, Path]:
    seed, home = sandbox
    git(seed, "branch", "-M", "main")
    origin = tmp_path / "skills.git"
    git(tmp_path, "clone", "-q", "--bare", str(seed), str(origin))
    private_remote(tmp_path)
    repo = tmp_path / "machine"
    git(tmp_path, "clone", "-q", str(origin), str(repo))
    return repo, home, seed


@pytest.mark.parametrize("linked", [False, True])
def test_sync_preserves_authoring_and_installs_published_skills_and_private_edits(
    deployed: tuple[Path, Path, Path], linked: bool
) -> None:
    repo, home, seed = deployed
    skill(seed / "authoring/content", "alpha", "published")
    skill(seed / "skills", "alpha", "published")
    (seed / "authoring/commands").mkdir(parents=True)
    (seed / "authoring/commands/hello.md").write_text("published command\n")
    commit(seed)
    git(seed, "push", "-q", str(repo.parent / "skills.git"), "main")
    git(repo, "switch", "-c", "feature")
    (repo / "authoring/content/alpha/SKILL.md").write_text("local draft\n")
    (repo / "skills/alpha/SKILL.md").write_text("local generated draft\n")
    (repo / "authoring/commands").mkdir(exist_ok=True)
    (repo / "authoring/commands/hello.md").write_text("untracked hello\n")
    skill(repo / "authoring/content", "new", "local only")
    git(repo, "add", "skills/alpha/SKILL.md")
    before = (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "status", "--porcelain", "-uall"),
    )
    git(repo, "clone", "-q", str(repo.parent / "skills-private.git"), "_skills_private")
    skill(repo / "_skills_private/content", "mine", "unsaved")
    launcher = repo
    if linked:
        launcher = repo.parent / "linked"
        git(repo, "worktree", "add", "-q", "-b", "task", str(launcher))
        skill(launcher / "authoring/content", "linked-draft", "not published")
    launcher_before = (
        git(launcher, "rev-parse", "HEAD"),
        git(launcher, "status", "--porcelain", "-uall"),
    )

    result = run(launcher, home)

    assert (result.returncode, result.stderr) == (0, "")
    assert (
        home / ".claude/skills/alpha/SKILL.md"
    ).read_text() == "# alpha\n\npublished\n"
    assert (home / ".claude/skills/mine/SKILL.md").read_text() == "# mine\n\nunsaved\n"
    assert (home / ".claude/commands/hello.md").read_text() == "published command\n"
    assert not (home / ".claude/skills/new").exists()
    assert (
        git(repo, "rev-parse", "HEAD"),
        git(repo, "status", "--porcelain", "-uall"),
    ) == before
    assert git(repo, "branch", "--show-current") == "feature"
    assert (
        git(launcher, "rev-parse", "HEAD"),
        git(launcher, "status", "--porcelain", "-uall"),
    ) == launcher_before
    if linked:
        assert not (launcher / "_skills_private").exists()
    assert run(repo, home).stdout == ""
    assert run(repo, home, "--check").returncode == 0
    cache = repo / ".git/published-deployment"
    assert run(cache, home, "--author-root", str(repo)).returncode == 0
    assert not (cache / "_skills_private").exists()
    assert git(repo / "_skills_private", "status", "--porcelain") == ""


def test_launcher_executes_newer_published_installer_code_without_upgrading_authoring(
    deployed: tuple[Path, Path, Path],
) -> None:
    repo, home, seed = deployed
    assert run(repo, home).returncode == 0
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()
    original = (repo / "scripts/install_skills.py").read_bytes()
    (repo / "scripts/sync.py").write_text(
        'raise SystemExit("unfinished launcher draft")\n'
    )
    new_installer = seed / "scripts/install_skills.py"
    text = new_installer.read_text()
    assert '"mac": frozenset(),' in text
    new_installer.write_text(
        text.replace('"mac": frozenset(),', '"mac": frozenset({"alpha"}),').replace(
            '"om1": frozenset({"apple-mail"})',
            '"om1": frozenset({"apple-mail", "alpha"})',
        )
    )
    commit(seed)
    git(seed, "push", "-q", str(repo.parent / "skills.git"), "main")
    author_head = git(repo, "rev-parse", "HEAD")
    result = run(repo, home)
    assert result.returncode == 0, result.stderr
    assert "remove\t~/.claude/skills/alpha" in result.stdout
    assert not (home / ".claude/skills/alpha").exists()
    assert (repo / "scripts/install_skills.py").read_bytes() == original
    assert git(repo, "rev-parse", "HEAD") == author_head


def test_detached_authoring_head_stays_detached_after_sync(
    deployed: tuple[Path, Path, Path],
) -> None:
    repo, home, _ = deployed
    git(repo, "switch", "--detach")
    before = git(repo, "rev-parse", "HEAD")
    result = run(repo, home)
    assert result.returncode == 0, result.stderr
    assert (home / ".claude/skills/alpha/SKILL.md").read_text() == "# alpha\n\nold\n"
    assert git(repo, "rev-parse", "HEAD") == before
    assert git(repo, "branch", "--show-current") == ""


def test_preview_and_check_compare_published_content_without_writing_installs(
    deployed: tuple[Path, Path, Path],
) -> None:
    repo, home, _ = deployed
    before = git(repo, "status", "--porcelain", "-uall")
    preview = run(repo, home, "--dry-run")
    check = run(repo, home, "--check")
    assert preview.returncode == 0 and "add\t~/.claude/skills/alpha" in preview.stdout
    assert check.returncode == 1 and "add\t~/.claude/skills/alpha" in check.stderr
    assert not (home / ".claude").exists()
    assert git(repo, "status", "--porcelain", "-uall") == before


def test_overlapping_local_syncs_pin_the_source_until_install_finishes(
    deployed: tuple[Path, Path, Path], tmp_path: Path
) -> None:
    repo, home, seed = deployed
    marker = tmp_path / "private-started"
    resume = tmp_path / "resume"
    private = seed / "scripts/sync_private.py"
    private.write_text(
        private.read_text().replace(
            'if __name__ == "__main__":\n',
            'if __name__ == "__main__":\n'
            "    import os, time\n"
            '    if os.environ.get("SYNC_TEST_PAUSE"):\n'
            '        Path(os.environ["SYNC_TEST_PAUSE"]).touch()\n'
            '        while not Path(os.environ["SYNC_TEST_RESUME"]).exists():\n'
            "            time.sleep(0.05)\n",
        ),
        encoding="utf-8",
    )
    commit(seed)
    git(seed, "push", "-q", str(repo.parent / "skills.git"), "main")
    before = git(repo, "rev-parse", "HEAD")
    with ThreadPoolExecutor(max_workers=2) as pool:
        older = pool.submit(
            run,
            repo,
            home,
            env={"SYNC_TEST_PAUSE": str(marker), "SYNC_TEST_RESUME": str(resume)},
        )
        try:
            deadline = time.monotonic() + 20
            while not marker.exists():
                assert not older.done(), older.result().stderr if older.done() else ""
                assert time.monotonic() < deadline, (
                    "older sync did not reach private save"
                )
                time.sleep(0.05)
            skill(seed / "authoring/content", "alpha", "new")
            skill(seed / "skills", "alpha", "new")
            commit(seed)
            newest = git(seed, "rev-parse", "HEAD")
            git(seed, "push", "-q", str(repo.parent / "skills.git"), "main")
            newer = pool.submit(run, repo, home)
            deadline = time.monotonic() + 20
            while git(repo, "rev-parse", "refs/remotes/origin/main") != newest:
                assert time.monotonic() < deadline, "newer sync did not fetch main"
                time.sleep(0.05)
            with pytest.raises(TimeoutError):
                newer.result(timeout=2)
        finally:
            resume.touch()
        previous = older.result(timeout=30)
        latest = newer.result(timeout=30)
    assert previous.returncode == 0, previous.stderr
    assert latest.returncode == 0, latest.stderr
    assert (home / ".claude/skills/alpha/SKILL.md").read_text() == "# alpha\n\nnew\n"
    assert git(repo, "rev-parse", "HEAD") == before


def test_missing_origin_is_failure_without_install(sandbox: tuple[Path, Path]) -> None:
    repo, home = sandbox
    result = run(repo, home)
    assert result.returncode == 1 and "could not fetch main" in result.stderr
    assert not (home / ".claude").exists()
