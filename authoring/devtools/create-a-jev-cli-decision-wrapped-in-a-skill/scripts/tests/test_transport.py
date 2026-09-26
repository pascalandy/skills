"""Permission, credentials, the SDK transport, doctor, and the engine stamp."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from jevtest import ENGINE, TERMS_NAME, Project, add_sub


def failing(
    status: int, headers: dict[str, str] | None = None, *, times: int | None = None
) -> Any:
    calls = {"count": 0}

    def hook(
        body: dict[str, Any], response: dict[str, Any]
    ) -> tuple[int, Any, dict[str, str]] | None:
        calls["count"] += 1
        if times is None or calls["count"] <= times:
            return status, {"error": f"status {status}"}, headers or {}
        return None

    return hook


def test_permission_before_transport(project: Project) -> None:
    add_sub(project)
    denials = {
        "send_code = true": ("send_code = false", "[privacy] send_code is not true"),
        f'terms = "{TERMS_NAME}"': (
            'terms = "typesafe-2025-01-01"',
            "this engine carries the summary",
        ),
        'approved_by = "Test Owner"': (
            'approved_by = ""',
            "[privacy] approved_by is missing",
        ),
    }
    for granted, (denied, expected) in denials.items():
        project.edit_config(granted, denied)
        result = project.run_merge()
        assert result.code == 1, (denied, result)
        assert result.json["error"]["kind"] == "permission"
        assert expected in result.json["error"]["message"] or expected in json.dumps(
            result.json["error"]["problems"]
        )
        assert "nothing was sent" in result.json["error"]["remediation"]
        assert project.fake.requests == []
        preview = project.jev("run", "merge", "--dry-run", "--json", key=False)
        assert preview.code == 0, (denied, preview)
        project.edit_config(denied, granted)

    project.edit_config("send_code = true", "send_code = false")
    env_grant = project.run_merge(
        env={"JEVGATE_SEND_CODE": "true", "JEVGATE_PRIVACY": "send_code=true"}
    )
    assert env_grant.code == 1 and env_grant.json["error"]["kind"] == "permission"
    project.edit_config("send_code = false", "send_code = true")

    allowed = project.run_merge()
    assert allowed.code == 0, allowed
    record = json.loads((project.root / allowed.json["record"]).read_text())
    assert record["privacy"] == {
        "send_code": True,
        "commit_cases": True,
        "approved_by": "Test Owner",
        "approved_on": "2026-09-26",
        "terms": TERMS_NAME,
    }
    sent = len(project.fake.requests)
    project.edit_config("send_code = true", "send_code = false")
    for offline in (
        ("explain", "last"),
        ("replay", allowed.json["run_id"]),
        (
            "label",
            "last",
            "--scope",
            "gate",
            "--outcome",
            "unknown",
            "--by",
            "human",
            "--evidence",
            "still works",
        ),
    ):
        assert project.jev(*offline, key=False).code in (0, 10), offline
    assert len(project.fake.requests) == sent

    text = (project.jev_dir / "config.toml").read_text()
    project.edit(
        ".jev/config.toml",
        text[text.index("[privacy]") : text.index("# Band overrides")],
        "",
    )
    no_table = project.run_merge()
    assert no_table.code == 1 and no_table.json["error"]["kind"] == "permission"
    assert "[privacy] send_code is not true" in no_table.json["error"]["message"]
    assert len(project.fake.requests) == sent


def test_transport_errors(project: Project) -> None:
    add_sub(project)
    fake = project.fake
    missing = project.run_merge(env={"TYPESAFE_API_KEY": ""})
    assert missing.code == 1 and missing.json["error"]["kind"] == "credentials", missing
    assert (
        "chezmoi keyring has no typesafe_ai api_key" in missing.json["error"]["message"]
    )
    assert fake.requests == []

    (project.home / "chezmoi.key").write_text("key-from-the-keyring\n")
    keyring = project.run_merge(env={"TYPESAFE_API_KEY": ""})
    assert keyring.code == 0, keyring
    assert {body["_authorization"] for body in fake.requests} == {
        "Bearer key-from-the-keyring"
    }
    assert (
        "secret keyring get --service=typesafe_ai --user=api_key"
        in project.chezmoi_log.read_text()
    )
    doctor = project.jev("doctor", "--json", env={"TYPESAFE_API_KEY": ""})
    credentials = next(
        check for check in doctor.json["checks"] if check["name"] == "credentials"
    )
    assert credentials == {
        "name": "credentials",
        "status": "ok",
        "detail": "key found in chezmoi keyring (value not shown)",
        "remediation": "",
        "kind": "config",
    }
    assert "key-from-the-keyring" not in doctor.stdout + doctor.stderr
    (project.home / "chezmoi.exit").write_text("36")
    locked = project.run_merge("--no-cache", env={"TYPESAFE_API_KEY": ""})
    assert locked.code == 1 and locked.json["error"]["kind"] == "credentials"
    assert (
        "macOS keychain is locked" in locked.json["error"]["message"]
        and "TYPESAFE_API_KEY" in locked.json["error"]["message"]
    )
    (project.home / "chezmoi.exit").unlink()

    cases = {
        401: ("credentials", "TypeSafe rejected the API key", 1),
        422: ("service", "TypeSafe refused the request as invalid", 1),
        529: ("service", "stayed unavailable after at most 2 retries within 30s", 3),
        429: ("service", "stayed unavailable after at most 2 retries within 30s", 3),
    }
    for status, (kind, message, attempts) in cases.items():
        fake.requests.clear()
        fake.hooks[:] = [failing(status, {"retry-after": "0"})]
        result = project.run_merge("--no-cache")
        assert result.code == 1, (status, result)
        assert (
            result.json["error"]["kind"] == kind
            and message in result.json["error"]["message"]
        ), (status, result.json)
        assert len(fake.requests) == attempts, (status, len(fake.requests))
        assert "verdict" not in result.json

    fake.requests.clear()
    fake.hooks[:] = [failing(429, {"retry-after": "0"}, times=1)]
    recovered = project.run_merge("--no-cache")
    assert recovered.code == 0, recovered
    assert len(fake.requests) == 3, (
        "one retry for the rate-limited request, then the group request"
    )

    fake.requests.clear()
    fake.hooks[:] = [failing(529, {"retry-after": "60"})]
    started = time.monotonic()
    budget = project.run_merge("--no-cache")
    assert budget.code == 1 and budget.json["error"]["kind"] == "service"
    assert time.monotonic() - started < 20, (
        "a retry-after beyond the 30s budget is not waited out"
    )
    assert len(fake.requests) == 1
    fake.hooks.clear()


def test_engine_stamp(project: Project) -> None:
    canonical = project.jev("version", "--json", key=False)
    assert canonical.json["modified"] is False
    assert canonical.json["hash"] == canonical.json["stamped_hash"]
    assert ENGINE.read_bytes() == (project.jev_dir / "jevgate.py").read_bytes()

    engine = project.jev_dir / "jevgate.py"
    engine.write_text(engine.read_text() + "\n# local tweak for this project\n")
    project.commit("Tweak the vendored engine")
    edited = project.jev("version", "--json", key=False)
    assert (
        edited.json["modified"] is True
        and edited.json["hash"] != edited.json["stamped_hash"]
    )
    doctor = project.jev("doctor", "--json")
    check = next(item for item in doctor.json["checks"] if item["name"] == "engine")
    assert check["status"] == "warn" and "edited locally" in check["detail"]
    add_sub(project)
    run = project.run_merge()
    assert run.json["engine"] == {
        "version": "0.1.1",
        "hash": edited.json["hash"],
        "modified": True,
    }
    record = json.loads((project.root / run.json["record"]).read_text())
    assert record["engine"]["modified"] is True


def test_doctor_readiness(tmp_path: Path, project: Project) -> None:
    ready = project.jev("doctor", "--json")
    assert ready.code == 0, ready
    offline = {
        "runtime": "ok",
        "sdk": "ok",
        "engine": "ok",
        "git": "ok",
        "secret scan": "ok",
        "config": "ok",
        "gate merge": "ok",
        "ignore rules": "ok",
        "integration ref": "ok",
        "credentials": "ok",
        "permission": "ok",
        "case policy": "ok",
    }
    statuses = {check["name"]: check["status"] for check in ready.json["checks"]}
    assert statuses == offline
    assert project.fake.model_requests == 0 and project.fake.requests == []

    # A35: the alias-only listing passes without inference, even though the
    # pin jev-1.13.0 is not among the listed names.
    online = project.jev("doctor", "--online", "--json")
    assert online.code == 0, online
    statuses = {check["name"]: check["status"] for check in online.json["checks"]}
    assert statuses == {**offline, "models": "ok"}
    models = next(check for check in online.json["checks"] if check["name"] == "models")
    assert models["detail"] == "authenticated listing: jev-latest, jev-preview"
    assert project.fake.model_requests == 1 and project.fake.requests == []

    # A rejected key fails as credentials; any other listing failure is service.
    for status, kind in ((401, "credentials"), (529, "service")):
        project.fake.models_failure = (status, {"retry-after": "0"})
        listing = project.jev("doctor", "--online", "--json")
        assert listing.code == 1 and listing.json["error"]["kind"] == kind, listing
        names = [c["name"] for c in listing.json["checks"] if c["status"] == "fail"]
        assert names == ["models"], listing
    project.fake.models_failure = None
    assert project.fake.requests == []

    project.edit_config("send_code = true", "send_code = false")
    denied = project.jev("doctor", "--json", env={"TYPESAFE_API_KEY": ""})
    assert denied.code == 1
    failed = {
        check["name"] for check in denied.json["checks"] if check["status"] == "fail"
    }
    assert failed == {"credentials", "permission"}
    assert denied.json["error"]["kind"] == "credentials"

    bare = tmp_path / "canonical"
    bare.mkdir()
    shutil.copy2(ENGINE, bare / "jevgate.py")
    fresh = Project(tmp_path / "empty", project.home, project.fake)
    fresh.root.mkdir()
    process = subprocess.run(
        [sys.executable, str(bare / "jevgate.py"), "doctor", "--json"],
        cwd=fresh.root,
        env=fresh.live_env(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    report = json.loads(process.stdout)
    config = next(check for check in report["checks"] if check["name"] == "config")
    assert config["status"] == "setup" and process.returncode == 0, process.stderr
