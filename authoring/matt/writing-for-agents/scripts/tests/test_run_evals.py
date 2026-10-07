from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parent.parent / "run_evals.py"

FAKE_CLAUDE = """\
#!/usr/bin/env bash
report="$FAKE_REPORTS/$(basename "$(dirname "$PWD")")"
mkdir -p "$report"
printf '%s\\n' "$@" > "$report/argv"
ls .claude/skills > "$report/skills"
cat .claude/skills/demo/SKILL.md > "$report/demo" 2>/dev/null || echo absent > "$report/demo"
eval "${FAKE_ACTION:-true}"
echo '{"type":"result","result":"claude answer"}'
"""

FAKE_CODEX = """\
#!/usr/bin/env bash
report="$FAKE_REPORTS/$(basename "$(dirname "$PWD")")"
mkdir -p "$report"
printf '%s\\n' "$@" > "$report/argv"
cat > "$report/stdin"
cat .agents/skills/demo/SKILL.md > "$report/demo" 2>/dev/null || echo absent > "$report/demo"
eval "${FAKE_ACTION:-true}"
out="" prev=""
for arg in "$@"; do [ "$prev" = -o ] && out=$arg; prev=$arg; done
echo "codex answer" > "$out"
"""

FAKE_GH = """\
#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$FAKE_REPORTS/real-gh.log"
"""


def write(path: Path, text: str, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)


def commit(repo: Path, message: str) -> str:
    def git(*args: str) -> str:
        return subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.name=T",
                "-c",
                "user.email=t@t",
                *args,
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    git("add", "-A")
    git("commit", "-qm", message)
    return git("rev-parse", "HEAD")


@dataclass(frozen=True)
class Lab:
    skill: Path
    ref: str
    before: str
    home: Path
    reports: Path
    env: dict[str, str]
    out: Path
    tmp: Path


@pytest.fixture
def lab(tmp_path: Path) -> Lab:
    """A repo whose skill changes across commits, fake agent CLIs, and a HOME
    holding installed copies."""
    repo = tmp_path / "repo"
    skills = repo / "skills"
    write(repo / "extras" / "helper" / "SKILL.md", "helper\n")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    before = commit(repo, "helper only")
    write(skills / "demo" / "SKILL.md", "demo v1\n")
    write(skills / "gone" / "SKILL.md", "gone\n")
    commit(repo, "demo v1")
    write(skills / "demo" / "SKILL.md", "demo v2\n")
    shutil.rmtree(skills / "gone")
    ref = commit(repo, "demo v2, gone removed")
    write(skills / "demo" / "SKILL.md", "demo v3 uncommitted\n")
    evals = skills / "demo" / "evals"
    write(evals / "fixtures" / "notes-md.md", "notes\n")
    scenarios = [
        {
            "skills": ["demo", "helper"],
            "setup": [
                'cp "$EVALS/fixtures/notes-md.md" NOTES.md',
                "git add -A",
                "git commit -qm base",
            ],
            "query": "Tidy the notes.",
        },
        {"query": "Second request."},
    ]
    write(evals / "evals.json", json.dumps(scenarios))

    bin_dir = tmp_path / "bin"
    write(bin_dir / "claude", FAKE_CLAUDE, 0o755)
    write(bin_dir / "codex", FAKE_CODEX, 0o755)
    write(bin_dir / "gh", FAKE_GH, 0o755)
    home = tmp_path / "home"
    for name in ("demo", "gone", "private"):
        write(home / ".codex" / "skills" / name / "SKILL.md", f"installed {name}\n")
    reports = tmp_path / "reports"
    reports.mkdir()
    env = {
        **os.environ,
        "HOME": str(home),
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "FAKE_REPORTS": str(reports),
        "GH_TOKEN": "user-token",
        "GITHUB_TOKEN": "user-token",
    }
    env.pop("RUN_EVALS_PARENT", None)
    return Lab(
        skills / "demo", ref, before, home, reports, env, tmp_path / "out", tmp_path
    )


def run(lab: Lab, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RUNNER), str(lab.skill), *args],
        capture_output=True,
        text=True,
        env={**lab.env, **env},
        check=False,
        timeout=30,
    )


