"""Fleet sync through its CLI, with real git clones and SSH replaced by a local shell."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from conftest import SCRIPTS, commit, skill

# Drops the options, runs the remote command in the host's home, and refuses
# the host named down the way ssh reports an unreachable machine. git and
# rsync use it too, through GIT_SSH_COMMAND and rsync -e.
FAKE_SSH = """#!/bin/sh
while [ $# -gt 0 ]; do
    case "$1" in
        -o | -l | -p) shift 2 ;;
        -*) shift ;;
        *) break ;;
    esac
done
host=${1#*@}
shift
if [ "$host" = down ]; then
    echo "ssh: connect to host down port 22: Connection refused" >&2
    exit 255
fi
cd "$FLEET_HOMES/$host" || exit 255
HOME="$FLEET_HOMES/$host" SHELL=/bin/sh exec /bin/sh -c "$*"
"""
# Logs the recipe, then runs the machine's real installer like the justfile.
FAKE_JUST = """#!/bin/sh
echo "$@" >> "$HOME/just.log"
shift
exec "$FLEET_PYTHON" scripts/install_skills.py "$@"
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def fleet(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A hub checkout with a private tree, its origin, and a fake ssh and just."""
    origin = tmp_path / "origin.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True
    )
    hub = tmp_path / "hub"
    (hub / "scripts").mkdir(parents=True)
    for name in (
        "_common.py",
        "flatten_skills.py",
        "install_skills.py",
        "sync_fleet.py",
    ):
        shutil.copy2(SCRIPTS / name, hub / "scripts" / name)
    (hub / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    skill(hub / "authoring/content", "alpha")
    skill(hub / "skills", "alpha")
    git(tmp_path, "init", "-q", "-b", "main", str(hub))
    commit(hub)
    git(hub, "remote", "add", "origin", str(origin))
    git(hub, "push", "-q", "origin", "main")
    skill(hub / "_skills_private/content", "secret")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("ssh", FAKE_SSH), ("just", FAKE_JUST)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    return hub, tmp_path / "homes", bin_dir


def machine(homes: Path, name: str, origin: Path) -> Path:
    checkout = homes / name / "projects/skills"
    checkout.parent.mkdir(parents=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(checkout)], check=True)
    return checkout


def register(hub: Path, *names: str) -> None:
    (hub / "_skills_private/fleet.toml").write_text(
        "".join(
            f'[machines.{name}]\nssh = "tester@{name}"\npath = "projects/skills"\n\n'
            for name in names
        )
    )


def change(hub: Path, name: str = "change.txt") -> str:
    """Commit on the hub without pushing, so only the hub can deliver it."""
    (hub / name).write_text("new\n")
    commit(hub)
    return git(hub, "rev-parse", "HEAD")


def run(
    hub: Path, homes: Path, bin_dir: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FLEET_HOMES"] = str(homes)
    env["FLEET_PYTHON"] = sys.executable
    env["HOME"] = str(hub.parent / "hub-home")
    env.pop("XDG_STATE_HOME", None)
    return subprocess.run(
        ["uv", "run", str(hub / "scripts/sync_fleet.py"), *args],
        check=False,
        cwd=hub,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_sends_the_hub_commit_and_private_tree_and_leaves_the_rest_untouched(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "origin.git"
    behind = machine(homes, "behind", origin)
    stale = behind / "_skills_private"
    retired = skill(stale / "content", "retired")
    (retired / "__pycache__").mkdir()
    dirty = machine(homes, "dirty", origin)
    skill(dirty / "authoring/content", "draft")
    editor = machine(homes, "editor", origin)
    (editor / ".vscode").mkdir()
    (editor / ".vscode/settings.json").write_text("{}\n")
    branch = machine(homes, "branch", origin)
    git(branch, "switch", "-q", "-c", "feature")
    ahead = machine(homes, "ahead", origin)
    (ahead / "local.txt").write_text("only here\n")
    commit(ahead)
    # linked has a symlinked private root before the sync; relinked gets one
    # while the push lands, after the inspection passed.
    linked = machine(homes, "linked", origin)
    relinked = machine(homes, "relinked", origin)
    for name in ("linked", "relinked"):
        (homes / name / "unrelated").mkdir()
        (homes / name / "unrelated/important.txt").write_text("keep\n")
    (linked / "_skills_private").symlink_to(homes / "linked/unrelated")
    hook = relinked / ".git/hooks/post-receive"
    hook.write_text('#!/bin/sh\nln -s "$HOME/unrelated" ../_skills_private\n')
    hook.chmod(0o755)
    before = git(dirty, "rev-parse", "HEAD")
    head = change(hub)
    register(
        hub, "behind", "dirty", "editor", "branch", "ahead", "linked", "relinked", "down"
    )

    result = run(hub, homes, bin_dir, "--json")

    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["sha"] == head
    assert [
        (entry["machine"], entry["status"], entry["detail"])
        for entry in report["machines"]
    ] == [
        ("behind", "synced", f"synced at {head[:7]}"),
        ("dirty", "needs-you", "checkout has uncommitted skill changes"),
        ("editor", "synced", f"synced at {head[:7]}"),
        ("branch", "needs-you", "checkout is on feature, not main"),
        ("ahead", "needs-you", f"checkout has commits {report['hub']} lacks"),
        *(
            (
                name,
                "needs-you",
                "~/projects/skills/_skills_private is a symlink; replace it with a folder",
            )
            for name in ("linked", "relinked")
        ),
        (
            "down",
            "offline",
            "ssh: connect to host down port 22: Connection refused",
        ),
    ]
    assert git(behind, "rev-parse", "HEAD") == head
    assert git(editor, "rev-parse", "HEAD") == head
    assert (editor / ".vscode/settings.json").read_text() == "{}\n"
    assert git(origin, "rev-parse", "main") == before
    assert (stale / "content/secret/SKILL.md").is_file()
    assert not retired.exists()
    assert not (stale / "fleet.toml").exists()
    assert (homes / "behind/just.log").read_text() == "install-skills --quiet\n"
    assert (homes / "behind/.claude/skills/secret/SKILL.md").is_file()
    for name, checkout in (("dirty", dirty), ("branch", branch), ("ahead", ahead)):
        assert not (checkout / "_skills_private").exists()
        assert not (homes / name / "just.log").exists()
    assert git(dirty, "rev-parse", "HEAD") == before
    for name, checkout in (("linked", linked), ("relinked", relinked)):
        unrelated = homes / name / "unrelated"
        assert [path.name for path in unrelated.iterdir()] == ["important.txt"]
        assert (checkout / "_skills_private").is_symlink()
        assert git(checkout, "rev-parse", "HEAD") == before
        assert not (homes / name / "just.log").exists()
    assert (
        "error: dirty needs-you: checkout has uncommitted skill changes; "
        "fix it on dirty, then rerun just sync-fleet dirty"
    ) in result.stderr
    assert "error: down offline:" in result.stderr


def test_dry_run_is_silent_and_changes_nothing(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    behind = machine(homes, "behind", hub.parent / "origin.git")
    before = git(behind, "rev-parse", "HEAD")
    change(hub)
    register(hub, "behind")

    result = run(hub, homes, bin_dir, "--dry-run")

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert git(behind, "rev-parse", "HEAD") == before
    assert not (behind / "_skills_private").exists()
    assert not (homes / "behind/just.log").exists()


def test_check_is_silent_when_converged_and_names_each_difference(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "origin.git"
    synced = machine(homes, "synced", origin)
    lagging = machine(homes, "lagging", origin)
    register(hub, "synced", "lagging")
    assert run(hub, homes, bin_dir).returncode == 0
    converged = run(hub, homes, bin_dir, "--check")
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, "", "")
    change(hub)
    assert run(hub, homes, bin_dir, "synced").returncode == 0
    (lagging / "_skills_private/content/secret/SKILL.md").write_text("edited\n")

    result = run(hub, homes, bin_dir, "--check")

    assert result.returncode == 1
    assert result.stdout == ""
    errors = [line for line in result.stderr.splitlines() if line.startswith("error:")]
    assert len(errors) == 1
    assert errors[0].startswith("error: lagging drift: checkout is behind ")
    assert "private tree differs from " in errors[0]
    assert "~/.claude/skills has 1 of 2 current (update 1)" in errors[0]
    assert git(synced, "rev-parse", "HEAD") == git(hub, "rev-parse", "HEAD")


def same_size_and_time(path: Path) -> None:
    """Rewrite the bytes but keep the size and time rsync's quick check trusts."""
    before = path.stat()
    path.write_text(path.read_text().replace("old", "new"))
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))


