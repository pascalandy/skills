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

# Where the fleet skill ships the registry, relative to the private clone
# beside a checkout; the seed's .gitignore keeps it untracked, so it never
# reaches another machine's clone.
REGISTRY = "authoring/integrations/fleet/references/fleet.toml"

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
HOME="$FLEET_HOMES/$host" SHELL=/bin/sh exec /bin/sh -c "$*"
"""
# Logs the recipe, then runs the machine's real installer like the justfile.
FAKE_JUST = """#!/bin/sh
echo "$@" >> "$HOME/just.log"
shift
# An installer from before #490 only warns about a conflict, with exit 0
if [ -n "$FLEET_OLD_INSTALLER" ]; then
    echo "WARNING:install-skills:warning: ~/.claude/skills/alpha is a symlink or file; move it aside, then rerun: just install-skills" >&2
    exit 0
fi
exec "$FLEET_PYTHON" scripts/install_skills.py "$@"
"""


def login_path(home: Path, bin_dir: Path) -> None:
    """Put the fake ssh and just first in a login shell's PATH. A login shell
    reads ~/.profile after /etc/profile, where macOS's path_helper moves the
    inherited entries behind /opt/homebrew/bin and the real just."""
    home.mkdir(parents=True, exist_ok=True)
    (home / ".profile").write_text(f'PATH="{bin_dir}:$PATH"\n')


OK = '{"ok":true}\n'


def changed(*changes: list[str]) -> str:
    return (
        json.dumps({"ok": True, "changes": list(changes)}, separators=(",", ":")) + "\n"
    )


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()


def private(checkout: Path) -> Path:
    """The private clone beside a checkout."""
    return checkout.parent / "skills-private"


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
        "compile_skills.py",
        "install_skills.py",
        "sync_fleet.py",
        "sync_private.py",
    ):
        shutil.copy2(SCRIPTS / name, hub / "scripts" / name)
    (hub / ".gitignore").write_text("__pycache__/\n")
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
            str(private(hub)),
        ],
        check=True,
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("ssh", FAKE_SSH), ("just", FAKE_JUST)):
        (bin_dir / name).write_text(body)
        (bin_dir / name).chmod(0o755)
    login_path(tmp_path / "hub-home", bin_dir)
    return hub, tmp_path / "homes", bin_dir


def machine(homes: Path, name: str, origin: Path) -> Path:
    checkout = homes / name / "projects/skills"
    checkout.parent.mkdir(parents=True)
    login_path(homes / name, homes.parent / "bin")
    subprocess.run(["git", "clone", "-q", str(origin), str(checkout)], check=True)
    return checkout


def entries(*names: str) -> str:
    return "".join(
        f'[machines.{name}]\nssh = "tester@{name}"\npath = "projects/skills"\n\n'
        for name in names
    )


def register(hub: Path, *names: str) -> None:
    registry = private(hub) / REGISTRY
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(entries(*names))


def change(hub: Path, name: str = "change.txt", push: bool = True) -> str:
    """Commit on the syncing machine and, unless told not to, push it to GitHub."""
    (hub / name).write_text("new\n")
    commit(hub)
    if push:
        git(hub, "push", "-q", "origin", "HEAD:main")
    return git(hub, "rev-parse", "HEAD")


def run(
    hub: Path, homes: Path, bin_dir: Path, *args: str, stdin: str = "", **extra: str
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, **GIT_IDENTITY, **extra}
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["FLEET_HOMES"] = str(homes)
    env["FLEET_PYTHON"] = sys.executable
    env["HOME"] = str(hub.parent / "hub-home")
    # This machine's step runs in $SHELL; sh reads the ~/.profile above
    env["SHELL"] = "/bin/sh"
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
    return result


def test_sends_github_main_and_leaves_the_rest_untouched(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "skills.git"
    remote = hub.parent / "skills-private.git"
    behind = machine(homes, "behind", origin)
    dirty = machine(homes, "dirty", origin)
    skill(dirty / "authoring/content", "draft")
    # editor has a private clone of its own and an editor setting.
    editor = machine(homes, "editor", origin)
    git(editor.parent, "clone", "-q", str(remote), "skills-private")
    (editor / ".vscode").mkdir()
    (editor / ".vscode/settings.json").write_text("{}\n")
    branch = machine(homes, "branch", origin)
    git(branch, "switch", "-q", "-c", "feature")
    ahead = machine(homes, "ahead", origin)
    (ahead / "local.txt").write_text("only here\n")
    commit(ahead)
    # plain holds a private folder that is not a clone; linked a symlink to one.
    plain = machine(homes, "plain", origin)
    kept = skill(private(plain) / "authoring/content", "kept") / "SKILL.md"
    linked = machine(homes, "linked", origin)
    private(linked).symlink_to(private(editor))
    # edited has private edits, and feature a private clone off main; a
    # private skill changes through a PR, so both stay untouched.
    edited = machine(homes, "edited", origin)
    git(edited.parent, "clone", "-q", str(remote), "skills-private")
    skill(private(edited) / "authoring/content", "mine")
    feature = machine(homes, "feature", origin)
    git(feature.parent, "clone", "-q", str(remote), "skills-private")
    git(private(feature), "switch", "-q", "-c", "feature")
    # unshared committed to its private main, which only a merged PR changes
    unshared = machine(homes, "unshared", origin)
    git(unshared.parent, "clone", "-q", str(remote), "skills-private")
    skill(private(unshared) / "authoring/content", "mine")
    commit(private(unshared))
    before = git(dirty, "rev-parse", "HEAD")
    head = change(hub)
    # A commit GitHub lacks stays on the machine that made it.
    change(hub, "unpushed.txt", push=False)
    register(
        hub,
        "behind",
        "dirty",
        "editor",
        "branch",
        "ahead",
        "plain",
        "linked",
        "edited",
        "feature",
        "unshared",
        "down",
    )

    result = run(hub, homes, bin_dir, "-v")

    assert (result.returncode, result.stdout) == (1, "")
    log = result.stderr.splitlines()
    assert f"GitHub main at {head[:7]}" in result.stderr

    def stopped(name: str, why: str) -> str:
        return f"{name}: needs-you: {homes / name / 'projects/skills-private'} {why}"

    not_a_clone = "is not a clone of the private repo; move it aside, then rerun"
    assert {
        f"behind: synced: synced at {head[:7]}",
        "dirty: needs-you: checkout has uncommitted skill changes",
        f"editor: synced: synced at {head[:7]}",
        "branch: needs-you: checkout is on feature, not main",
        "ahead: needs-you: checkout has commits GitHub lacks; push them",
        stopped("plain", not_a_clone),
        stopped("linked", not_a_clone),
        stopped(
            "edited",
            "has uncommitted edits; move them to a worktree of skills-private "
            "and open a PR, then rerun",
        ),
        stopped("feature", "is not on main; switch it to main, then rerun"),
        stopped(
            "unshared",
            "has 1 commit its origin/main lacks; open a PR from a worktree of "
            "skills-private, then reset main to origin/main and rerun",
        ),
        "down: offline: ssh: connect to host down port 22: Connection refused",
    } <= set(log)
    answer = json.loads(log[-1])
    errors = answer["errors"]
    assert answer["changes"] == [
        ["sync", "behind", head[:7]],
        ["sync", "editor", head[:7]],
    ]
    assert git(behind, "rev-parse", "HEAD") == head
    assert git(editor, "rev-parse", "HEAD") == head
    assert (editor / ".vscode/settings.json").read_text() == "{}\n"
    assert git(origin, "rev-parse", "main") == head
    assert not (behind / "unpushed.txt").exists()
    assert git(private(behind), "rev-parse", "HEAD") == git(remote, "rev-parse", "main")
    assert not (private(behind) / REGISTRY).exists()
    assert (homes / "behind/just.log").read_text() == "install-skills\n"
    assert (homes / "behind/.claude/skills/secret/SKILL.md").is_file()
    for name, checkout in (("dirty", dirty), ("branch", branch), ("ahead", ahead)):
        assert not private(checkout).exists()
        assert not (homes / name / "just.log").exists()
    assert git(dirty, "rev-parse", "HEAD") == before
    assert kept.read_text() == "# kept\n\nold\n"
    assert not (private(plain) / ".git").exists()
    assert (private(edited) / "authoring/content/mine/SKILL.md").is_file()
    for name, checkout in (
        ("plain", plain),
        ("linked", linked),
        ("edited", edited),
        ("feature", feature),
        ("unshared", unshared),
    ):
        assert git(checkout, "rev-parse", "HEAD") == before
        assert not (homes / name / "just.log").exists()
    assert (
        "dirty needs-you: checkout has uncommitted skill changes; "
        "fix it on dirty, then rerun just sync-fleet dirty"
    ) in errors
    assert any(error.startswith("down offline:") for error in errors)
    assert f"behind: move\t{before[:7]}\t{head[:7]}" in log
    assert "behind: add\t~/.claude/skills/secret" in log


def test_dry_run_names_each_machine_a_sync_would_change_and_changes_nothing(
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
    preview = run(hub, homes, bin_dir, "-n", "-v")

    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        changed(["sync", "behind", head[:7]], ["sync", "stale", head[:7]]),
        "",
    )
    assert preview.stdout == result.stdout
    assert "stale: ~/.claude/skills waits for add 1" in preview.stderr.splitlines()
    assert git(behind, "rev-parse", "HEAD") == before
    assert not (homes / "stale/.claude/skills/alpha").exists()

    # A preview stops where a sync would, on this machine's private edits
    (private(hub) / "authoring/content/secret/SKILL.md").write_text("edited\n")
    edited = run(hub, homes, bin_dir, "-n")

    assert (edited.returncode, edited.stdout) == (1, "")
    assert json.loads(edited.stderr)["errors"] == [
        (
            f"{private(hub)} has uncommitted edits; move them to a worktree of "
            "skills-private and open a PR, then rerun"
        )
    ]


def test_others_still_stops_on_the_coordinators_unshared_private_commit(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The coordinator's private clone gates every run, even when --others skips it."""
    hub, homes, bin_dir = fleet
    machine(homes, "behind", hub.parent / "skills.git")
    register(hub, "behind")
    skill(private(hub) / "authoring/content", "mine")
    commit(private(hub))

    result = run(hub, homes, bin_dir, "--others", "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr)["errors"] == [
        (
            f"{private(hub)} has 1 commit its origin/main lacks; open a PR from a "
            "worktree of skills-private, then reset main to origin/main and rerun"
        )
    ]
    assert not (homes / "behind/just.log").exists()


