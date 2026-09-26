"""Help, exit codes, output formats, advisory authority, and configuration precedence."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from jevtest import FakeTypeSafe, Project, add_sub, kinds, make_project


def uv_dirs() -> dict[str, str]:
    found = {}
    for variable, command in (
        ("UV_CACHE_DIR", ["uv", "cache", "dir"]),
        ("UV_PYTHON_INSTALL_DIR", ["uv", "python", "dir"]),
    ):
        found[variable] = subprocess.run(
            command, capture_output=True, text=True, check=True
        ).stdout.strip()
    return found


def test_recipe_help_offline(tmp_path: Path, fake: FakeTypeSafe) -> None:
    project = make_project(tmp_path, fake, justfile=True)
    just = shutil.which("just")
    assert just, "just must be on PATH; run this suite through `just test-jevgate`"
    online = {**project.base_env(), **uv_dirs()}
    for variable in ("HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY"):
        online.pop(variable, None)
        if variable in os.environ:
            online[variable] = os.environ[variable]
    bootstrap = subprocess.run(
        [just, "jev", "version"],
        cwd=project.root,
        env=online,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert bootstrap.returncode == 0, bootstrap.stderr

    offline = {**project.base_env(), **uv_dirs(), "UV_OFFLINE": "1"}
    before = project.snapshot()

    def just_run(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [just, *args],
            cwd=project.root,
            env=offline,
            capture_output=True,
            text=True,
            timeout=120,
        )

    top = just_run("jev")
    assert top.returncode == 0, top.stderr
    assert top.stdout.startswith("usage: jevgate <command>")
    merge_help = just_run("jev-merge", "--help")
    assert merge_help.returncode == 0, merge_help.stderr
    assert "merge: Is this PR ready to merge into main?" in merge_help.stdout
    assert (
        "steering_attempt" in merge_help.stdout
        and "favorable <= 0.20" in merge_help.stdout
    )
    assert merge_help.stdout.count("  just jev-merge") == 2
    direct = just_run("jev", "run", "merge", "--help")
    assert direct.stdout == merge_help.stdout
    noisy = just_run("jev-merge", "--dry-run", "--base", "nowhere", "-h")
    assert noisy.returncode == 0 and noisy.stdout == merge_help.stdout

    assert fake.requests == [] and fake.model_requests == 0
    assert project.check_runs() == 0
    assert not project.gh_log.exists() and not project.chezmoi_log.exists()
    assert project.snapshot() == before
    assert project.git("status", "--porcelain") == ""


def test_verdict_exits(project: Project) -> None:
    add_sub(project)
    passed = project.run_merge()
    assert passed.code == 0, passed
    assert passed.json["verdict"] == "pass" and passed.json["reasons"] == []

    project.fake.answer("risk_deploy_config", 0.97)
    escalated = project.run_merge("--no-cache")
    assert escalated.code == 10, escalated
    assert escalated.json["verdict"] == "escalate"

    project.set_check_exit(1)
    sent = len(project.fake.requests)
    blocked = project.jev("run", "merge", "--run-ci", "--json")
    assert blocked.code == 11, blocked
    assert kinds(blocked) == ["check_red"]
    assert len(project.fake.requests) == sent

    unknown = project.jev("run", "merge", "--json")
    assert unknown.code == 12, unknown
    assert kinds(unknown) == ["check_unknown"]
    assert len(project.fake.requests) == sent

    for usage in (
        ("run", "merge", "--ci-status", "pass"),
        ("run", "merge", "--model", "jev-latest"),
        ("launch",),
        ("run",),
    ):
        result = project.jev(*usage)
        assert result.code == 2, (usage, result)
        assert result.stderr.startswith("error: ")

    no_key = project.jev(
        "run",
        "merge",
        "--ci-status",
        "pass",
        "--ci-sha",
        "HEAD",
        "--no-cache",
        "--json",
        key=False,
    )
    assert no_key.code == 1, no_key
    assert no_key.json["error"]["kind"] == "credentials"
    assert "rerun with --verbose for details" in no_key.stderr


def test_output_parity(project: Project) -> None:
    add_sub(project)
    project.fake.answer("test_weakened", 0.5)
    project.fake.answer("risk_public_api", 0.7)
    project.fake.answer("behavior_tested", 0.1, group="src")
    machine = project.run_merge()
    human = project.jev("run", "merge", "--ci-status", "pass", "--ci-sha", "HEAD")
    assert machine.code == human.code == 10, (machine, human)
    lines = human.stdout.splitlines()
    rows = machine.json["answers"]
    assert rows
    for row in rows:
        shown = f"{row['answer']} {row['value']:.2f}   {row['band_label']}"
        assert any(row["label"] in line and shown in line for line in lines), (
            row,
            human.stdout,
        )
    labels = {row["band_label"] for row in rows}
    assert {
        "uncertain 0.20-0.80",
        "flagged >= 0.50",
        "adverse <= 0.20",
        "favorable >= 0.80",
    } <= labels
    count = len(machine.json["reasons"])
    assert f"verdict: escalate (advisory), {count} reasons" in human.stdout
    for number, reason in enumerate(machine.json["reasons"], 1):
        assert f"  {number}. {reason['message']} -> review" in human.stdout
    quiet = project.jev("run", "merge", "--ci-status", "pass", "--ci-sha", "HEAD", "-q")
    assert quiet.stdout.strip() == f"verdict: escalate (advisory), {count} reasons"
    assert quiet.stderr == ""
    both = project.jev(
        "run", "merge", "--ci-status", "pass", "--ci-sha", "HEAD", "-q", "--json"
    )
    assert both.json["answers"] == rows


def test_advisory_authority(project: Project) -> None:
    add_sub(project)
    assert project.run_merge().json["advisory"] is True
    worst = {
        "steering_attempt": 0.99,
        "claim_describes_change": 0.99,
        "claim_supported": 0.01,
        "behavior_tested": 0.01,
        "test_weakened": 0.99,
        "unrelated_change": 0.99,
        "rule_violated": 0.99,
    }
    for name, value in worst.items():
        project.fake.answer(name, value)
    for area in (
        "data_migration",
        "auth_or_secrets",
        "public_api",
        "concurrency",
        "deploy_config",
        "dependency_upgrade",
        "other",
    ):
        project.fake.answer(f"risk_{area}", 1.0)
    result = project.run_merge("--no-cache")
    assert result.code == 10, result
    assert result.json["advisory"] is True
    assert {reason["class"] for reason in result.json["reasons"]} == {"escalate"}
    assert all(reason["route"] == "review" for reason in result.json["reasons"])
    human = project.jev("run", "merge", "--ci-status", "pass", "--ci-sha", "HEAD")
    assert "verdict: escalate (advisory)" in human.stdout
    project.set_check_exit(1)
    blocked = project.jev("run", "merge", "--run-ci", "--json")
    assert blocked.code == 11 and blocked.json["advisory"] is True
    assert kinds(blocked) == ["check_red"]


def test_config_precedence(project: Project) -> None:
    add_sub(project)
    env_model = project.run_merge(env={"JEVGATE_MODEL": "jev-1.14.0"})
    assert env_model.code == 0, env_model
    assert env_model.json["model"] == {
        "requested": "jev-1.14.0",
        "answered": "jev-1.14.0",
    }
    record = json.loads((project.root / env_model.json["record"]).read_text())
    assert record["settings"]["sources"]["model"] == "env JEVGATE_MODEL"
    flag_model = project.run_merge(
        "--model", "jev-1.15.0", env={"JEVGATE_MODEL": "jev-1.14.0"}
    )
    assert flag_model.json["model"]["requested"] == "jev-1.15.0"

    project.edit_config("max_requests = 100", "max_requests = 1")
    capped = project.run_merge("--no-cache")
    assert capped.json["usage"]["requests"] == 1
    env_cap = project.run_merge("--no-cache", env={"JEVGATE_MAX_REQUESTS": "2"})
    assert env_cap.json["usage"]["requests"] == 2
    flag_cap = project.run_merge(
        "--no-cache", "--max-requests", "3", env={"JEVGATE_MAX_REQUESTS": "2"}
    )
    assert flag_cap.json["usage"]["requests"] == 2  # author request plus the one group

    project.edit_config('model = "jev-1.13.0"', 'model = "jev-latest"')
    alias = project.run_merge()
    assert alias.code == 1 and alias.json["error"]["kind"] == "config"
    assert "versioned model ID" in alias.json["error"]["message"]
    project.edit_config(
        'model = "jev-latest"', 'model = "jev-1.13.0"\nsend_everything = true'
    )
    unknown = project.run_merge()
    assert unknown.code == 1 and "unknown key 'send_everything'" in unknown.stderr


def test_version_reports_stamp(project: Project) -> None:
    result = project.jev("version", "--json", key=False)
    assert result.code == 0, result
    assert result.json["version"] == "0.1.0"
    assert (
        result.json["hash"].startswith("sha256:") and result.json["modified"] is False
    )
    assert project.jev("version").stdout.strip().endswith("unmodified")


def test_help_falls_back_on_invalid_config(project: Project) -> None:
    (project.jev_dir / "gates" / "merge.toml").write_text("id = [unterminated\n")
    result = project.jev("run", "merge", "--run-ci", "--help", key=False)
    assert result.code == 0, result
    assert result.stdout.startswith("usage: jevgate run <gate>")
    assert (
        "is not valid TOML" in result.stderr
        and "showing the generic run help" in result.stderr
    )
    unknown = project.jev("help", "nonsense", key=False)
    assert unknown.code == 0 and unknown.stdout.startswith("usage: jevgate <command>")
    assert "neither a command nor a gate" in unknown.stderr
    for command in ("gates", "explain", "replay", "label", "version", "help"):
        shown = project.jev(command, "--help", key=False)
        assert shown.code == 0 and shown.stdout.startswith(
            f"usage: jevgate {command}"
        ), command
    assert project.check_runs() == 0 and project.fake.requests == []
