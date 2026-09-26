"""Native discovery reports verified paths and unavailable adapters honestly."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "discover_skills.py"


def run(home: Path, executable: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["XDG_STATE_HOME"] = str(home / "state")
    env["UV_CACHE_DIR"] = str(home.parent / "uv-cache")
    env["PATH"] = str(executable.parent)
    return subprocess.run(
        [shutil.which("uv") or "uv", "run", str(SCRIPT), *args],
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


def test_native_opencode_discovery_and_unverified_claude(tmp_path: Path) -> None:
    home = tmp_path / "home"
    entry = home / ".config/opencode/skills/alpha/SKILL.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("# alpha\n", encoding="utf-8")
    manifest = home / "state/install-skills/manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps(
            {
                "version": 2,
                "targets": {
                    ".agents/skills": {
                        "alpha": {"source": "public", "digest": "a" * 64}
                    },
                    ".config/opencode/skills": {
                        "alpha": {"source": "public", "digest": "a" * 64}
                    },
                    ".claude/skills": {
                        "alpha": {"source": "public", "digest": "a" * 64}
                    },
                },
            }
        ),
        encoding="utf-8",
    )
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
    manifest.write_text("bad json", encoding="utf-8")
    malformed = run(home, binary, "--profile", "mac")
    assert malformed.returncode == 1
    assert malformed.stdout == ""
    assert malformed.stderr.startswith("error: cannot read manifest")