def merged_private(tmp_path: Path) -> str:
    """Land a commit on the private main, the way a merged PR does."""
    work = tmp_path / "private-pr"
    git(tmp_path, "clone", "-q", str(tmp_path / "skills-private.git"), str(work))
    (work / "merged.md").write_text("merged\n")
    commit(work)
    git(work, "push", "-q", "origin", "main")
    return git(work, "rev-parse", "HEAD")


def test_a_stale_origin_main_does_not_block_a_remote_clone_at_githubs_main(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: the inspection trusted a stale origin/main."""
    hub, homes, bin_dir = fleet
    checkout = machine(homes, "remote", hub.parent / "skills.git")
    register(hub, "remote")
    assert run(hub, homes, bin_dir).returncode == 0
    clone = private(checkout)
    stale = git(clone, "rev-parse", "origin/main")
    github = merged_private(hub.parent)
    # Fast-forward to GitHub's main without moving origin/main
    git(clone, "fetch", "-q", "--refmap=", "origin", "main")
    git(clone, "merge", "-q", "--ff-only", "FETCH_HEAD")
    assert git(clone, "rev-parse", "origin/main") == stale
    head = change(hub)

    result = run(hub, homes, bin_dir, "--others")

    assert (result.returncode, result.stderr) == (0, "")
    assert git(checkout, "rev-parse", "HEAD") == head
    assert git(clone, "rev-parse", "HEAD") == github


@pytest.mark.parametrize("mode", [["--dry-run"], []], ids=["preview", "apply"])
def test_a_remote_clone_without_origin_main_stops_before_the_checkout_moves(
    fleet: tuple[Path, Path, Path], mode: list[str]
) -> None:
    """The old code failed here: a failed comparison counted as no commits, so
    the preview passed and the sync moved the checkout, then refused the clone.
    Each mode gets its own fixture, since the first run fetches origin/main."""
    hub, homes, bin_dir = fleet
    checkout = machine(homes, "remote", hub.parent / "skills.git")
    register(hub, "remote")
    assert run(hub, homes, bin_dir).returncode == 0
    clone = private(checkout)
    skill(clone / "authoring/content", "mine")
    commit(clone)
    git(clone, "update-ref", "-d", "refs/remotes/origin/main")
    before = git(checkout, "rev-parse", "HEAD")
    change(hub)

    result = run(hub, homes, bin_dir, "--others", *mode)

    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr.splitlines()[-1])["errors"] == [
        (
            f"remote needs-you: {clone} has 1 commit its origin/main lacks; open a "
            "PR from a worktree of skills-private, then reset main to origin/main "
            "and rerun; fix it on remote, then rerun just sync-fleet remote"
        )
    ]
    assert git(checkout, "rev-parse", "HEAD") == before
    assert (homes / "remote/just.log").read_text() == "install-skills\n"


def stale_remote(fleet: tuple[Path, Path, Path]) -> Path:
    """A registered remote whose private clone is at GitHub's main, with a stale
    origin/main that makes the inspection fetch."""
    hub, homes, bin_dir = fleet
    checkout = machine(homes, "remote", hub.parent / "skills.git")
    register(hub, "remote")
    assert run(hub, homes, bin_dir).returncode == 0
    clone = private(checkout)
    merged_private(hub.parent)
    git(clone, "fetch", "-q", "--refmap=", "origin", "main")
    git(clone, "merge", "-q", "--ff-only", "FETCH_HEAD")
    return clone


def test_the_inspection_fetch_leaves_fetch_head_to_the_sync(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: its fetch rewrote FETCH_HEAD outside the lock of
    scripts/sync_private.py, so a concurrent inspection could empty it between
    that sync's check and its merge, and the merge then did nothing."""
    hub, homes, bin_dir = fleet
    clone = stale_remote(fleet)
    fetch_head = clone / ".git/FETCH_HEAD"
    fetch_head.write_text("the sync's own fetch\n")
    stale = git(clone, "rev-parse", "origin/main")

    result = run(hub, homes, bin_dir, "--check")

    assert (result.returncode, result.stdout) == (0, OK)
    assert git(clone, "rev-parse", "origin/main") != stale, "the inspection fetched"
    assert fetch_head.read_text() == "the sync's own fetch\n"


def test_a_failed_inspection_fetch_asks_for_a_retry_not_a_pr(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: it ignored the failed fetch and called the
    stale origin/main's missing commits unshared, asking for a PR."""
    hub, homes, bin_dir = fleet
    clone = stale_remote(fleet)
    # git's reason would quote the URL, token included
    absent = f"{hub.parent / 'absent.git'}?access_token=SECRET"
    git(clone, "remote", "set-url", "origin", absent)

    result = run(hub, homes, bin_dir, "--others", "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr)["errors"] == [
        (
            f"remote needs-you: {clone} could not fetch origin main to compare; "
            "retry; fix it on remote, then rerun just sync-fleet remote"
        )
    ]


def test_check_reports_private_edits_made_after_the_inspection(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: the check dropped the dirty state it saw, since
    the inspection had found the clone clean a moment before."""
    hub, homes, bin_dir = fleet
    checkout = machine(homes, "remote", hub.parent / "skills.git")
    register(hub, "remote")
    assert run(hub, homes, bin_dir).returncode == 0
    # The edit lands once the inspection, the step that prints private-needs, ends
    late = """payload=$(cat)
HOME="$FLEET_HOMES/$host" SHELL=/bin/sh /bin/sh -c "$*" <<EOF
$payload
EOF
code=$?
case "$payload" in
    *private-needs*) echo late > "$FLEET_HOMES/$host/projects/skills-private/late.txt" ;;
esac
exit "$code"
"""
    ssh = bin_dir / "ssh"
    ssh.write_text(
        ssh.read_text().replace(
            'HOME="$FLEET_HOMES/$host" SHELL=/bin/sh exec /bin/sh -c "$*"', late
        )
    )

    result = run(hub, homes, bin_dir, "--check")

    assert (private(checkout) / "late.txt").is_file()
    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr)["errors"] == [
        "remote drift: private repo has uncommitted edits; rerun just sync-fleet remote"
    ]


def test_a_broken_registry_keeps_the_private_pull_in_the_report(
    fleet: tuple[Path, Path, Path],
) -> None:
    """The old code failed here: the error dropped the pull it had made."""
    hub, homes, bin_dir = fleet
    host = socket.gethostname().split(".")[0]
    work = hub.parent / "private-pr"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills-private.git"), str(work))
    (work / REGISTRY).parent.mkdir(parents=True)
    (work / REGISTRY).write_text("[machines.broken\n")
    git(work, "add", "-f", REGISTRY)
    commit(work)
    git(work, "push", "-q", "origin", "main")

    result = run(hub, homes, bin_dir, "--others")

    assert (result.returncode, result.stdout) == (1, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert "fleet.toml is not valid TOML" in answer["errors"][0]
    assert answer["changes"] == [["sync", host, git(hub, "rev-parse", "HEAD")[:7]]]
    assert git(private(hub), "rev-parse", "HEAD") == git(work, "rev-parse", "HEAD")


def test_check_answers_ok_when_converged_and_names_each_difference(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    origin = hub.parent / "skills.git"
    synced = machine(homes, "synced", origin)
    lagging = machine(homes, "lagging", origin)
    onbranch = machine(homes, "onbranch", origin)
    detached = machine(homes, "detached", origin)
    register(hub, "synced", "lagging", "onbranch", "detached")
    assert run(hub, homes, bin_dir).returncode == 0
    converged = run(hub, homes, bin_dir, "--check")
    assert (converged.returncode, converged.stdout, converged.stderr) == (0, OK, "")
    # Off main at the expected commit: a sync refuses them, so a check does too
    git(private(onbranch), "switch", "-q", "-c", "feature")
    git(private(detached), "switch", "-q", "--detach")
    off_main = run(hub, homes, bin_dir, "--check", "onbranch", "detached")
    assert (off_main.returncode, off_main.stdout) == (1, "")
    assert sorted(json.loads(off_main.stderr)["errors"]) == [
        f"{name} drift: {private(checkout)} is not on main; switch it to main, "
        f"then rerun; rerun just sync-fleet {name}"
        for name, checkout in (("detached", detached), ("onbranch", onbranch))
    ]
    change(hub)
    assert run(hub, homes, bin_dir, "synced").returncode == 0
    (private(lagging) / "authoring/content/secret/SKILL.md").write_text("edited\n")
    # Another machine pushed a private edit that neither has pulled yet.
    other = hub.parent / "other-private"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills-private.git"), str(other))
    (other / "notes.md").write_text("elsewhere\n")
    commit(other)
    git(other, "push", "-q", "origin", "main")
    github = git(other, "rev-parse", "HEAD")

    result = run(hub, homes, bin_dir, "--check", "synced", "lagging")

    assert (result.returncode, result.stdout) == (1, "")
    errors = sorted(json.loads(result.stderr)["errors"])
    assert len(errors) == 2
    lagging_error, synced_error = errors
    assert lagging_error.startswith(
        f"lagging drift: {private(lagging)} has uncommitted edits; "
    )
    assert "; checkout is behind " in lagging_error
    assert f", GitHub at {github[:7]}" in lagging_error
    assert "~/.claude/skills waits for update 1" in lagging_error
    assert synced_error.startswith(
        f"synced drift: private repo is at {git(private(hub), 'rev-parse', 'HEAD')[:7]}, "
        f"GitHub at {github[:7]}"
    )
    assert git(synced, "rev-parse", "HEAD") == git(hub, "rev-parse", "HEAD")


# A machine left offline may still run one; its preview cannot show a conflict,
# so the check fails closed
def test_check_fails_on_an_installer_from_before_490(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "old", hub.parent / "skills.git")
    register(hub, "old")
    assert run(hub, homes, bin_dir).returncode == 0

    result = run(hub, homes, bin_dir, "--check", FLEET_OLD_INSTALLER="1")

    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr)["errors"] == [
        (
            "old drift: its installer predates #490 and answers no JSON line, so a "
            "conflict would not show; rerun just sync-fleet old"
        )
    ]


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
    assert (committed.returncode, committed.stderr) == (0, "")
    installed = json.loads(committed.stdout)
    assert installed["ok"] is True
    assert ["add", "~/.claude/skills/alpha"] in installed["changes"]
    assert (home / ".claude/skills/alpha/SKILL.md").is_file()
    assert not fleet_log.exists()

    refs = f"refs/heads/main {head} refs/heads/main {before}\n"
    pushing = run(hub, homes, bin_dir, "--hook", "pre-push", stdin=refs)
    assert (pushing.returncode, pushing.stdout, pushing.stderr) == (0, OK, "")
    git(hub, "push", "-q", "origin", "main")

    deadline = time.monotonic() + 60
    while "behind: synced" not in (fleet_log.read_text() if fleet_log.exists() else ""):
        assert time.monotonic() < deadline, "background sync did not finish"
        time.sleep(0.2)
    assert git(behind, "rev-parse", "HEAD") == head != before


def test_a_hook_fails_in_a_main_checkout_without_the_registry(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    worktree = hub.parent / "worktree"
    git(hub, "worktree", "add", "-q", str(worktree))

    result = run(hub, homes, bin_dir, "--hook", "post-commit")
    elsewhere = run(worktree, homes, bin_dir, "--hook", "post-commit")

    assert (result.returncode, result.stdout) == (1, "")
    [error] = json.loads(result.stderr)["errors"]
    assert error.startswith("no fleet.toml in ")
    assert not (hub.parent / "hub-home/.claude").exists()
    assert (elsewhere.returncode, elsewhere.stdout, elsewhere.stderr) == (0, OK, "")


def test_a_worktree_syncs_with_the_main_checkouts_registry_and_skips_hooks(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "down")
    worktree = hub.parent / "worktree"
    git(hub, "worktree", "add", "-q", str(worktree))
    head = git(hub, "rev-parse", "HEAD")
    fleet_log = hub.parent / "hub-home/.local/state/skills-sync/fleet.log"

    result = run(worktree, homes, bin_dir, "--dry-run")
    refs = f"refs/heads/main {head} refs/heads/main {'0' * 40}\n"
    pushing = run(worktree, homes, bin_dir, "--hook", "pre-push", stdin=refs)

    assert (result.returncode, result.stdout) == (75, "")
    assert json.loads(result.stderr)["errors"][0].startswith("down offline: ")
    assert (pushing.returncode, pushing.stdout, pushing.stderr) == (0, OK, "")
    assert not fleet_log.exists()


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
        changed(["sync", here, github[:7]]),
        "",
    )
    assert git(hub, "rev-parse", "HEAD") == github != before
    assert (home / "just.log").read_text() == "install-skills\n"
    assert (home / ".claude/skills/secret/SKILL.md").is_file()


def test_a_run_whose_only_failures_are_offline_machines_exits_75(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "down")

    result = run(hub, homes, bin_dir, "--dry-run")

    assert (result.returncode, result.stdout) == (75, "")
    answer = json.loads(result.stderr)
    assert answer["errors"][0].startswith("down offline: ")
    assert answer["retry"] == "just sync-fleet --dry-run"


def test_an_unknown_machine_is_a_usage_error(fleet: tuple[Path, Path, Path]) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "mbp")

    result = run(hub, homes, bin_dir, "mpb")

    assert (result.returncode, result.stdout) == (2, "")
    assert json.loads(result.stderr) == {
        "ok": False,
        "errors": ["unknown machine mpb; the registry lists mbp"],
        "help": "just sync-fleet --help",
    }


def test_a_machine_that_refuses_the_login_is_a_failure_not_a_retry(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    register(hub, "down", "locked")

    result = run(hub, homes, bin_dir, "--dry-run")

    assert (result.returncode, result.stdout) == (1, "")
    assert sorted(json.loads(result.stderr)["errors"]) == [
        "down offline: ssh: connect to host down port 22: Connection refused; "
        + "it catches up at the next sync, or rerun just sync-fleet down",
        "locked failed: tester@locked: Permission denied (publickey).; "
        + "rerun just sync-fleet locked --debug",
    ]


def test_a_check_that_loses_the_machine_midway_exits_75(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    machine(homes, "flaky", hub.parent / "skills.git")
    register(hub, "flaky")

    result = run(hub, homes, bin_dir, "--check")

    assert (result.returncode, result.stdout) == (75, "")
    assert json.loads(result.stderr)["errors"][0].startswith(
        "flaky offline: Connection to flaky closed by remote host.; "
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

    result = run(hub, homes, bin_dir, "--check")

    assert (result.returncode, result.stdout) == (1, "")
    [error] = json.loads(result.stderr)["errors"]
    assert error.startswith("broken failed: ")
    assert "has a file ancestor" in error


def test_a_failed_install_keeps_the_machines_completed_changes(
    fleet: tuple[Path, Path, Path],
) -> None:
    hub, homes, bin_dir = fleet
    broken = machine(homes, "broken", hub.parent / "skills.git")
    before = git(broken, "rev-parse", "HEAD")
    change(hub)
    (homes / "broken/.config").write_text("not a directory\n")
    register(hub, "broken")

    result = run(hub, homes, bin_dir)

    assert (result.returncode, result.stdout) == (1, "")
    answer = json.loads(result.stderr.splitlines()[-1])
    assert answer["ok"] is False
    assert answer["changes"] == [["sync", "broken", git(hub, "rev-parse", "HEAD")[:7]]]
    assert git(broken, "rev-parse", "HEAD") != before
    assert git(broken, "rev-parse", "HEAD") == git(hub, "rev-parse", "HEAD")


def test_reads_the_registry_after_pulling_the_private_clone(
    fleet: tuple[Path, Path, Path],
) -> None:
    """A registry change merged on GitHub applies to the same run, and the pull
    counts as a change on this machine, even when --others skips it."""
    hub, homes, bin_dir = fleet
    host = socket.gethostname().split(".")[0]
    added = machine(homes, "added", hub.parent / "skills.git")
    register(hub, "down")
    # The merged PR adds the machine to the registry the hub has not pulled
    other = hub.parent / "other-private"
    git(hub.parent, "clone", "-q", str(hub.parent / "skills-private.git"), str(other))
    (other / REGISTRY).parent.mkdir(parents=True)
    (other / REGISTRY).write_text(entries("added"))
    git(other, "add", "-f", REGISTRY)
    commit(other)
    git(other, "push", "-q", "origin", "main")
    (private(hub) / REGISTRY).unlink()

    result = run(hub, homes, bin_dir, "--others")

    head = git(hub, "rev-parse", "HEAD")[:7]
    assert (result.returncode, result.stdout, result.stderr) == (
        0,
        changed(["sync", host, head], ["sync", "added", head]),
        "",
    )
    assert (private(hub) / REGISTRY).read_text() == entries("added")
    assert (homes / "added/just.log").read_text() == "install-skills\n"
    assert git(private(added), "rev-parse", "HEAD") == git(other, "rev-parse", "HEAD")


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
