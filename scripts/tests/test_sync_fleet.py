"""Fleet sync through its CLI, with real git clones and SSH replaced by a local shell."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import sync_fleet
from _cli import TemporaryError
from conftest import GIT_IDENTITY, SCRIPTS, commit, private_remote, skill

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
if [ "$host" = locked ]; then
    echo "tester@locked: Permission denied (publickey)." >&2
    exit 255
fi
# flaky answers its first call, then drops the connection partway through
if [ "$host" = flaky ]; then
    calls="$FLEET_HOMES/flaky.calls"
    echo call >> "$calls"
    if [ "$(wc -l < "$calls")" -gt 1 ]; then
        echo "private - missing"
        echo "Connection to flaky closed by remote host." >&2
        exit 255
    fi
fi
cd "$FLEET_HOMES/$host" || exit 255
shell=${FLEET_TEST_SHELL:-/bin/sh}
HOME="$FLEET_HOMES/$host" SHELL="$shell" exec "$shell" -c "$*"
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
        "_launch_sync.py",
        "_published_checkout.py",
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
    hub: Path,
    homes: Path,
    bin_dir: Path,
    *args: str,
    stdin: str = "",
    mode: str = "fleet",
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_IDENTITY}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FLEET_HOMES"] = str(homes)
    env["FLEET_PYTHON"] = sys.executable
    env["HOME"] = str(hub.parent / "hub-home")
    env.pop("XDG_STATE_HOME", None)
    result = subprocess.run(
        ["uv", "run", str(hub / "scripts/_launch_sync.py"), mode, *args],
        check=False,
        cwd=hub,
        env=env,
        input=stdin,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result


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
        ("dirty", "synced", f"synced at {head[:7]}"),
        ("editor", "synced", f"synced at {head[:7]}"),
        ("branch", "synced", f"synced at {head[:7]}"),
        ("ahead", "synced", f"synced at {head[:7]}"),
        ("plain", "needs-you", not_a_clone),
        ("linked", "needs-you", not_a_clone),
        (
            "down",
            "offline",
            "ssh: connect to host down port 22: Connection refused",
        ),
    ]
    assert git(behind, "rev-parse", "HEAD") == before
    assert git(editor, "rev-parse", "HEAD") == before
    assert (editor / ".vscode/settings.json").read_text() == "{}\n"
    assert git(origin, "rev-parse", "main") == head
    assert not (behind / "unpushed.txt").exists()
    assert git(private, "show", "main:content/secret/SKILL.md") == "from the hub"
    assert git(private, "show", "main:content/mine/SKILL.md") == "# mine\n\nold"
    assert git(hub / "_skills_private", "status", "--porcelain") == ""
    assert not (behind / REGISTRY).exists()
    assert not (homes / "behind/just.log").exists()
    installed = homes / "behind/.claude/skills/secret/SKILL.md"
    assert installed.read_text() == "from the hub\n"
    assert (homes / "editor/.claude/skills/mine/SKILL.md").is_file()
    for name, checkout in (("dirty", dirty), ("branch", branch), ("ahead", ahead)):
        assert (checkout / "_skills_private/.git").is_dir()
        assert not (homes / name / "just.log").exists()
        assert git(checkout, "rev-parse", "HEAD") != head
    assert git(dirty, "rev-parse", "HEAD") == before
    assert kept.read_text() == "# kept\n\nold\n"
    assert not (plain / "_skills_private/.git").exists()
    for name, checkout in (("plain", plain), ("linked", linked)):
        assert git(checkout, "rev-parse", "HEAD") == before
        assert not (homes / name / "just.log").exists()
    assert (
        dirty / "authoring/content/draft/SKILL.md"
    ).read_text() == "# draft\n\nold\n"
    assert (
        branch / "authoring/content/alpha/SKILL.md"
    ).read_text() == "# alpha\n\nold\n"
    assert git(branch, "branch", "--show-current") == "feature"
    assert (ahead / "local.txt").read_text() == "only here\n"
    assert any(error.startswith("down offline:") for error in report["errors"])
    behind_changes = report["machines"][0]["changes"]
    assert behind_changes[0] == f"move - to {head[:7]}"
    assert "add\t~/.claude/skills/secret" in behind_changes


def test_dry_run_refreshes_code_without_touching_authoring_or_installs(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "skills.git"
    behind = machine(homes, "behind", origin)
    current = machine(homes, "current", origin)
    stale = machine(homes, "stale", origin)
    register(hub, "behind", "current", "stale")
    assert run(hub, homes, bin_dir).returncode == 0
    head = change(hub)
    before = git(behind, "rev-parse", "HEAD")
    for checkout in (current, stale):
        git(checkout, "pull", "-q")
    # stale is at GitHub's main, but lost an installed skill
    shutil.rmtree(homes / "stale/.claude/skills/alpha")

    result = run(hub, homes, bin_dir, "-n")
    preview = json.loads(run(hub, homes, bin_dir, "-n", "--json").stdout)

    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        f"ready\tbehind\t{head[:7]}\nready\tcurrent\t{head[:7]}\nready\tstale\t{head[:7]}\n",
        "",
    )
    assert preview["machines"][2]["changes"] == [
        "~/.claude/skills has 1 of 2 current (add 1)"
    ]
    assert git(behind, "rev-parse", "HEAD") == before
    assert not (homes / "stale/.claude/skills/alpha").exists()

    # A sync first saves this machine's private edits, which every machine pulls
    (hub / "_skills_private/content/secret/SKILL.md").write_text("edited\n")
    saving = run(hub, homes, bin_dir, "-n")

    assert (saving.returncode, saving.stderr) == (0, "")
    assert saving.stdout == "".join(
        f"ready\t{name}\t{head[:7]}\n" for name in ("behind", "current", "stale")
    )
    assert git(hub / "_skills_private", "status", "--porcelain") != ""


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
    assert lagging_error.startswith(
        "error: lagging drift: published checkout is behind "
    )
    assert lagging_error.count("private repo has uncommitted edits") == 1
    assert f", GitHub at {github[:7]}" in lagging_error
    assert "~/.claude/skills has 1 of 2 current (update 1)" in lagging_error
    assert synced_error.startswith(
        f"error: synced drift: private repo is at {git(hub / '_skills_private', 'rev-parse', 'HEAD')[:7]}, "
        f"GitHub at {github[:7]}"
    )
    assert git(synced, "rev-parse", "HEAD") != git(hub, "rev-parse", "HEAD")


def test_hooks_skip_other_branches_and_sync_the_fleet_once_a_push_lands(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    behind = machine(homes, "behind", hub.parent / "skills.git")
    before = git(behind, "rev-parse", "HEAD")
    here = socket.gethostname().split(".")[0].lower()
    register(hub, "behind", here)
    home = hub.parent / "hub-home"
    (home / "projects").mkdir(parents=True)
    (home / "projects/skills").symlink_to(hub)
    fleet_log = home / ".local/state/skills-sync/fleet.log"

    git(hub, "switch", "-q", "-c", "feature")
    assert run(hub, homes, bin_dir, "post-merge", mode="hook").returncode == 0
    git(hub, "switch", "-q", "main")
    amended = run(hub, homes, bin_dir, "post-rewrite", "amend", mode="hook")
    assert amended.returncode == 0
    assert not (home / ".local/state").exists()
    assert not (home / ".claude").exists()

    head = change(hub, push=False)
    refs = f"refs/heads/main {head} refs/heads/main {before}\n"
    pushing = run(hub, homes, bin_dir, "pre-push", mode="hook", stdin=refs)
    assert (pushing.returncode, pushing.stdout, pushing.stderr) == (0, "", "")
    git(hub, "push", "-q", "origin", "main")

    deadline = time.monotonic() + 90
    while not all(
        f"{name}: synced" in (fleet_log.read_text() if fleet_log.exists() else "")
        for name in ("behind", here)
    ):
        assert time.monotonic() < deadline, "background sync did not finish: " + (
            fleet_log.read_text() if fleet_log.exists() else "no log"
        )
        time.sleep(0.2)
    assert git(behind, "rev-parse", "HEAD") == before != head
    assert git(behind / ".git/published-deployment", "rev-parse", "HEAD") == head
    assert git(hub / ".git/published-deployment", "rev-parse", "HEAD") == head
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()


@pytest.mark.parametrize("owned", [True, False], ids=["dirty", "unregistered"])
def test_hooks_warn_without_blocking_git_when_the_published_cache_is_unsafe(
    fleet: tuple[Path, Path, Path], owned: bool
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "target")
    cache = hub / ".git/published-deployment"
    if owned:
        git(hub, "worktree", "add", "-q", "--detach", str(cache))
        problem = f"published worktree {cache} has edits; inspect them"
    else:
        shutil.copytree(hub / "scripts", cache / "scripts")
        problem = f"{cache} is not the owned worktree; move it aside"
    (cache / "stray.txt").write_text("unsaved\n")
    head = git(hub, "rev-parse", "HEAD")
    refs = f"refs/heads/main {head} refs/heads/main {head}\n"

    pushing = run(hub, homes, bin_dir, "pre-push", mode="hook", stdin=refs)
    syncing = run(hub, homes, bin_dir)

    assert (pushing.returncode, pushing.stdout, pushing.stderr) == (
        0,
        "",
        f"warning: {problem}; the fleet does not sync\n",
    )
    assert not (hub.parent / "hub-home/.local/state").exists()
    assert (syncing.returncode, syncing.stdout, syncing.stderr) == (
        1,
        "",
        f"error: {problem}\n",
    )
    assert (cache / "stray.txt").read_text() == "unsaved\n"


def test_hooks_warn_without_blocking_git_when_the_registry_is_missing(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet

    result = run(hub, homes, bin_dir, "post-merge", mode="hook")

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
    assert git(hub, "rev-parse", "HEAD") == before != github
    assert git(hub / ".git/published-deployment", "rev-parse", "HEAD") == github
    assert not (home / "just.log").exists()
    assert (home / ".claude/skills/secret/SKILL.md").is_file()


@pytest.mark.parametrize("initiating", [False, True])
def test_private_conflict_stays_saved_while_another_machine_continues(
    fleet: tuple[Path, Path, Path], initiating: bool
) -> None:
    hub, homes, bin_dir = fleet
    name = socket.gethostname().split(".")[0] if initiating else "conflict"
    conflict = hub if initiating else machine(homes, name, hub.parent / "skills.git")
    if initiating:
        source_home = hub.parent / "hub-home/projects"
        source_home.mkdir(parents=True)
        (source_home / "skills").symlink_to(hub)
    machine(homes, "good", hub.parent / "skills.git")
    register(hub, name, "good")
    assert run(hub, homes, bin_dir).returncode == 0
    (conflict / "_skills_private/content/secret/SKILL.md").write_text(
        "local unsaved edit\n"
    )
    other = hub.parent / "other-private"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills-private.git"), str(other))
    (other / "content/secret/SKILL.md").write_text("remote competing edit\n")
    commit(other)
    git(other, "push", "-q", "origin", "main")
    result = run(hub, homes, bin_dir, "--json")
    assert result.returncode == 1
    outcomes = {
        entry["machine"]: entry["status"]
        for entry in json.loads(result.stderr)["machines"]
    }
    assert outcomes == {name: "failed", "good": "synced"}
    assert "private edits" in result.stderr
    assert git(conflict / "_skills_private", "status", "--porcelain") == ""
    assert "local unsaved edit" in git(
        conflict / "_skills_private", "show", "HEAD:content/secret/SKILL.md"
    )
    assert (
        homes / "good/.claude/skills/secret/SKILL.md"
    ).read_text() == "remote competing edit\n"


@pytest.mark.parametrize("linked", [False, True])
def test_cached_dispatch_survives_old_authoring_and_reuses_original_private_clone(
    fleet: tuple[Path, Path, Path], linked: bool
) -> None:
    hub, homes, bin_dir = fleet
    target = machine(homes, "target", hub.parent / "skills.git")
    register(hub, "target")
    assert run(hub, homes, bin_dir).returncode == 0
    git(target, "switch", "-q", "-c", "old-tooling")
    (target / "scripts/sync_fleet.py").write_text(
        'raise SystemExit("old authoring launcher must not run")\n'
    )
    git(target, "rm", "-q", "scripts/_published_checkout.py")
    commit(target)
    before = git(target, "rev-parse", "HEAD")
    head = change(hub)
    (hub / "_skills_private/content/secret/SKILL.md").write_text("from original\n")
    launcher = hub
    if linked:
        launcher = hub.parent / "linked"
        git(hub, "worktree", "add", "-q", "-b", "task", str(launcher))

    result = run(launcher, homes, bin_dir)

    assert result.returncode == 0, result.stderr
    assert (
        homes / "target/.claude/skills/secret/SKILL.md"
    ).read_text() == "from original\n"
    assert git(target / ".git/published-deployment", "rev-parse", "HEAD") == head
    assert git(target, "rev-parse", "HEAD") == before
    assert git(target, "branch", "--show-current") == "old-tooling"
    if linked:
        assert not (launcher / "_skills_private").exists()
    checked = run(launcher, homes, bin_dir, "--check")
    assert (checked.returncode, checked.stdout, checked.stderr) == (0, "", "")


def test_published_deletion_removes_owned_copies_but_keeps_private_and_foreign(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "target", hub.parent / "skills.git")
    register(hub, "target")
    skill(hub / "authoring/content", "retired", "published")
    skill(hub / "skills", "retired", "published")
    commands = hub / "authoring/commands"
    commands.mkdir()
    (commands / "farewell.md").write_text("published command\n")
    commit(hub)
    git(hub, "push", "-q", "origin", "main")
    assert run(hub, homes, bin_dir).returncode == 0
    foreign = skill(homes / "target/.claude/skills", "foreign")
    assert (homes / "target/.claude/skills/retired/SKILL.md").is_file()
    assert (homes / "target/.claude/commands/farewell.md").is_file()
    git(
        hub,
        "rm",
        "-qr",
        "authoring/content/retired",
        "skills/retired",
        "authoring/commands/farewell.md",
    )
    commit(hub)
    git(hub, "push", "-q", "origin", "main")
    assert run(hub, homes, bin_dir).returncode == 0
    assert not (homes / "target/.claude/skills/retired").exists()
    assert not (homes / "target/.claude/commands/farewell.md").exists()
    assert (homes / "target/.claude/skills/secret/SKILL.md").is_file()
    assert (foreign / "SKILL.md").is_file()


@pytest.mark.parametrize("preview", [False, True])
def test_unknown_deployment_path_is_not_deleted_and_other_machine_continues(
    fleet: tuple[Path, Path, Path], preview: bool
) -> None:
    hub, homes, bin_dir = fleet
    blocked = machine(homes, "blocked", hub.parent / "skills.git")
    good = machine(homes, "good", hub.parent / "skills.git")
    marker = blocked / ".git/published-deployment/keep.txt"
    marker.parent.mkdir()
    marker.write_text("unknown path\n")
    cached_script = marker.parent / "scripts/sync_fleet.py"
    cached_script.parent.mkdir()
    cached_script.write_text('raise RuntimeError("UNKNOWN_CACHE_EXECUTED")\n')
    register(hub, "blocked", "good")
    change(hub)
    result = run(hub, homes, bin_dir, "--json", *(["--dry-run"] if preview else []))
    assert result.returncode == 1
    outcomes = {
        entry["machine"]: entry["status"]
        for entry in json.loads(result.stderr)["machines"]
    }
    assert outcomes == {"blocked": "failed", "good": "ready" if preview else "synced"}
    assert marker.read_text() == "unknown path\n"
    assert "UNKNOWN_CACHE_EXECUTED" not in result.stderr
    assert "is not the owned worktree; move it aside" in result.stderr
    assert (good / ".git/published-deployment/skills/alpha/SKILL.md").is_file()


def test_remote_cache_edits_are_rejected_before_executing_published_code(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    target = machine(homes, "target", hub.parent / "skills.git")
    register(hub, "target")
    assert run(hub, homes, bin_dir).returncode == 0
    cache = target / ".git/published-deployment"
    cached_script = cache / "scripts/sync_fleet.py"
    cached_script.write_text('raise RuntimeError("DIRTY_CACHE_EXECUTED")\n')

    result = run(hub, homes, bin_dir, "--json")

    assert result.returncode == 1
    [outcome] = json.loads(result.stderr)["machines"]
    assert (outcome["status"], outcome["detail"]) == (
        "failed",
        f"published worktree {cache} has edits; inspect them",
    )
    assert cached_script.read_text() == 'raise RuntimeError("DIRTY_CACHE_EXECUTED")\n'


def test_deleted_owned_deployment_worktree_recovers_without_touching_authoring(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    remote = machine(homes, "target", hub.parent / "skills.git")
    register(hub, "target")
    assert run(hub, homes, bin_dir).returncode == 0
    cache = remote / ".git/published-deployment"
    published_sha = git(cache, "rev-parse", "HEAD")
    original_sha = git(remote, "rev-parse", "HEAD")
    shutil.rmtree(cache)
    assert run(hub, homes, bin_dir).returncode == 0
    assert git(cache, "rev-parse", "HEAD") == published_sha
    assert git(remote, "rev-parse", "HEAD") == original_sha


def test_cached_newer_published_revision_does_not_roll_back_on_stale_remote(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    remote = machine(homes, "target", hub.parent / "skills.git")
    register(hub, "target")
    assert run(hub, homes, bin_dir).returncode == 0
    old = git(hub, "rev-parse", "HEAD")
    skill(hub / "authoring/content", "alpha", "new published")
    skill(hub / "skills", "alpha", "new published")
    new = change(hub)
    assert run(hub, homes, bin_dir).returncode == 0
    cache = remote / ".git/published-deployment"
    assert git(cache, "rev-parse", "HEAD") == new
    older = run(hub, homes, bin_dir, "--machine-step", "apply", "--revision", old)
    assert older.returncode == 0 and f"deployment {new}" in older.stdout
    assert git(cache, "rev-parse", "HEAD") == new
    git(hub, "push", "-q", "--force", "origin", f"{old}:main")
    assert run(hub, homes, bin_dir).returncode == 0
    assert run(hub, homes, bin_dir, "--check").returncode == 0
    assert git(cache, "rev-parse", "HEAD") == new
    assert git(remote, "rev-parse", "HEAD") == old
    assert (
        homes / "target/.claude/skills/alpha/SKILL.md"
    ).read_text() == "# alpha\n\nnew published\n"


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
    assert "down offline:" in result.stderr


def test_an_unknown_machine_is_a_usage_error(fleet: tuple[Path, Path, Path]) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "mbp")

    result = run(hub, homes, bin_dir, "mpb")

    assert (result.returncode, result.stdout) == (2, "")
    assert "error: unknown machine mpb; the registry lists mbp\n" in result.stderr
    assert result.stderr.endswith("run 'just sync-fleet --help'\n")


def test_a_machine_that_refuses_the_login_is_a_failure_not_a_retry(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "down", "locked")

    result = run(hub, homes, bin_dir, "--dry-run", "--json")

    assert (result.returncode, result.stdout) == (1, "")
    outcomes = {m["machine"]: m for m in json.loads(result.stderr)["machines"]}
    assert (outcomes["down"]["status"], outcomes["down"]["temporary"]) == (
        "offline",
        True,
    )
    assert outcomes["locked"] == {
        "machine": "locked",
        "status": "failed",
        "detail": "tester@locked: Permission denied (publickey).",
        "targets": [],
        "changes": [],
        "temporary": False,
        "sha": "",
    }


def test_a_check_that_loses_the_machine_midway_exits_75(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "flaky", hub.parent / "skills.git")
    register(hub, "flaky")

    result = run(hub, homes, bin_dir, "--check")

    assert (result.returncode, result.stdout) == (75, "")
    assert (
        "error: flaky offline: Connection to flaky closed by remote host.; "
        in result.stderr
    )


def test_a_fetch_that_times_out_without_a_known_main_exits_75(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def slow(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired("git fetch", sync_fleet.TIMEOUT)

    monkeypatch.setattr(sync_fleet, "call", slow)
    monkeypatch.setattr(
        sync_fleet, "git", lambda *args: subprocess.CompletedProcess(args, 1, "", "")
    )

    with pytest.raises(TemporaryError, match="git fetch took longer than 600s"):
        sync_fleet.github_main()


def test_a_failed_install_step_reports_the_installers_own_error(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "broken", hub.parent / "skills.git")
    # A file where the agent directories go makes the installer fail
    (homes / "broken/.config").write_text("not a directory\n")
    register(hub, "broken")

    result = run(hub, homes, bin_dir, "--check", "--json")

    assert (result.returncode, result.stdout) == (1, "")
    [outcome] = json.loads(result.stderr)["machines"]
    assert outcome["status"] == "failed"
    assert "has a file ancestor" in outcome["detail"]


def test_an_interrupt_kills_a_group_whose_leader_exits_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sync_fleet, "GRACE", 0.3)
    monkeypatch.setattr(sync_fleet, "STOPPING", threading.Event())
    ready = tmp_path / "ready"
    # The leader exits on SIGTERM; its child ignores it and keeps the pipes open
    script = (
        f'(trap "" TERM; exec sleep 30) &\ntrap "exit 0" TERM\n: > "{ready}"\nwait\n'
    )
    done: list[subprocess.CompletedProcess[str]] = []
    worker = threading.Thread(
        target=lambda: done.append(sync_fleet.call(["sh", "-c", script]))
    )
    worker.start()
    deadline = time.monotonic() + 10
    while not ready.exists():
        assert time.monotonic() < deadline, "the step never started"
        time.sleep(0.02)

    sync_fleet.stop_children()
    worker.join(timeout=5)

    assert not worker.is_alive(), "a descendant kept the worker waiting"
    assert done[0].returncode == 0