def answer(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    """The one-line answer: on stdout for a success, else the last line of stderr."""
    if result.returncode == 0:
        assert result.stdout.count("\n") == 1, result.stdout
        return json.loads(result.stdout)
    assert result.stdout == ""
    return json.loads(result.stderr.splitlines()[-1])


def report(lab: Lab, name: str, file: str) -> str:
    return (lab.reports / name / file).read_text(encoding="utf-8")


def test_each_scenario_runs_in_each_agent_with_the_skill_from_the_ref(lab: Lab):
    out = lab.out
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(out))

    assert result.returncode == 0, result.stderr
    names = ("s1-claude", "s1-codex", "s2-claude", "s2-codex")
    assert answer(result) == {"ok": True, "folders": [str(out / n) for n in names]}
    assert report(lab, "s1-claude", "demo") == "demo v2\n"
    assert report(lab, "s1-codex", "demo") == "demo v2\n"
    assert report(lab, "s1-claude", "skills").split() == ["demo", "helper"]
    assert report(lab, "s2-claude", "demo") == "demo v2\n"
    assert "Tidy the notes." in report(lab, "s1-claude", "argv").splitlines()
    assert report(lab, "s1-codex", "stdin") == "Tidy the notes."
    first = out / "s1-claude"
    assert (first / "answer.md").read_text() == "claude answer"
    assert (out / "s1-codex" / "answer.md").read_text() == "codex answer\n"
    assert "base" in (first / "git-log.txt").read_text()
    assert (first / "git-status.txt").read_text() == ""
    assert (first / "ref.txt").read_text() == f"{lab.ref}\n"
    assert (first / "skills.txt").read_text() == "installed\tdemo\ninstalled\thelper\n"


# The installed skill named private is neither listed nor deleted, so it stays
# visible; a home under a folder named private, like macOS's /private/var,
# hides the same skills
@pytest.mark.parametrize("home", ["home", "private/home"])
def test_codex_hides_installed_copies_of_listed_and_deleted_skills(lab: Lab, home: str):
    moved = lab.tmp / home
    if moved != lab.home:
        shutil.copytree(lab.home, moved)
    result = run(
        lab, "--ref", str(lab.ref), "--output-dir", str(lab.out), HOME=str(moved)
    )

    assert result.returncode == 0, result.stderr
    argv = report(lab, "s2-codex", "argv").splitlines()
    installed = moved / ".codex" / "skills"
    hidden = next(arg for arg in argv if arg.startswith("skills.config="))
    assert sorted(re.findall(r'path="([^"]+)"', hidden)) == [
        str(installed / name / "SKILL.md") for name in ("demo", "gone")
    ]


def test_a_ref_without_the_skill_gives_a_no_skill_baseline(lab: Lab):
    out = lab.out
    result = run(
        lab, "--ref", str(lab.before), "--output-dir", str(out), "--agent", "codex"
    )

    assert result.returncode == 0, result.stderr
    assert report(lab, "s1-codex", "demo") == "absent\n"
    assert (out / "s1-codex" / "skills.txt").read_text() == (
        "absent\tdemo\ninstalled\thelper\n"
    )


def test_a_missing_agent_cli_stops_before_any_run(lab: Lab):
    tools = lab.tmp / "tools"
    tools.mkdir()
    for cli in ("git", "tar", "bash"):
        (tools / cli).symlink_to(shutil.which(cli) or cli)
    out = lab.out
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(out), PATH=str(tools))

    assert result.returncode == 1
    assert answer(result) == {
        "ok": False,
        "errors": [
            f"{cli} is not installed; install it, or leave its agent out with --agent"
            for cli in ("claude", "codex")
        ],
    }
    assert not out.exists()


def test_a_failed_setup_names_the_command_and_prints_every_run_on_stderr(lab: Lab):
    evals = lab.skill / "evals" / "evals.json"
    evals.write_text(json.dumps([{"query": "Go.", "setup": ["false"]}]))
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(lab.out))

    assert result.returncode == 1
    assert "s1-claude\tsetup failed: false" in result.stderr
    assert answer(result)["errors"] == [
        (
            "2 of 2 runs did not finish: s1-claude, s1-codex; "
            "read setup.log or stderr.log in each run folder"
        )
    ]
    assert answer(result)["folders"] == [
        str(lab.out / "s1-claude"),
        str(lab.out / "s1-codex"),
    ]


def test_dry_run_answers_the_folders_and_writes_nothing(lab: Lab):
    out = lab.out
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(out), "--dry-run")

    assert result.returncode == 0, result.stderr
    folders = answer(result)["folders"]
    assert isinstance(folders, list)
    assert (folders[0], len(folders)) == (str(out / "s1-claude"), 4)
    assert not out.exists()
    assert not any(lab.reports.iterdir())


