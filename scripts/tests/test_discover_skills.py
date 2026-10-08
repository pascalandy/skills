"""Native discovery reports verified paths and unavailable adapters honestly."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

GIT = Path(shutil.which("git") or "/usr/bin/git").parent


def run(home: Path, executable: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["UV_CACHE_DIR"] = str(home.parent / "uv-cache")
    # The fake agent shadows any real one; git lists the sandbox's skills.
    env["PATH"] = f"{executable.parent}{os.pathsep}{GIT}"
    script = home.parent / "repo/scripts/discover_skills.py"
    # uv sets UV to its own binary; a version manager's shim would put its own
    # tool directories, and a real agent, ahead of the fake one.
    uv = os.environ.get("UV") or shutil.which("uv") or "uv"
    result = subprocess.run(
        [uv, "run", str(script), *args],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result


OK = '{"ok":true}\n'
MISSED = (
    "opencode did not load alpha; run just install-skills --profile mac, then rerun"
)


def errors(result: subprocess.CompletedProcess[str]) -> list[str]:
    """A failed run's errors, from the answer on the last line of stderr."""
    assert (result.returncode, result.stdout) == (1, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer["ok"] is False
    return answer["errors"]


def fake_opencode(binary: Path, location: Path) -> None:
    binary.write_text(
        "#!/bin/sh\n/bin/cat <<'EOF'\n"
        + json.dumps([{"name": "alpha", "location": str(location)}])
        + "\nEOF\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)


def test_native_opencode_discovery_matches_the_installed_copy(
    sandbox: tuple[Path, Path], tmp_path: Path
) -> None:
    _, home = sandbox
    entry = home / ".config/opencode/skills/alpha/SKILL.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("# alpha\n", encoding="utf-8")
    binary = tmp_path / "bin/opencode"
    binary.parent.mkdir()
    fake_opencode(binary, entry)
    verified = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert (verified.returncode, verified.stdout, verified.stderr) == (0, OK, "")
    shared = home / ".agents/skills/alpha/SKILL.md"
    shared.parent.mkdir(parents=True)
    shared.write_text("# stale alpha\n", encoding="utf-8")
    fake_opencode(binary, shared)
    stale = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert errors(stale) == [MISSED]
    shared.write_text("# alpha\n", encoding="utf-8")
    (entry.parent / "guide.md").write_text("current\n", encoding="utf-8")
    shared_guide = shared.parent / "guide.md"
    shared_guide.write_text("stale\n", encoding="utf-8")
    stale_package = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert errors(stale_package) == [MISSED]
    shared.unlink()
    shared.symlink_to(entry)
    stale_link = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert errors(stale_link) == [MISSED]
    shared.unlink()
    shared.write_text("# alpha\n", encoding="utf-8")
    shared_guide.write_text("current\n", encoding="utf-8")
    deduplicated = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert (deduplicated.returncode, deduplicated.stdout) == (0, OK)
    real = home / "actual/alpha"
    real.parent.mkdir()
    entry.parent.rename(real)
    entry.parent.symlink_to(real, target_is_directory=True)
    fake_opencode(binary, real / "SKILL.md")
    linked = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert (linked.returncode, linked.stdout, linked.stderr) == (0, OK, "")
    entry.unlink()
    missing = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert missing.stderr == f'{{"ok":false,"errors":["{MISSED}"]}}\n'
    assert errors(missing) == [MISSED]


def test_claude_code_is_not_an_agent_it_checks(
    sandbox: tuple[Path, Path], tmp_path: Path
) -> None:
    _, home = sandbox
    home.mkdir()

    claude = run(home, tmp_path / "bin/claude", "--profile", "mac", "--agent", "claude")

    assert (claude.returncode, claude.stdout) == (2, "")
    assert "invalid choice: 'claude'" in json.loads(claude.stderr)["errors"][0]


def test_an_agent_that_times_out_exits_75(
    sandbox: tuple[Path, Path], tmp_path: Path
) -> None:
    _, home = sandbox
    home.mkdir()
    binary = tmp_path / "bin/opencode"
    binary.parent.mkdir()
    binary.write_text("#!/bin/sh\nexec /bin/sleep 30\n", encoding="utf-8")
    binary.chmod(0o755)

    slow = run(home, binary, "--profile", "mac", "--agent", "opencode", "--timeout=1s")

    assert (slow.returncode, slow.stdout) == (75, "")
    assert json.loads(slow.stderr) == {
        "ok": False,
        "errors": ["opencode: timed out after 1s; retry, or pass a longer --timeout"],
        "retry": "just skills-discover --profile mac --agent opencode --timeout=1s",
    }
