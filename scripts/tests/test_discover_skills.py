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
    return subprocess.run(
        [uv, "run", str(script), *args],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
    )


def fake_opencode(binary: Path, location: Path) -> None:
    binary.write_text(
        "#!/bin/sh\n/bin/cat <<'EOF'\n"
        + json.dumps([{"name": "alpha", "location": str(location)}])
        + "\nEOF\n",
        encoding="utf-8",
    )
    binary.chmod(0o755)


def test_native_opencode_discovery_and_unverified_claude(
    sandbox: tuple[Path, Path], tmp_path: Path
) -> None:
    _, home = sandbox
    entry = home / ".config/opencode/skills/alpha/SKILL.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("# alpha\n", encoding="utf-8")
    binary = tmp_path / "bin/opencode"
    binary.parent.mkdir()
    fake_opencode(binary, entry)
    verified = run(home, binary, "--profile", "mac", "--agent", "opencode", "--json")
    assert verified.returncode == 0, verified.stderr
    assert json.loads(verified.stdout)["agents"]["opencode"]["status"] == "verified"
    shared = home / ".agents/skills/alpha/SKILL.md"
    shared.parent.mkdir(parents=True)
    shared.write_text("# stale alpha\n", encoding="utf-8")
    fake_opencode(binary, shared)
    stale = run(home, binary, "--profile", "mac", "--agent", "opencode", "--json")
    assert stale.returncode == 1
    assert json.loads(stale.stdout)["agents"]["opencode"]["missing"] == ["alpha"]
    shared.write_text("# alpha\n", encoding="utf-8")
    (entry.parent / "guide.md").write_text("current\n", encoding="utf-8")
    shared_guide = shared.parent / "guide.md"
    shared_guide.write_text("stale\n", encoding="utf-8")
    stale_package = run(
        home, binary, "--profile", "mac", "--agent", "opencode", "--json"
    )
    assert stale_package.returncode == 1
    assert json.loads(stale_package.stdout)["agents"]["opencode"]["missing"] == [
        "alpha"
    ]
    shared.unlink()
    shared.symlink_to(entry)
    stale_link = run(home, binary, "--profile", "mac", "--agent", "opencode", "--json")
    assert stale_link.returncode == 1
    assert json.loads(stale_link.stdout)["agents"]["opencode"]["missing"] == ["alpha"]
    shared.unlink()
    shared.write_text("# alpha\n", encoding="utf-8")
    shared_guide.write_text("current\n", encoding="utf-8")
    deduplicated = run(
        home, binary, "--profile", "mac", "--agent", "opencode", "--json"
    )
    assert deduplicated.returncode == 0, deduplicated.stderr
    real = home / "actual/alpha"
    real.parent.mkdir()
    entry.parent.rename(real)
    entry.parent.symlink_to(real, target_is_directory=True)
    fake_opencode(binary, real / "SKILL.md")
    linked = run(
        home,
        binary,
        "--profile",
        "mac",
        "--agent",
        "opencode",
        "--agent",
        "claude",
        "--json",
    )
    assert linked.returncode == 0
    assert json.loads(linked.stdout)["verdict"] == "partial"
    assert json.loads(linked.stdout)["agents"]["opencode"]["status"] == "verified"
    summary = run(home, binary, "--profile", "mac", "--agent", "opencode")
    assert summary.stdout == "ok: mac; opencode=verified\n"
    entry.unlink()
    missing = run(home, binary, "--profile", "mac", "--agent", "opencode", "--json")
    assert missing.returncode == 1
    assert json.loads(missing.stdout)["agents"]["opencode"]["missing"] == ["alpha"]
    unverified = run(home, binary, "--profile", "mac", "--agent", "claude", "--json")
    assert unverified.returncode == 1
    assert json.loads(unverified.stdout)["agents"]["claude"]["status"] == "unverified"