@pytest.mark.parametrize(
    ("scenarios", "args", "message"),
    [
        ([{"query": "Go.", "setup": "In an empty folder"}], [], "setup must be a list"),
        ([None], [], "scenario 1 must be an object"),
        ([{"query": "Go.", "skills": "helper"}], [], "skills must be a list"),
        ([{"query": "Go.", "skills": [None]}], [], "skills must be a list"),
        ([{"query": "Go.", "skills": [" "]}], [], "skills must be a list"),
        ([{"query": "Go."}], ["--scenario", "3"], "--scenario 3 is out of range"),
        ([{"query": "Go."}], ["--ref", "no-such-ref"], "names no commit"),
    ],
)
def test_bad_input_is_a_usage_error(lab: Lab, scenarios, args, message):
    evals = lab.skill / "evals" / "evals.json"
    evals.write_text(json.dumps(scenarios))
    ref = [] if "--ref" in args else ["--ref", str(lab.ref)]
    result = run(lab, *ref, *args, "--output-dir", str(lab.out))

    assert result.returncode == 2
    failure = answer(result)
    assert message in str(failure["errors"])
    assert failure["help"] == "run_evals.py --help"


@pytest.mark.parametrize("number", [signal.SIGINT, signal.SIGTERM])
def test_an_interrupt_during_setup_launches_no_agent(lab: Lab, number):
    evals = lab.skill / "evals" / "evals.json"
    evals.write_text(
        json.dumps([{"query": "Go.", "setup": ["echo ready > ready; exec sleep 30"]}])
    )
    runner = subprocess.Popen(
        [
            sys.executable,
            str(RUNNER),
            str(lab.skill),
            "--ref",
            lab.ref,
            "--output-dir",
            str(lab.out),
            "--agent",
            "codex",
        ],
        env=lab.env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not (lab.out / "s1-codex" / "work" / "ready").exists():
            assert time.monotonic() < deadline, "setup never started"
            time.sleep(0.05)
        runner.send_signal(number)
        stdout, stderr = runner.communicate(timeout=3)
    finally:
        try:
            os.killpg(runner.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        runner.communicate()

    assert runner.returncode == 128 + number
    assert stdout == b""
    word = b"interrupted" if number == signal.SIGINT else b"terminated"
    answer = json.loads(stderr)
    assert answer["errors"] == [word.decode()]
    assert str(lab.out / "s1-codex") in answer["folders"]
    assert not any(lab.reports.iterdir())


def test_a_setup_timeout_stops_before_launching_an_agent(lab: Lab):
    evals = lab.skill / "evals" / "evals.json"
    evals.write_text(
        json.dumps([{"query": "Go.", "setup": ["echo preparing; sleep 10"]}])
    )
    # The deadline also covers the git init before the setup, which takes more
    # than 0.1s on a loaded machine
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--timeout",
        "1s",
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert "s1-codex\ttimeout" in result.stderr
    assert (lab.out / "s1-codex" / "setup.log").read_text() == "preparing\n"
    assert not any(lab.reports.iterdir())


def test_a_timeout_stops_the_whole_process_group(lab: Lab):
    late = lab.reports / "late"
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--scenario",
        "2",
        "--timeout",
        "1s",
        FAKE_ACTION=f"(trap '' TERM; sleep 2; echo late > {late}) & sleep 30",
    )
    time.sleep(3)

    assert result.returncode == 1
    assert "s2-codex\ttimeout" in result.stderr
    assert not late.exists()


def test_codex_hides_copies_under_codex_home(lab: Lab):
    home = lab.tmp / "codex-home"
    write(home / "skills" / "demo" / "SKILL.md", "installed demo\n")
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--scenario",
        "2",
        CODEX_HOME=str(home),
    )

    assert result.returncode == 0, result.stderr
    argv = report(lab, "s2-codex", "argv").splitlines()
    hidden = next(arg for arg in argv if arg.startswith("skills.config="))
    assert str(home / "skills" / "demo" / "SKILL.md") in hidden


