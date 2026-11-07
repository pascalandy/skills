"""The managed session lifecycle owns renewal and pre-paid authentication."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
import transcript
import youtube_session as session

URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
VALUE = "synthetic-session-must-not-appear-in-diagnostics"


def write_cookies(path: Path, value: str = VALUE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\t{value}\n",
        encoding="utf-8",
    )


def test_run_discovers_the_managed_file_without_reading_it_in_dry_run(
    monkeypatch, capsys
) -> None:
    path = session.session_file()
    write_cookies(path)
    monkeypatch.setattr(
        session, "check_session", lambda *_a, **_k: pytest.fail("network")
    )
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: pytest.fail("credentials")
    )
    assert transcript.main(["run", "youtube", "--url", URL, "--dry-run"]) == 0
    answer = json.loads(capsys.readouterr().out)
    assert answer["source"]["cookies_file"] == str(path)


@pytest.mark.parametrize("queued", [False, True])
def test_rejected_managed_session_stops_before_credentials_and_paid_work(
    monkeypatch, capsys, queued
) -> None:
    write_cookies(session.session_file())

    def reject(*_a, **_k):
        raise session.SessionError("Session expired. Run 'transcript auth refresh'")

    monkeypatch.setattr(session, "check_session", reject)
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: pytest.fail("credentials")
    )
    urls = [URL, "https://www.youtube.com/watch?v=QwpTAk_IiyU"] if queued else [URL]
    assert transcript.main(["run", "youtube", "--url", *urls, "--no-summary"]) == 1
    output = capsys.readouterr()
    assert output.out == "" and "auth refresh" in output.err
    assert VALUE not in output.err


@pytest.mark.parametrize(
    "flag,status", [(True, 200), (False, 200), (None, 200), (None, 429)]
)
def test_check_requires_positive_server_login_and_keeps_diagnostics_private(
    monkeypatch, capsys, flag, status
) -> None:
    write_cookies(session.session_file())
    original = httpx.Client

    def respond(request):
        assert VALUE in request.headers["cookie"]
        body = "ytcfg.set(" + json.dumps({"LOGGED_IN": flag}) + ");" + VALUE
        return httpx.Response(status, text=body)

    monkeypatch.setattr(
        session.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    code = transcript.main(["auth", "check"])
    output = capsys.readouterr()
    assert code == (0 if flag is True else 75 if status == 429 else 1)
    assert VALUE not in output.out + output.err
    if code == 0:
        assert json.loads(output.out)["authenticated"] is True
    else:
        assert output.out == ""


@pytest.mark.parametrize("accepted", [True, False])
def test_refresh_verifies_before_atomic_replacement_and_reports_partial_targets(
    tmp_path, monkeypatch, accepted
) -> None:
    destination = session.session_file()
    write_cookies(destination, "old-session")
    monkeypatch.setattr(session, "_export_arc", lambda path: write_cookies(path))

    def verify(path, **_kwargs):
        assert VALUE in path.read_text()
        assert "old-session" in destination.read_text()
        if not accepted:
            raise session.SessionError("Sign in again")

    def distribute(path, host, **_kwargs):
        assert VALUE in path.read_text()
        if host == "offline":
            raise session.SessionError("offline")

    monkeypatch.setattr(session, "check_session", verify)
    monkeypatch.setattr(session, "_install_remote", distribute)
    if not accepted:
        with pytest.raises(session.SessionError):
            session.refresh_session(["healthy", "offline"])
        assert "old-session" in destination.read_text()
        return
    changes, errors = session.refresh_session(["healthy", "offline"])
    assert [change[1] for change in changes] == [
        str(destination),
        "healthy:.local/share/transcript/youtube.cookies.txt",
    ]
    assert errors == ["offline"]
    assert VALUE in destination.read_text()
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700
    assert sorted(item.name for item in destination.parent.iterdir()) == [
        destination.name
    ]


def test_remote_receiver_uses_atomic_private_install_and_preserves_old_on_bad_input(
    tmp_path,
) -> None:
    remote_home = tmp_path / "remote"
    remote_home.mkdir()
    candidate = tmp_path / "candidate"
    write_cookies(candidate)
    destination = remote_home / ".local/share/transcript/youtube.cookies.txt"
    for payload, expected_code in [
        (candidate.read_bytes(), 0),
        (b"bad " + VALUE.encode(), 1),
    ]:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                Path(session.__file__).read_text()
                + "\ncheck_session = lambda *_a, **_k: None\n"
                + session.REMOTE_INSTALL,
            ],
            input=payload,
            capture_output=True,
            env={**os.environ, "HOME": str(remote_home)},
            check=False,
        )
        assert result.returncode == expected_code
        assert VALUE.encode() not in result.stdout + result.stderr
        assert destination.read_bytes() == candidate.read_bytes()
        assert stat.S_IMODE(destination.stat().st_mode) == 0o600
        assert list(destination.parent.iterdir()) == [destination]


def test_refresh_dry_run_lists_targets_without_opening_keychain_or_writing(
    monkeypatch, capsys
) -> None:
    target_file = session.targets_file()
    target_file.parent.mkdir(parents=True)
    target_file.write_text("remote-a\nuser@remote-b\nremote-a\n", encoding="utf-8")
    monkeypatch.setattr(
        session, "refresh_session", lambda *_a, **_k: pytest.fail("mutation")
    )
    assert transcript.main(["auth", "refresh", "--dry-run"]) == 0
    answer = json.loads(capsys.readouterr().out)
    assert len(answer["changes"]) == 3
    assert not session.session_file().exists()


def test_targets_reject_ssh_options_before_any_export(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        session, "refresh_session", lambda *_a, **_k: pytest.fail("export")
    )
    assert transcript.main(["auth", "refresh", "--to=-oProxyCommand=bad"]) == 1
    assert "host aliases" in capsys.readouterr().err
