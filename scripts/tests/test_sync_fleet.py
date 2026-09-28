"""Fleet sync through its CLI, with real git clones and SSH replaced by a local shell."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from conftest import (
    GIT_IDENTITY,
    SCRIPTS,
    commit,
    exits,
    observe,
    private_remote,
    skill,
)

# Where the private-network skill ships the registry; the seed's .gitignore keeps
# it untracked, so it never reaches another machine's clone.
REGISTRY = "_skills_private/integrations/private-network/references/fleet.toml"

# Drops the options, runs the remote command in the host's home, and refuses
# the host named down the way ssh reports an unreachable machine. git uses it
# too, through GIT_SSH_COMMAND.
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
    """A hub checkout with a private clone, both origins, and a fake ssh and just."""
    origin = tmp_path / "skills.git"
    subprocess.run(
        ["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True
    )
    hub = tmp_path / "hub"
    (hub / "scripts").mkdir(parents=True)
    for name in (
        "_cli.py",
        "_common.py",
        "flatten_skills.py",
        "install_skills.py",
        "sync_fleet.py",
        "sync_private.py",
    ):
        shutil.copy2(SCRIPTS / name, hub / "scripts" / name)
    (hub / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    skill(hub / "authoring/content", "alpha")
    skill(hub / "skills", "alpha")
    git(tmp_path, "init", "-q", "-b", "main", str(hub))
    commit(hub)
    git(hub, "remote", "add", "origin", str(origin))
    git(hub, "push", "-q", "origin", "main")
    subprocess.run(
        [
            "git",
            "clone",
            "-q",
            str(private_remote(tmp_path)),
            str(hub / "_skills_private"),
        ],
        check=True,
    )
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
    (hub / REGISTRY).parent.mkdir(parents=True, exist_ok=True)
    (hub / REGISTRY).write_text(
        "".join(
            f'[machines.{name}]\nssh = "tester@{name}"\npath = "projects/skills"\n\n'
            for name in names
        )
    )


def change(hub: Path, name: str = "change.txt", push: bool = True) -> str:
    """Commit on the syncing machine and, unless told not to, push it to GitHub."""
    (hub / name).write_text("new\n")
    commit(hub)
    if push:
        git(hub, "push", "-q", "origin", "HEAD:main")
    return git(hub, "rev-parse", "HEAD")


def run(
    hub: Path, homes: Path, bin_dir: Path, *args: str, stdin: str = ""
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_IDENTITY}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FLEET_HOMES"] = str(homes)
    env["FLEET_PYTHON"] = sys.executable
    env["HOME"] = str(hub.parent / "hub-home")
    env.pop("XDG_STATE_HOME", None)
    result = subprocess.run(
        ["uv", "run", str(hub / "scripts/sync_fleet.py"), *args],
        check=False,
        cwd=hub,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=120,
    )
    observe("sync_fleet", result.returncode)
    return result


@exits("sync_fleet", 1)
def test_sends_github_main_saves_private_edits_and_leaves_the_rest_untouched(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "skills.git"
    private = hub.parent / "skills-private.git"
    behind = machine(homes, "behind", origin)
    dirty = machine(homes, "dirty", origin)
    skill(dirty / "authoring/content", "draft")
    # editor has a private skill of its own, uncommitted, and an editor setting.
    editor = machine(homes, "editor", origin)
    git(editor, "clone", "-q", str(private), "_skills_private")
    skill(editor / "_skills_private/content", "mine")
    (editor / ".vscode").mkdir()
    (editor / ".vscode/settings.json").write_text("{}\n")
    branch = machine(homes, "branch", origin)
    git(branch, "switch", "-q", "-c", "feature")
    ahead = machine(homes, "ahead", origin)
    (ahead / "local.txt").write_text("only here\n")
    commit(ahead)
    # plain holds a private folder that is not a clone; linked a symlink to one.
    plain = machine(homes, "plain", origin)
    kept = skill(plain / "_skills_private/content", "kept") / "SKILL.md"
    linked = machine(homes, "linked", origin)
    (linked / "_skills_private").symlink_to(editor / "_skills_private")
    before = git(dirty, "rev-parse", "HEAD")
    head = change(hub)
    # A commit GitHub lacks stays on the machine that made it.
    change(hub, "unpushed.txt", push=False)
    (hub / "_skills_private/content/secret/SKILL.md").write_text("from the hub\n")
    register(
        hub, "behind", "dirty", "editor", "branch", "ahead", "plain", "linked", "down"
    )

    result = run(hub, homes, bin_dir, "--json")

    assert (result.returncode, result.stdout) == (1, "")
    report = json.loads(result.stderr)
    assert report["sha"] == head
    not_a_clone = (
        "~/projects/skills/_skills_private is not a clone of the private repo; "
        "move it aside, then rerun"
    )
    assert [
        (entry["machine"], entry["status"], entry["detail"])
        for entry in report["machines"]
    ] == [
        ("behind", "synced", f"synced at {head[:7]}"),
        ("dirty", "needs-you", "checkout has uncommitted skill changes"),
        ("editor", "synced", f"synced at {head[:7]}"),
        ("branch", "needs-you", "checkout is on feature, not main"),
        ("ahead", "needs-you", "checkout has commits GitHub lacks; push them"),
        ("plain", "needs-you", not_a_clone),
        ("linked", "needs-you", not_a_clone),
        (
            "down",
            "offline",
            "ssh: connect to host down port 22: Connection refused",
        ),
    ]
    assert git(behind, "rev-parse", "HEAD") == head
    assert git(editor, "rev-parse", "HEAD") == head
    assert (editor / ".vscode/settings.json").read_text() == "{}\n"
    assert git(origin, "rev-parse", "main") == head
    assert not (behind / "unpushed.txt").exists()
    assert git(private, "show", "main:content/secret/SKILL.md") == "from the hub"
    assert git(private, "show", "main:content/mine/SKILL.md") == "# mine\n\nold"
    assert git(hub / "_skills_private", "status", "--porcelain") == ""
    assert not (behind / REGISTRY).exists()
    assert (homes / "behind/just.log").read_text() == "install-skills\n"
    installed = homes / "behind/.claude/skills/secret/SKILL.md"
    assert installed.read_text() == "from the hub\n"
    assert (homes / "editor/.claude/skills/mine/SKILL.md").is_file()
    for name, checkout in (("dirty", dirty), ("branch", branch), ("ahead", ahead)):
        assert not (checkout / "_skills_private").exists()
        assert not (homes / name / "just.log").exists()
    assert git(dirty, "rev-parse", "HEAD") == before
    assert kept.read_text() == "# kept\n\nold\n"
    assert not (plain / "_skills_private/.git").exists()
    for name, checkout in (("plain", plain), ("linked", linked)):
        assert git(checkout, "rev-parse", "HEAD") == before
        assert not (homes / name / "just.log").exists()
    assert (
        "dirty needs-you: checkout has uncommitted skill changes; "
        "fix it on dirty, then rerun just sync-fleet dirty"
    ) in report["errors"]
    assert any(error.startswith("down offline:") for error in report["errors"])
    behind_changes = report["machines"][0]["changes"]
    assert behind_changes[0] == f"move {before[:7]} to {head[:7]}"
    assert "add\t~/.claude/skills/secret" in behind_changes


@exits("sync_fleet", 0)
def test_dry_run_names_each_machine_it_would_move_and_changes_nothing(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    behind = machine(homes, "behind", hub.parent / "skills.git")
    current = machine(homes, "current", hub.parent / "skills.git")
    before = git(behind, "rev-parse", "HEAD")
    head = change(hub)
    git(current, "pull", "-q")
    register(hub, "behind", "current")

    result = run(hub, homes, bin_dir, "-n")

    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        f"ready\tbehind\t{head[:7]}\n",
        "",
    )
    assert git(behind, "rev-parse", "HEAD") == before
    assert not (behind / "_skills_private").exists()
    assert not (homes / "behind/just.log").exists()


def test_check_is_silent_when_converged_and_names_each_difference(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "skills.git"
    synced = machine(homes, "synced", origin)
    lagging = machine(homes, "lagging", origin)
    register(hub, "synced", "lagging")
    assert run(hub, homes, bin_dir).returncode == 0
    converged = run(hub, homes, bin_dir, "--check")
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, "", "")
    change(hub)
    assert run(hub, homes, bin_dir, "synced").returncode == 0
    (lagging / "_skills_private/content/secret/SKILL.md").write_text("edited\n")
    # Another machine pushed a private edit that neither has pulled yet.
    other = hub.parent / "other-private"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills-private.git"), str(other))
    (other / "notes.md").write_text("elsewhere\n")
    commit(other)
    git(other, "push", "-q", "origin", "main")
    github = git(other, "rev-parse", "HEAD")

    result = run(hub, homes, bin_dir, "--check")

    assert result.returncode == 1
    assert result.stdout == ""
    errors = sorted(
        line for line in result.stderr.splitlines() if line.startswith("error:")
    )
    assert len(errors) == 2
    lagging_error, synced_error = errors
    assert lagging_error.startswith("error: lagging drift: checkout is behind ")
    assert "private repo has uncommitted edits" in lagging_error
    assert f", GitHub at {github[:7]}" in lagging_error
    assert "~/.claude/skills has 1 of 2 current (update 1)" in lagging_error
    assert synced_error.startswith(
        f"error: synced drift: private repo is at {git(hub / '_skills_private', 'rev-parse', 'HEAD')[:7]}, "
        f"GitHub at {github[:7]}"
    )
    assert git(synced, "rev-parse", "HEAD") == git(hub, "rev-parse", "HEAD")


def test_hooks_install_on_commit_and_sync_the_fleet_once_a_push_lands(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    behind = machine(homes, "behind", hub.parent / "skills.git")
    before = git(behind, "rev-parse", "HEAD")
    register(hub, "behind")
    home = hub.parent / "hub-home"
    fleet_log = home / ".local/state/skills-sync/fleet.log"

    git(hub, "switch", "-q", "-c", "feature")
    change(hub, push=False)
    assert run(hub, homes, bin_dir, "--hook", "post-commit").returncode == 0
    git(hub, "switch", "-q", "main")
    assert run(hub, homes, bin_dir, "--hook", "post-rewrite", "amend").returncode == 0
    assert not (home / ".local/state").exists()
    assert not (home / ".claude").exists()

    head = change(hub, push=False)
    committed = run(hub, homes, bin_dir, "--hook", "post-commit")
    assert (committed.returncode, committed.stdout, committed.stderr) == (0, "", "")
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()
    assert not fleet_log.exists()

    refs = f"refs/heads/main {head} refs/heads/main {before}\n"
    pushing = run(hub, homes, bin_dir, "--hook", "pre-push", stdin=refs)
    assert (pushing.returncode, pushing.stdout, pushing.stderr) == (0, "", "")
    git(hub, "push", "-q", "origin", "main")

    deadline = time.monotonic() + 60
    while "behind: synced" not in (fleet_log.read_text() if fleet_log.exists() else ""):
        assert time.monotonic() < deadline, "background sync did not finish"
        time.sleep(0.2)
    assert git(behind, "rev-parse", "HEAD") == head != before


def test_hooks_warn_without_blocking_git_when_the_registry_is_missing(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet

    result = run(hub, homes, bin_dir, "--hook", "post-commit")

    assert result.returncode == 0
    assert "no fleet.toml" in result.stderr
    assert not (hub.parent / "hub-home/.claude").exists()


def test_brings_the_machine_it_runs_on_to_github_main(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    here = socket.gethostname().split(".")[0].lower()
    home = hub.parent / "hub-home"
    (home / "projects").mkdir(parents=True)
    (home / "projects/skills").symlink_to(hub)
    register(hub, here)
    # Another machine pushed to GitHub; this checkout has not pulled it yet.
    other = hub.parent / "other"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills.git"), str(other))
    github = change(other, "elsewhere.txt")
    before = git(hub, "rev-parse", "HEAD")

    result = run(hub, homes, bin_dir)

    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        f"synced\t{here}\t{github[:7]}\n",
        "",
    )
    assert git(hub, "rev-parse", "HEAD") == github != before
    assert (home / "just.log").read_text() == "install-skills\n"
    assert (home / ".claude/skills/secret/SKILL.md").is_file()


@exits("sync_fleet", 75)
def test_a_run_whose_only_failures_are_offline_machines_exits_75(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "down")

    result = run(hub, homes, bin_dir, "--dry-run")

    assert (result.returncode, result.stdout) == (75, "")
    assert (
        result.stderr.splitlines()[0]
        == f"offline\tdown\t{git(hub, 'rev-parse', '--short=7', 'HEAD')}"
    )
    assert result.stderr.endswith("retry: just sync-fleet --dry-run\n")


def test_an_unknown_machine_is_a_usage_error(fleet: tuple[Path, Path, Path]) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "mbp")

    result = run(hub, homes, bin_dir, "mpb")

    assert (result.returncode, result.stdout) == (2, "")
    assert "error: unknown machine mpb; the registry lists mbp\n" in result.stderr
    assert result.stderr.endswith("run 'just sync-fleet --help'\n")