def test_a_skill_at_the_repository_root_installs(tmp_path: Path, lab: Lab):
    repo = tmp_path / "solo-skill"
    write(repo / "SKILL.md", "solo\n")
    write(repo / "evals" / "evals.json", json.dumps([{"query": "Go."}]))
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    ref = commit(repo, "solo skill")
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            str(repo),
            "--ref",
            ref,
            "--agent",
            "codex",
            "--output-dir",
            str(lab.out),
        ],
        capture_output=True,
        text=True,
        env=lab.env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (
        lab.out / "s1-codex" / "skills.txt"
    ).read_text() == "installed\tsolo-skill\n"
    assert report(lab, "s1-codex", "demo") == "absent\n"


CREDENTIAL_PROBE = (
    'printf "%s|%s|%s|%s|%s|%s\\n" "${GH_TOKEN:-none}" "${GITHUB_TOKEN:-none}" '
    '"$GH_CONFIG_DIR" "$GIT_SSH_COMMAND" "$(git config --get-all credential.helper)" '
    '"$RUN_EVALS_PARENT" > '
)


def probe(lab: Lab, name: str) -> list[str]:
    return (lab.reports / name).read_text().strip().split("|")


def test_setup_and_agent_run_without_github_credentials(lab: Lab):
    evals = lab.skill / "evals" / "evals.json"
    setup_probe = CREDENTIAL_PROBE + str(lab.reports / "setup")
    evals.write_text(
        json.dumps([{"query": "Go.", "setup": [setup_probe, "gh issue list"]}])
    )
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        FAKE_ACTION=CREDENTIAL_PROBE + str(lab.reports / "agent") + "; gh pr list",
    )

    assert result.returncode == 0, result.stderr
    folder = lab.out / "s1-codex"
    for name in ("setup", "agent"):
        token, github_token, config, ssh, helper, parent = probe(lab, name)
        assert (token, github_token, ssh, helper, parent) == (
            "none",
            "none",
            "false",
            "",
            "1",
        )
        assert config == str(folder / "gh-config")
    assert not any((folder / "gh-config").iterdir())
    assert (folder / "gh-calls.log").read_text().splitlines() == [
        "issue list",
        "pr list",
    ]


def test_a_token_file_gives_gh_only_that_token(lab: Lab):
    token = lab.tmp / "read-only-token"
    token.write_text("read-only\n")
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--scenario",
        "2",
        "--github-token-file",
        str(token),
        FAKE_ACTION=CREDENTIAL_PROBE + str(lab.reports / "agent"),
    )

    assert result.returncode == 0, result.stderr
    assert probe(lab, "agent")[:2] == ["read-only", "none"]


def test_a_runner_inside_an_eval_run_refuses_to_start(lab: Lab):
    result = run(
        lab, "--ref", lab.ref, "--output-dir", str(lab.out), RUN_EVALS_PARENT="1"
    )

    assert result.returncode == 1
    assert "running inside an eval run" in str(answer(result)["errors"])
    assert not lab.out.exists()


def test_git_sees_no_inherited_askpass_or_auth_header(lab: Lab):
    write(
        lab.home / ".gitconfig",
        "[core]\n\taskPass = /bin/echo\n[http]\n\textraHeader = Authorization: x\n",
    )
    found = lab.reports / "git"
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--scenario",
        "2",
        GIT_ASKPASS="/bin/echo",
        SSH_ASKPASS="/bin/echo",
        FAKE_ACTION=(
            'printf "%s|%s|%s|%s\\n" "${GIT_ASKPASS:-none}" "${SSH_ASKPASS:-none}" '
            '"$(git config --get core.askPass || echo none)" '
            f'"$(git config --get-regexp "http.*extraheader" || echo none)" > {found}'
        ),
    )

    assert result.returncode == 0, result.stderr
    assert found.read_text().strip() == "none|none|none|none"


def test_a_timeout_stops_a_child_in_its_own_session(lab: Lab):
    late = lab.reports / "late"
    escape = (
        f"{sys.executable} -c 'import os, sys, time; os.setsid(); time.sleep(2); "
        f'open(sys.argv[1], "w").write("late")\' {late} & sleep 30'
    )
    result = run(
        lab,
        "--ref",
        lab.ref,
        "--output-dir",
        str(lab.out),
        "--agent",
        "codex",
        "--scenario",
        "2",
        "--timeout",
        "1s",
        FAKE_ACTION=escape,
    )
    time.sleep(3)

    assert result.returncode == 1
    assert "s2-codex\ttimeout" in result.stderr
    assert not late.exists()