def executable(path: Path) -> None:
    path.chmod(0o755)


@pytest.mark.parametrize("edit", [same_size_and_time, executable])
def test_sync_repairs_the_private_drift_check_reports(
    fleet: tuple[Path, Path, Path], edit: Callable[[Path], None]
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "mac", hub.parent / "origin.git")
    register(hub, "mac")
    assert run(hub, homes, bin_dir).returncode == 0
    source = hub / "_skills_private/content/secret/SKILL.md"
    received = homes / "mac/projects/skills/_skills_private/content/secret/SKILL.md"
    # The sync does not copy times, so align them; after the edit, the size and
    # time rsync's quick check compares still match on both sides.
    times = source.stat()
    os.utime(received, ns=(times.st_atime_ns, times.st_mtime_ns))
    edit(source)
    assert (received.stat().st_size, received.stat().st_mtime_ns) == (
        source.stat().st_size,
        source.stat().st_mtime_ns,
    )

    drift = run(hub, homes, bin_dir, "--check")
    synced = run(hub, homes, bin_dir)
    converged = run(hub, homes, bin_dir, "--check")

    assert drift.returncode == 1
    assert "error: mac drift: private tree differs from " in drift.stderr
    assert (synced.returncode, synced.stderr) == (0, "")
    installed = homes / "mac/.claude/skills/secret/SKILL.md"
    assert installed.read_bytes() == source.read_bytes()
    assert os.access(installed, os.X_OK) == os.access(source, os.X_OK)
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, "", "")


def test_hook_acts_only_in_the_hub_main_checkout(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    behind = machine(homes, "behind", hub.parent / "origin.git")
    before = git(behind, "rev-parse", "HEAD")
    register(hub, "behind")
    home = hub.parent / "hub-home"
    fleet_log = home / ".local/state/skills-sync/fleet.log"

    git(hub, "switch", "-q", "-c", "feature")
    change(hub)
    assert run(hub, homes, bin_dir, "--hook", "post-commit").returncode == 0
    git(hub, "switch", "-q", "main")
    assert run(hub, homes, bin_dir, "--hook", "post-rewrite", "amend").returncode == 0
    assert not (home / ".local/state").exists()
    assert not (home / ".claude").exists()

    head = change(hub)
    result = run(hub, homes, bin_dir, "--hook", "post-commit")

    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()
    deadline = time.monotonic() + 60
    while "behind: synced" not in (fleet_log.read_text() if fleet_log.exists() else ""):
        assert time.monotonic() < deadline, "background sync did not finish"
        time.sleep(0.2)
    assert git(behind, "rev-parse", "HEAD") == head != before
