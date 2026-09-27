"""Fleet sync through its CLI, with real git clones and SSH replaced by a local shell."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import SCRIPTS, commit

# Drops the options, runs the remote command in the host's home, and refuses
# the host named down the way ssh reports an unreachable machine.
FAKE_SSH = """#!/bin/sh
while [ "$1" = -o ]; do shift 2; done
host=${1#*@}
if [ "$host" = down ]; then
    echo "ssh: connect to host down port 22: Connection refused" >&2
    exit 255
fi
HOME="$FLEET_HOMES/$host" SHELL=/bin/sh exec /bin/sh -c "$2"
"""
FAKE_JUST = """#!/bin/sh
echo "$@" >> "$HOME/just.log"
echo "applied: fake"
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def fleet(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A control checkout, its origin, and machine homes cloned from it."""
    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True
    )
    control = tmp_path / "control"
    (control / "scripts").mkdir(parents=True)
    for name in ("_common.py", "sync_fleet.py"):
        shutil.copy2(SCRIPTS / name, control / "scripts" / name)
    (control / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    git(tmp_path, "init", "-q", "-b", "main", str(control))
    commit(control)
    git(control, "remote", "add", "origin", str(origin))
    git(control, "push", "-q", "origin", "main")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("ssh", FAKE_SSH), ("just", FAKE_JUST)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    return control, tmp_path / "homes", bin_dir


def machine(homes: Path, name: str, origin: Path) -> Path:
    checkout = homes / name / "projects/skills"
    checkout.parent.mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(checkout)], check=True)
    return checkout


def register(control: Path, *names: str) -> None:
    registry = control / "_skills_private/fleet.toml"
    registry.parent.mkdir(exist_ok=True)
    registry.write_text(
        "".join(
            f'[machines.{name}]\nssh = "tester@{name}"\npath = "projects/skills"\n\n'
            for name in names
        )
    )


def publish(control: Path) -> str:
    (control / "change.txt").write_text("published\n")
    commit(control)
    git(control, "push", "-q", "origin", "main")
    return git(control, "rev-parse", "HEAD")


def run(
    control: Path, homes: Path, bin_dir: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FLEET_HOMES"] = str(homes)
    return subprocess.run(
        ["uv", "run", str(control / "scripts/sync_fleet.py"), *args],
        check=False,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_syncs_clean_machines_and_leaves_the_rest_untouched(
    fleet: tuple[Path, Path, Path],
) -> None:
    control, homes, bin_dir = fleet
    origin = control.parent / "origin.git"
    behind = machine(homes, "behind", origin)
    dirty = machine(homes, "dirty", origin)
    (dirty / "draft.txt").write_text("work in progress\n")
    head = publish(control)
    ahead = machine(homes, "ahead", origin)
    (ahead / "local.txt").write_text("not pushed\n")
    commit(ahead)
    unpushed = git(ahead, "rev-parse", "HEAD")
    register(control, "behind", "dirty", "ahead", "down")

    result = run(control, homes, bin_dir, "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["sha"] == head
    assert report["machines"] == [
        {"machine": "behind", "status": "synced", "detail": "applied: fake"},
        {
            "machine": "dirty",
            "status": "skipped",
            "detail": "checkout has uncommitted changes",
        },
        {
            "machine": "ahead",
            "status": "skipped",
            "detail": "main has unpushed commits",
        },
        {
            "machine": "down",
            "status": "unreachable",
            "detail": "ssh: connect to host down port 22: Connection refused",
        },
    ]
    assert git(behind, "rev-parse", "HEAD") == head
    assert (homes / "behind/just.log").read_text() == "install-skills\n"
    assert git(ahead, "rev-parse", "HEAD") == unpushed
    assert not (homes / "dirty/just.log").exists()
    assert not (homes / "ahead/just.log").exists()
    assert "error: dirty skipped: checkout has uncommitted changes" in result.stderr


def test_dry_run_reports_readiness_without_moving_or_installing(
    fleet: tuple[Path, Path, Path],
) -> None:
    control, homes, bin_dir = fleet
    behind = machine(homes, "behind", control.parent / "origin.git")
    before = git(behind, "rev-parse", "HEAD")
    head = publish(control)
    register(control, "behind")

    result = run(control, homes, bin_dir, "--dry-run")

    assert result.returncode == 0
    assert result.stdout == f"1 machine ready for {head[:7]}: behind\n"
    assert git(behind, "rev-parse", "HEAD") == before
    assert not (homes / "behind/just.log").exists()
