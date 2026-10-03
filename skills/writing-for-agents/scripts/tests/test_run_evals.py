from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
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
    write(skills / "helper" / "SKILL.md", "helper\n")
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
        {"skills": ["demo"], "query": "Second request."},
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
    }
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
    )


def report(lab: Lab, name: str, file: str) -> str:
    return (lab.reports / name / file).read_text(encoding="utf-8")


def test_each_scenario_runs_in_each_agent_with_the_skill_from_the_ref(lab: Lab):
    out = lab.out
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(out))

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"s1-claude\tdone\t{out / 's1-claude'}",
        f"s1-codex\tdone\t{out / 's1-codex'}",
        f"s2-claude\tdone\t{out / 's2-claude'}",
        f"s2-codex\tdone\t{out / 's2-codex'}",
    ]
    assert report(lab, "s1-claude", "demo") == "demo v2\n"
    assert report(lab, "s1-codex", "demo") == "demo v2\n"
    assert report(lab, "s1-claude", "skills").split() == ["demo", "helper"]
    assert "Tidy the notes." in report(lab, "s1-claude", "argv").splitlines()
    assert report(lab, "s1-codex", "stdin") == "Tidy the notes."
    first = out / "s1-claude"
    assert (first / "answer.md").read_text() == "claude answer"
    assert (out / "s1-codex" / "answer.md").read_text() == "codex answer\n"
    assert "base" in (first / "git-log.txt").read_text()
    assert (first / "git-status.txt").read_text() == ""
    assert (first / "ref.txt").read_text() == f"{lab.ref}\n"
    assert (first / "skills.txt").read_text() == "installed\tdemo\ninstalled\thelper\n"


def test_codex_hides_installed_copies_of_listed_and_deleted_skills(lab: Lab):
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(lab.out))

    assert result.returncode == 0, result.stderr
    argv = report(lab, "s2-codex", "argv").splitlines()
    installed = lab.home / ".codex" / "skills"
    hidden = next(arg for arg in argv if arg.startswith("skills.config="))
    assert str(installed / "demo" / "SKILL.md") in hidden
    assert str(installed / "gone" / "SKILL.md") in hidden
    assert "private" not in hidden


def test_gh_wrapper_logs_every_call_and_refuses_writes(lab: Lab):
    out = lab.out
    result = run(
        lab,
        "--ref",
        str(lab.ref),
        "--output-dir",
        str(out),
        "--agent",
        "claude",
        "--scenario",
        "2",
        FAKE_ACTION="gh issue view 1; gh pr create --title x || true",
    )

    assert result.returncode == 0, result.stderr
    calls = (out / "s2-claude" / "gh-calls.log").read_text().splitlines()
    assert calls == [
        "issue view 1",
        "pr create --title x",
        "REFUSED pr create --title x",
    ]
    real = lab.reports / "real-gh.log"
    assert real.read_text() == "issue view 1\n"


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
    assert result.stdout == ""
    assert "claude is not installed" in result.stderr
    assert "codex is not installed" in result.stderr
    assert not out.exists()


def test_a_failed_setup_names_the_command_and_prints_every_run_on_stderr(lab: Lab):
    evals = lab.skill / "evals" / "evals.json"
    evals.write_text(json.dumps([{"query": "Go.", "setup": ["false"]}]))
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(lab.out))

    assert result.returncode == 1
    assert result.stdout == ""
    assert "s1-claude\tsetup failed: false" in result.stderr
    assert "2 of 2 runs did not finish" in result.stderr


def test_dry_run_prints_the_plan_and_writes_nothing(lab: Lab):
    out = lab.out
    result = run(lab, "--ref", str(lab.ref), "--output-dir", str(out), "--dry-run")

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines()[0] == f"s1-claude\tplanned\t{out / 's1-claude'}"
    assert len(result.stdout.splitlines()) == 4
    assert not out.exists()
    assert not any(lab.reports.iterdir())


@pytest.mark.parametrize(
    ("scenarios", "args", "message"),
    [
        ([{"query": "Go.", "setup": "In an empty folder"}], [], "setup must be a list"),
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
    assert message in result.stderr
    assert result.stdout == ""
