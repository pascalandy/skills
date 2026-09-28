"""Every entry point against the contract in docs/maintainer/references/script-conventions.md.

ENTRIES registers each script that follows the contract with what an isolated
run needs. PENDING lists the scripts a later wave migrates and EXCLUDED the ones
the contract leaves out; a script in none of them fails the suite. Each probe
runs in its own repository and home, with a bin/ directory first on PATH.
"""

from __future__ import annotations

import errno
import importlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from itertools import takewhile
from pathlib import Path

import pytest
from conftest import DECLARED, GIT_IDENTITY, SCRIPTS, commit, observe, skill

ROOT = SCRIPTS.parent
TESTS = SCRIPTS / "tests"
BLOCK_MARKER = "# >>> cli-block"


@dataclass(frozen=True)
class Sandbox:
    """A repository holding every scripts/ file, a home, and a bin/ first on PATH."""

    repo: Path
    home: Path
    bin: Path

    def env(self, **extra: str) -> dict[str, str]:
        # The caller's git, XDG, and debug settings would change what scripts do
        env = {
            name: value
            for name, value in os.environ.items()
            if not name.startswith(("GIT_", "XDG_")) and not name.endswith("_DEBUG")
        }
        return {
            **env,
            **GIT_IDENTITY,
            "HOME": str(self.home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "PATH": f"{self.bin}{os.pathsep}{os.environ['PATH']}",
            **extra,
        }

    def command(self, path: str, *args: str) -> list[str]:
        return [sys.executable, str(self.repo / path), *args]

    def run(
        self, path: str, *args: str, **env: str
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            self.command(path, *args),
            cwd=self.repo,
            env=self.env(**env),
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        observe(Path(path).stem, result.returncode)
        return result

    def stub(self, name: str, body: str) -> None:
        """Put a shell script named `name` first on PATH."""
        path = self.bin / name
        path.write_text(f"#!/bin/sh\n{body}", encoding="utf-8")
        path.chmod(0o755)


def make_sandbox(root: Path) -> Sandbox:
    repo = root / "repo"
    (repo / "scripts").mkdir(parents=True)
    for path in SCRIPTS.glob("*.py"):
        shutil.copy2(path, repo / "scripts" / path.name)
    (repo / ".gitignore").write_text("_skills_private/\n__pycache__/\n")
    skill(repo / "authoring/content", "alpha")
    skill(repo / "skills", "alpha")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    commit(repo)
    sandbox = Sandbox(repo, root / "home", root / "bin")
    sandbox.home.mkdir()
    sandbox.bin.mkdir()
    return sandbox


def prepared(script: Entry, root: Path) -> Sandbox:
    """A sandbox holding the files every run of `script` needs."""
    sandbox = make_sandbox(root)
    script.prepare(sandbox)
    return sandbox


def nothing(_: Sandbox) -> None:
    return None


def no_arguments(_: Sandbox) -> tuple[str, ...]:
    return ()


@dataclass(frozen=True)
class Entry:
    """How the probes run one script.

    `block` is the command a stub on PATH blocks in, or `fifo:<path>` for a file
    the script reads; `args` reach that block. `safe` prepares a run that
    changes nothing a user owns and returns its arguments. `positional` holds
    the arguments every usage probe needs.
    """

    name: str
    block: str
    args: tuple[str, ...] = ()
    prepare: Callable[[Sandbox], None] = nothing
    safe: Callable[[Sandbox], tuple[str, ...]] = no_arguments
    positional: tuple[str, ...] = ()
    debug: bool = True


def quoted_frontmatter(sandbox: Sandbox) -> None:
    path = sandbox.repo / "authoring/content/alpha/SKILL.md"
    path.write_text('---\nname: "alpha"\n---\n', encoding="utf-8")


def jev_pins(sandbox: Sandbox) -> None:
    """check.py reads the TypeSafe SDK pins from both engines when it loads."""
    for relative in (
        "authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/jevgate.py",
        "authoring/devtools/label-for-issues-jev/scripts/jevlabel.py",
    ):
        (sandbox.repo / relative).parent.mkdir(parents=True)
        shutil.copy2(ROOT / relative, sandbox.repo / relative)


def check_list(_: Sandbox) -> tuple[str, ...]:
    return ("--list",)


def release_ready(sandbox: Sandbox) -> None:
    """A committed changelog section, with HEAD on origin/main."""
    (sandbox.repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [0.1.0] - 2026-09-26\n\n- First\n", encoding="utf-8"
    )
    commit(sandbox.repo)
    subprocess.run(
        ["git", "update-ref", "refs/remotes/origin/main", "HEAD"],
        cwd=sandbox.repo,
        check=True,
    )


def first_release(_: Sandbox) -> tuple[str, ...]:
    return ("v0.1.0",)


def new_skill_preview(sandbox: Sandbox) -> tuple[str, ...]:
    skill(sandbox.repo / "authoring/content", "beta")
    return ("--dry-run",)


def mac_preview(_: Sandbox) -> tuple[str, ...]:
    return ("--profile", "mac", "--dry-run")


def opencode_finds_alpha(sandbox: Sandbox) -> tuple[str, ...]:
    """An installed alpha and an OpenCode that reports it."""
    entry = sandbox.home / ".config/opencode/skills/alpha/SKILL.md"
    entry.parent.mkdir(parents=True)
    entry.write_text("# alpha\n", encoding="utf-8")
    listing = json.dumps([{"name": "alpha", "location": str(entry)}])
    sandbox.stub("opencode", f"echo '{listing}'\n")
    return ("--profile", "mac", "--agent", "opencode")


def with_origin(sandbox: Sandbox) -> None:
    subprocess.run(
        ["git", "remote", "add", "origin", "https://example.invalid/skills.git"],
        cwd=sandbox.repo,
        check=True,
    )


def dry_run(_: Sandbox) -> tuple[str, ...]:
    return ("--dry-run",)


def fleet_of_one(sandbox: Sandbox) -> None:
    """GitHub as a bare clone, and a registry naming one remote machine."""
    origin = sandbox.repo.parent / "origin.git"
    subprocess.run(
        ["git", "clone", "-q", "--bare", str(sandbox.repo), str(origin)], check=True
    )
    subprocess.run(
        ["git", "remote", "add", "origin", str(origin)], cwd=sandbox.repo, check=True
    )
    subprocess.run(["git", "fetch", "-q", "origin"], cwd=sandbox.repo, check=True)
    registry = sandbox.repo / "_skills_private/fleet.toml"
    registry.parent.mkdir()
    registry.write_text(
        '[machines.far]\nssh = "tester@far"\npath = "projects/skills"\n'
    )


def far_is_behind(sandbox: Sandbox) -> tuple[str, ...]:
    """GitHub moves one commit ahead of the checkout far reports."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=sandbox.repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    (sandbox.repo / "change.txt").write_text("new\n")
    commit(sandbox.repo)
    subprocess.run(
        ["git", "push", "-q", "origin", "HEAD:main"], cwd=sandbox.repo, check=True
    )
    sandbox.stub("ssh", f"echo 'checkout main {head} clean'\n")
    return ("--dry-run",)


ENTRIES: dict[str, Entry] = {
    # A preview blocks in the SSH step a worker thread runs
    "scripts/sync_fleet.py": Entry(
        name="just sync-fleet",
        block="ssh",
        args=("--dry-run",),
        prepare=fleet_of_one,
        safe=far_is_behind,
    ),
    # The preview blocks in the installer it starts, so signals test the handoff
    "scripts/sync.py": Entry(
        name="just sync", block="git", args=("--dry-run",), safe=dry_run
    ),
    "scripts/sync_private.py": Entry(
        name="scripts/sync_private.py",
        block="git",
        prepare=with_origin,
        safe=dry_run,
    ),
    "scripts/discover_skills.py": Entry(
        name="just skills-discover",
        block="opencode",
        args=("--agent", "opencode"),
        safe=opencode_finds_alpha,
        positional=("--profile", "mac"),
    ),
    "scripts/install_skills.py": Entry(
        name="just install-skills", block="git", safe=mac_preview
    ),
    "scripts/flatten_skills.py": Entry(
        name="just flatten-skills", block="git", safe=new_skill_preview
    ),
    "scripts/release_check.py": Entry(
        name="just release-check",
        block="git",
        prepare=release_ready,
        safe=first_release,
        positional=("v0.1.0",),
    ),
    "scripts/check.py": Entry(
        name="just check",
        block="uv",
        args=("--only", "frontmatter"),
        prepare=jev_pins,
        safe=check_list,
    ),
    "scripts/check_frontmatter.py": Entry(
        name="just check-frontmatter",
        block="fifo:authoring/content/beta/SKILL.md",
        prepare=quoted_frontmatter,
        debug=False,
    ),
    "scripts/check_cli_block.py": Entry(
        name="scripts/check_cli_block.py",
        block="fifo:authoring/content/alpha/scripts/tool.py",
        debug=False,
    ),
}

# Scripts a later wave moves onto the contract
PENDING = {
    "authoring/content/html-mode/scripts/check_html_mode.py",
    "authoring/content/mermaid/scripts/render_examples.py",
    "authoring/content/storytelling/tests/validate-package.py",
    "authoring/content/transcript-sk/scripts/transcript.py",
    "authoring/devtools/coding-language/references/Bash/scripts/pref_bash_script_template.sh",
    "authoring/devtools/coding-language/references/Bash/scripts/run_shellck.sh",
    "authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/jevgate.py",
    "authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/stamp_engine.py",
    "authoring/devtools/label-for-issues-jev/scripts/jevlabel.py",
    "authoring/knowledge/distill/scripts/distill.py",
    "authoring/mattpocock/matt-mode/scripts/check_matt_mode.py",
    "authoring/mattpocock/matt-mode/scripts/check_meta_skill_layout.py",
    "authoring/mattpocock/matt-mode/scripts/update_matt_mode.py",
    "authoring/pstack/poteto-mode/scripts/check-plan.mjs",
    "authoring/pstack/poteto-mode/scripts/orch/orch.ts",
    "authoring/pstack/poteto-mode/scripts/watch-pr/watch-pr",
    "authoring/pstack/poteto-mode/scripts/worktree-audit.sh",
    "authoring/pstack/show-me-your-work/scripts/log.sh",
    "authoring/verify/verify-transcript-sk/scripts/verify_transcript_sk.py",
    "authoring/verify/verify-video-archive/scripts/verify_video_archive.py",
    "authoring/web-research/tavily/scripts/grokipedia.py",
}

EXCLUDED = {
    "authoring/content/transcript-sk/scripts/ytdlp_arc.py": "owner decision: out of scope",
    "authoring/content/transcript-sk/scripts/youtube_smoke.py": "live check against YouTube",
    ".lefthook/pre-push/sync-skills.sh": "exec shim for just sync-hook",
    "authoring/devtools/create-a-jev-cli-decision-wrapped-in-a-skill/scripts/tests/proof_live_noul.py": "live proof against the TypeSafe API",
}


def entry_points() -> set[str]:
    """Every script a person, agent, hook, or CI can run, outside ignored files."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout.decode()
    found: set[str] = set()
    for relative in filter(None, listed.split("\0")):
        path = ROOT / relative
        name = path.name
        if relative.startswith("scripts/"):
            if path.parent == SCRIPTS and name.endswith(".py") and name[0] != "_":
                found.add(relative)
            continue
        if (
            not relative.startswith(("authoring/", ".lefthook/"))
            or not path.is_file()
            or name.startswith(("test_", "conftest"))
            or ".test." in name
            or ".test-helper." in name
        ):
            continue
        if path.suffix == ".py":
            runnable = '__name__ == "__main__"' in path.read_text(encoding="utf-8")
        else:
            with path.open("rb") as stream:
                runnable = path.suffix == ".sh" or stream.read(2) == b"#!"
        if runnable:
            found.add(relative)
    return found


def section(text: str, title: str) -> list[str]:
    """The lines under `title:` in a help page, up to the next blank line."""
    lines = text.splitlines()
    return list(takewhile(str.strip, lines[lines.index(f"{title}:") + 1 :]))


FLAG = re.compile(r"(?<![\w/.-])(--?[A-Za-z][\w-]*)")


def accepted(flag: str, allowed: set[str]) -> bool:
    """Whether the script takes `flag`, reading `-vn` as `-v -n`."""
    if flag in allowed:
        return True
    return not flag.startswith("--") and all(f"-{c}" in allowed for c in flag[1:])


def recipes() -> dict[str, str]:
    """Each justfile recipe that runs a scripts/ file, mapped to that file."""
    found: dict[str, str] = {}
    name = ""
    for line in (ROOT / "justfile").read_text(encoding="utf-8").splitlines():
        if header := re.match(r"([a-z][\w-]*)[^:=]*:(?!=)", line):
            name = header[1]
        elif name and (target := re.search(r"\bscripts/\w+\.py", line)):
            found[name] = target[0]
    return found


def doc_sources() -> Iterator[Path]:
    """Files whose lines may run a script: docs, hooks, CI, and scripts/."""
    for name in ("README.md", "AGENTS.md", "CHANGELOG.md", "justfile", "lefthook.yml"):
        yield ROOT / name
    yield from (ROOT / "docs").rglob("*.md")
    yield from (ROOT / "authoring").rglob("*.md")
    yield from (ROOT / ".github").rglob("*.yml")
    yield from (path for path in (ROOT / ".lefthook").rglob("*") if path.is_file())
    yield from SCRIPTS.glob("*.py")


# What ends a command inside a line: shell operators everywhere, closing quotes
# in Python strings, and code spans or table cells in Markdown
ENDINGS = {".py": "`\"'", ".md": "`|"}


def doc_flags(path: str) -> Iterator[tuple[str, str]]:
    """Each flag a doc line passes to the script, with where the line is."""
    names = [name for name, target in recipes().items() if target == path]
    runs = re.compile(
        "|".join(
            [rf"\bjust {re.escape(name)}(?![\w-])" for name in names]
            + [rf"(?<![\w/]){re.escape(path)}(?![\w.])"]
        )
    )
    for source in doc_sources():
        stop = re.compile(
            r"&&|\|\||[;#<>()]"
            + (
                f"|[{re.escape(ENDINGS[source.suffix])}]"
                if source.suffix in ENDINGS
                else ""
            )
        )
        lines = source.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            for match in runs.finditer(line):
                rest = line[match.end() :]
                end = stop.search(rest)
                for flag in FLAG.findall(rest[: end.start() if end else None]):
                    yield flag, f"{source.relative_to(ROOT)}:{number}"


# Blocks until SIGTERM, then stops its own child, says it is cleaning up, and
# waits for the test to release it; it writes its PID and its child's last,
# once the trap is set
STUB = """\
trap 'kill "$child"; : > "{ready}.cleanup"; while [ ! -e "{ready}.release" ]; do sleep 0.05; done; exit 0' TERM
sleep 60 &
child=$!
echo "$$ $child" > "{ready}.tmp" && mv "{ready}.tmp" "{ready}"
wait
"""


def wait_for(condition: Callable[[], object], what: str, seconds: float = 30) -> None:
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, f"timed out waiting for {what}"
        time.sleep(0.05)


def wait_until_blocked(
    process: subprocess.Popen[str], ready: Path | None, fifo: Path | None
) -> tuple[list[int], int | None]:
    """Wait until the script sits in its block: return the stub's PID and its
    child's, or an open write end of the FIFO the script is reading."""
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise AssertionError(f"exited before blocking: {process.communicate()}")
        if fifo is not None:
            try:
                return [], os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
            except OSError as error:
                if error.errno != errno.ENXIO:
                    raise
        elif ready is not None and ready.exists():
            return [int(pid) for pid in ready.read_text().split()], None
        time.sleep(0.05)
    raise AssertionError("the script never reached its block")


def alive(pid: int) -> bool:
    """Whether `pid` runs; on Linux, a zombie waiting for init counts as gone."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    if not Path("/proc/self/stat").exists():
        return True
    try:
        state = Path(f"/proc/{pid}/stat").read_text().split(") ")[-1]
    except FileNotFoundError:
        return False
    return not state.startswith("Z")


@pytest.fixture(params=sorted(ENTRIES))
def entry(request: pytest.FixtureRequest) -> tuple[str, Entry]:
    return request.param, ENTRIES[request.param]


def test_every_entry_point_is_registered() -> None:
    listed = set(ENTRIES) | PENDING | set(EXCLUDED)
    found = entry_points()

    assert sorted(found - listed) == [], "register these in ENTRIES or PENDING"
    assert sorted(listed - found) == [], "these are gone; drop them"
    assert not set(ENTRIES) & PENDING


def test_a_pending_script_has_not_moved_onto_the_contract() -> None:
    migrated = [
        path
        for path in sorted(PENDING)
        if (text := (ROOT / path).read_text(encoding="utf-8"))
        and ("EXIT_CODES = exit_codes(" in text or BLOCK_MARKER in text)
    ]

    assert migrated == [], "move these from PENDING to ENTRIES"


def test_every_exit_code_has_a_test_that_triggers_it(entry: tuple[str, Entry]) -> None:
    path, _ = entry
    for test in TESTS.glob("test_*.py"):
        importlib.import_module(test.stem)
    stem = Path(path).stem
    table = set(importlib.import_module(stem).EXIT_CODES)
    # The usage and signal probes below trigger 2, 130, and 143 for every entry
    declared = DECLARED.get(stem, set())

    assert sorted(table - {2, 130, 143} - declared) == [], "add @exits tests"
    assert sorted(declared - table) == [], "add these codes to EXIT_CODES"


def test_help_shows_examples_and_exit_codes_and_wins(
    entry: tuple[str, Entry], tmp_path: Path
) -> None:
    path, script = entry
    sandbox = prepared(script, tmp_path)
    shown = sandbox.run(path, "--help")
    examples = section(shown.stdout, "examples")
    codes = [int(line.split()[0]) for line in section(shown.stdout, "exit codes")]

    assert (shown.returncode, shown.stderr) == (0, "")
    assert shown.stdout.startswith(f"usage: {script.name} ")
    assert 2 <= len(examples) <= 5
    assert all(script.name in example for example in examples)
    assert codes == list(importlib.import_module(Path(path).stem).EXIT_CODES)
    for argv in (
        ["-h"],
        ["--bogus-flag", "--help"],
        [*script.positional, "--help", "--bogus-flag"],
    ):
        again = sandbox.run(path, *argv)
        assert (again.returncode, again.stdout, again.stderr) == (0, shown.stdout, "")


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (["--bogus-flag"], "unrecognized arguments: --bogus-flag"),
        (["--verbos"], "unrecognized arguments: --verbos"),
    ],
    ids=["unknown", "abbreviated"],
)
def test_a_usage_error_exits_2_with_short_usage_and_the_help_hint(
    entry: tuple[str, Entry], argv: list[str], error: str, tmp_path: Path
) -> None:
    path, script = entry
    result = prepared(script, tmp_path).run(path, *script.positional, *argv)
    lines = result.stderr.splitlines()

    assert (result.returncode, result.stdout) == (2, "")
    assert lines[0].startswith(f"usage: {script.name}")
    assert f"error: {error}" in lines
    assert lines[-1] == f"run '{script.name} --help'"


def test_a_missing_argument_exits_2_with_the_help_hint(
    entry: tuple[str, Entry], tmp_path: Path
) -> None:
    path, script = entry
    if not script.positional:
        pytest.skip("takes no required argument")
    result = prepared(script, tmp_path).run(path)

    assert (result.returncode, result.stdout) == (2, "")
    assert "the following arguments are required" in result.stderr
    assert result.stderr.splitlines()[-1] == f"run '{script.name} --help'"


def test_double_dash_ends_options_so_help_after_it_is_an_argument(
    entry: tuple[str, Entry], tmp_path: Path
) -> None:
    path, script = entry
    result = prepared(script, tmp_path).run(path, *script.positional, "--", "--help")

    assert result.returncode != 0
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("first", "repeat", "code", "last"),
    [
        (signal.SIGINT, None, 130, "interrupted"),
        (signal.SIGTERM, None, 143, "terminated"),
        (signal.SIGTERM, signal.SIGINT, 143, "terminated"),
    ],
    ids=["sigint", "sigterm", "repeat"],
)
def test_a_signal_exits_without_a_traceback_and_stops_children(
    entry: tuple[str, Entry],
    first: signal.Signals,
    repeat: signal.Signals | None,
    code: int,
    last: str,
    tmp_path: Path,
) -> None:
    path, script = entry
    fifo_block = script.block.startswith("fifo:")
    if fifo_block and repeat is not None:
        pytest.skip("no child to clean up; test_cli.py covers the repeat itself")
    sandbox = prepared(script, tmp_path)
    ready = fifo = None
    if fifo_block:
        fifo = sandbox.repo / script.block.removeprefix("fifo:")
        fifo.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(fifo)
    else:
        ready = tmp_path / "ready"
        sandbox.stub(script.block, STUB.format(ready=ready))
    process = subprocess.Popen(
        sandbox.command(path, *script.positional, *script.args),
        cwd=sandbox.repo,
        env=sandbox.env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    children: list[int] = []
    writer = None
    try:
        children, writer = wait_until_blocked(process, ready, fifo)
        process.send_signal(first)
        if ready is not None:
            cleanup = Path(f"{ready}.cleanup")
            # The script passed SIGTERM on and now waits for the stub to clean up
            wait_for(cleanup.exists, "the stub to start cleaning up")
            if repeat is not None:
                process.send_signal(repeat)
                time.sleep(0.3)
                assert process.poll() is None, "a repeated signal cut cleanup short"
            Path(f"{ready}.release").touch()
        stdout, stderr = process.communicate(timeout=30)
        observe(Path(path).stem, process.returncode)

        assert process.returncode == code, stderr
        assert (stdout, stderr.splitlines()[-1]) == ("", last)
        assert "Traceback" not in stderr
        for pid in children:
            wait_for(lambda pid=pid: not alive(pid), f"process {pid} to end", 10)
    finally:
        process.kill()
        process.wait()
        if ready is not None:
            Path(f"{ready}.release").touch()
        for pid in children:
            if alive(pid):
                os.kill(pid, signal.SIGKILL)
        if writer is not None:
            os.close(writer)


def test_verbosity_changes_only_stderr(
    entry: tuple[str, Entry], tmp_path: Path
) -> None:
    path, script = entry
    sandbox = prepared(script, tmp_path)
    args = script.safe(sandbox)
    levels = [[], ["-v"], *([["--debug"]] if script.debug else [])]
    runs = [sandbox.run(path, *args, *level) for level in levels]
    quiet = runs[0]

    assert [(run.returncode, run.stdout) for run in runs] == [
        (quiet.returncode, quiet.stdout)
    ] * len(runs)
    assert quiet.returncode != 0 or quiet.stderr == ""
    assert not any("Traceback" in run.stderr for run in runs[:2])
    if script.debug:
        variable = f"{Path(path).stem.upper()}_DEBUG"
        via_env = sandbox.run(path, *args, **{variable: "1"})
        assert (via_env.returncode, via_env.stdout) == (quiet.returncode, quiet.stdout)
        assert len(via_env.stderr.splitlines()) == len(runs[-1].stderr.splitlines())


def test_doc_lines_that_run_a_script_use_only_its_flags(
    entry: tuple[str, Entry], tmp_path: Path
) -> None:
    path, script = entry
    shown = prepared(script, tmp_path).run(path, "--help")
    allowed = set(FLAG.findall("\n".join(section(shown.stdout, "options"))))

    unknown = [
        f"{where}: {flag}"
        for flag, where in doc_flags(path)
        if not accepted(flag, allowed)
    ]

    assert unknown == []
