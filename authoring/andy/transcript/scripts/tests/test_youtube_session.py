"""The fnox vault holds the session; reading, renewal and pre-paid authentication."""

from __future__ import annotations

import json
import logging
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
import transcript
import youtube_session as session

REAL_FNOX_RUN = session._fnox_run

URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
VALUE = "synthetic-session-must-not-appear-in-diagnostics"


@pytest.fixture(autouse=True)
def isolated_session_config(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))


def write_cookies(path: Path, value: str = VALUE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\t{value}\n",
        encoding="utf-8",
    )


LABEL = session.VAULT_LABEL
COOKIES = f"# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t0\tSID\t{VALUE}\n"
STORE_LINE = 'YOUTUBE_COOKIES_TXT= { provider = "age", value = "CIPHERTEXT" }'


class FakeFnox:
    """A stand-in for `_fnox_run` that keeps the vault value in memory."""

    def __init__(self, *, listed: bool = True, stored: str | None = COOKIES) -> None:
        self.listed = listed
        self.stored = stored
        self.calls: list[list[str]] = []
        self.stdin: list[str | None] = []

    def __call__(self, arguments, *, stdin=None, timeout=15):
        arguments = list(arguments)
        self.calls.append(arguments)
        self.stdin.append(stdin)
        ok = subprocess.CompletedProcess(arguments, 0, "", "")
        if arguments == ["list"]:
            key = (
                f" {session.VAULT_KEY}  provider (age) [file]\n" if self.listed else ""
            )
            return subprocess.CompletedProcess(arguments, 0, key, "")
        if "set" in arguments:
            self.stored = stdin
            store = Path(arguments[arguments.index("-c") + 1])
            kept = [
                line
                for line in store.read_text(encoding="utf-8").splitlines()
                if not line.startswith(session.VAULT_KEY)
            ]
            store.write_text("\n".join([*kept, STORE_LINE, ""]), encoding="utf-8")
            return ok
        if "exec" in arguments and self.stored is not None:
            target = Path(arguments[-1])
            if arguments[-2] == "sh" and "cmp" in arguments[-3]:
                same = target.read_text(encoding="utf-8") == self.stored
                return subprocess.CompletedProcess(arguments, 0 if same else 1, "", "")
            target.write_text(self.stored, encoding="utf-8")
            return ok
        return subprocess.CompletedProcess(arguments, 1, "", "no such secret")


def use_vault(monkeypatch, fnox: FakeFnox) -> FakeFnox:
    monkeypatch.setattr(session, "_fnox_run", fnox)
    return fnox


def test_the_vault_is_the_cookie_source_when_no_cookies_file_is_given(
    monkeypatch, capsys
) -> None:
    fnox = use_vault(monkeypatch, FakeFnox())
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: pytest.fail("credentials")
    )

    assert transcript.select_youtube_auth(None) == transcript.CookieFile(
        verify_session=True
    )
    assert transcript.main(["run", "youtube", "--url", URL, "--dry-run"]) == 0
    answer = json.loads(capsys.readouterr().out)
    assert answer["source"]["cookies_file"] == LABEL
    # A dry run names the source from `fnox list`, never from a decryption
    assert all(call == ["list"] for call in fnox.calls)


def test_an_explicit_cookies_file_wins_over_the_vault(monkeypatch, tmp_path) -> None:
    fnox = use_vault(monkeypatch, FakeFnox())
    explicit = tmp_path / "mine.txt"
    write_cookies(explicit)

    selected = transcript.select_youtube_auth(explicit)

    assert selected == transcript.CookieFile(explicit.resolve())
    assert not selected.verify_session and fnox.calls == []


@pytest.mark.parametrize("fnox", [None, FakeFnox(listed=False)])
def test_without_a_vault_entry_runs_stay_anonymous(monkeypatch, fnox) -> None:
    monkeypatch.setattr(session, "_fnox_run", fnox or (lambda *_a, **_k: None))

    assert transcript.select_youtube_auth(None) == "anonymous"


def test_an_enclosing_fnox_exec_provides_the_cookie_file(monkeypatch, tmp_path) -> None:
    outer = tmp_path / "outer-cookies.txt"
    outer.write_text(COOKIES, encoding="utf-8")
    monkeypatch.setenv(session.VAULT_KEY, str(outer))
    monkeypatch.setattr(
        session, "_fnox_run", lambda *_a, **_k: pytest.fail("fnox ran again")
    )

    source = transcript.select_youtube_auth(None)
    with transcript.private_cookie_file(source) as copy:
        assert copy != outer and copy.read_text(encoding="utf-8") == COOKIES


def test_vault_cookies_exist_only_in_a_private_temporary_copy(
    monkeypatch, tmp_path
) -> None:
    fnox = use_vault(monkeypatch, FakeFnox())
    seen = []

    with transcript.private_cookie_file(transcript.CookieFile()) as copy:
        seen.append(copy)
        assert copy.read_text(encoding="utf-8") == COOKIES
        assert copy.stat().st_mode & 0o777 == 0o600
        assert copy.parent.stat().st_mode & 0o777 == 0o700

    assert not seen[0].exists() and not seen[0].parent.exists()
    exec_call = fnox.calls[0]
    assert exec_call[:6] == [
        "exec",
        "--only",
        session.VAULT_KEY,
        "--if-missing",
        "error",
        "--",
    ]
    assert VALUE not in " ".join(exec_call)


def test_fnox_candidates_move_on_only_when_the_executable_is_missing(
    monkeypatch,
) -> None:
    tried = []

    def run(command, **_kwargs):
        tried.append(command[0])
        if command[0] != session.FNOX_CANDIDATES[2]:
            raise FileNotFoundError
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(session, "run_process", run)
    assert REAL_FNOX_RUN(["list"]) is not None
    assert tried == list(session.FNOX_CANDIDATES)

    tried.clear()

    def broken(command, **_kwargs):
        tried.append(command[0])
        raise subprocess.TimeoutExpired(command, 15)

    monkeypatch.setattr(session, "run_process", broken)
    with pytest.raises(session.SessionError):
        REAL_FNOX_RUN(["list"])
    assert tried == [session.FNOX_CANDIDATES[0]]


@pytest.mark.parametrize("queued", [False, True])
def test_vault_session_is_verified_before_credentials_and_paid_work(
    monkeypatch, capsys, queued
) -> None:
    use_vault(monkeypatch, FakeFnox())
    checked = []

    def reject(path, **_k):
        checked.append(path.read_text(encoding="utf-8"))
        raise session.SessionError("Session expired. Run 'transcript auth refresh'")

    monkeypatch.setattr(session, "check_session", reject)
    monkeypatch.setattr(
        transcript, "validate_env", lambda *_a: pytest.fail("credentials")
    )
    urls = [URL, "https://www.youtube.com/watch?v=QwpTAk_IiyU"] if queued else [URL]
    assert transcript.main(["run", "youtube", "--url", *urls, "--no-summary"]) == 1
    output = capsys.readouterr()
    assert checked == [COOKIES]
    assert output.out == "" and "fix: just transcript-auth-refresh" in output.err
    assert VALUE not in output.err


def test_an_accepted_vault_session_reaches_credentials(monkeypatch) -> None:
    use_vault(monkeypatch, FakeFnox())
    monkeypatch.setattr(session, "check_session", lambda *_a, **_k: None)
    reached = []

    def credentials(*_a):
        reached.append(True)
        raise transcript.CredentialError("stop here")

    monkeypatch.setattr(transcript, "validate_env", credentials)

    assert transcript.main(["run", "youtube", "--url", URL, "--no-summary"]) == 1
    assert reached == [True]


@pytest.mark.parametrize(
    "flag,status", [(True, 200), (False, 200), (None, 200), (None, 429)]
)
def test_check_requires_positive_server_login_and_keeps_diagnostics_private(
    monkeypatch, capsys, flag, status
) -> None:
    use_vault(monkeypatch, FakeFnox())
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
        assert json.loads(output.out) == {
            "ok": True,
            "authenticated": True,
            "file": LABEL,
        }
    else:
        assert output.out == ""


def test_check_without_a_vault_entry_names_the_refresh(monkeypatch, capsys) -> None:
    use_vault(monkeypatch, FakeFnox(listed=False))

    assert transcript.main(["auth", "check"]) == 1
    assert "just transcript-auth-refresh" in capsys.readouterr().err


def test_the_session_check_keeps_http_transport_logs_out_of_debug(
    monkeypatch, tmp_path, caplog
) -> None:
    cookies = tmp_path / "cookies.txt"
    write_cookies(cookies)
    set_cookie = "SID=synthetic-set-cookie-value; Path=/"

    def respond(request):
        # What httpcore's debug records carry for a real response
        for name in session.HTTP_LOGGERS:
            logging.getLogger(f"{name}.http11").debug(
                "receive_response_headers.complete return_value=%r",
                [(b"Set-Cookie", set_cookie.encode())],
            )
        body = "ytcfg.set(" + json.dumps({"LOGGED_IN": True}) + ");"
        return httpx.Response(200, text=body, headers={"Set-Cookie": set_cookie})

    original = httpx.Client
    monkeypatch.setattr(
        session.httpx,
        "Client",
        lambda **kwargs: original(**kwargs, transport=httpx.MockTransport(respond)),
    )
    # A caller may set DEBUG on a child logger explicitly; the guard still holds
    child = logging.getLogger("httpcore.http11")
    before = child.level
    child.setLevel(logging.DEBUG)
    try:
        with caplog.at_level(logging.DEBUG):
            session.check_session(cookies)
            child.debug("after the check")
    finally:
        child.setLevel(before)

    assert "synthetic-set-cookie-value" not in caplog.text
    assert "after the check" in caplog.text  # the loggers work again afterwards
    assert not child.disabled


@pytest.mark.parametrize("failure", ["exit", "timeout"])
def test_a_failed_vault_listing_is_an_error_not_an_absent_entry(
    monkeypatch, capsys, failure
) -> None:
    def run(command, **_kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(command, 15)
        return subprocess.CompletedProcess(command, 2, "", "boom")

    monkeypatch.setattr(session, "_fnox_run", REAL_FNOX_RUN)
    monkeypatch.setattr(session, "run_process", run)
    monkeypatch.setattr(session, "FNOX_CANDIDATES", ("fnox",))
    monkeypatch.delenv(session.VAULT_KEY, raising=False)

    with pytest.raises(session.SessionError):
        session.vault_available()
    # No transport is chosen: a run cannot slip into anonymous access
    with pytest.raises(transcript.ConfigurationError):
        transcript.select_youtube_auth(None)
    assert transcript.main(["auth", "check"]) == 1
    error = capsys.readouterr().err
    assert "not in the vault" not in error and "just transcript-auth-refresh" not in error


def test_a_missing_fnox_or_an_omitting_listing_is_the_only_anonymous_fallback(
    monkeypatch,
) -> None:
    monkeypatch.delenv(session.VAULT_KEY, raising=False)
    monkeypatch.setattr(session, "_fnox_run", lambda *_a, **_k: None)
    assert session.vault_available() is False
    use_vault(monkeypatch, FakeFnox(listed=False))
    assert session.vault_available() is False


class ShellFnox:
    """A `_fnox_run` that runs the child shell command with the vault value in
    $YOUTUBE_COOKIES_TXT, and PATH shims that record any external call."""

    def __init__(self, tmp_path: Path, value: str) -> None:
        shims = tmp_path / "shims"
        shims.mkdir()
        self.calls = tmp_path / "external-calls"
        for name in ("cp", "cmp", "test"):
            shim = shims / name
            shim.write_text(f'#!/bin/sh\necho "$@" >> "{self.calls}"\n')
            shim.chmod(0o755)
        self.env = {"PATH": f"{shims}:/usr/bin:/bin", session.VAULT_KEY: value}

    def __call__(self, arguments, *, stdin=None, timeout=15):
        arguments = list(arguments)
        if "set" in arguments:
            store = Path(arguments[arguments.index("-c") + 1])
            store.write_text(f"[secrets]\n{STORE_LINE[:-1]}, as_file = true }}\n")
            return subprocess.CompletedProcess(arguments, 0, "", "")
        command = arguments[arguments.index("--") + 1 :]
        return subprocess.run(
            command, env=self.env, capture_output=True, text=True, check=False
        )


def test_a_vault_value_that_is_not_a_file_never_reaches_an_external_command(
    monkeypatch, tmp_path
) -> None:
    raw = "synthetic-raw-value-not-a-path"
    monkeypatch.delenv(session.VAULT_KEY, raising=False)
    shell = ShellFnox(tmp_path, raw)
    monkeypatch.setattr(session, "_fnox_run", shell)
    destination = tmp_path / "copy.txt"
    candidate = tmp_path / "candidate.txt"
    write_cookies(candidate)

    with pytest.raises(session.SessionError, match="as_file") as copied:
        session.copy_vault_cookies(destination)
    root = make_dotfiles(tmp_path)
    with pytest.raises(session.SessionError, match="as_file") as written:
        session.write_vault(candidate, session.vault_source(root))

    assert not shell.calls.exists() and not destination.exists()
    assert raw not in f"{copied.value} {written.value}"

def git(directory: Path, *arguments: str) -> None:
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=test",
            "-c",
            "user.email=test@example.com",
            "-C",
            str(directory),
            *arguments,
        ],
        check=True,
        capture_output=True,
    )


def make_clone(tmp_path: Path) -> Path:
    """An ordinary dotfiles clone holding the fnox store, like chezmoi's source."""
    clone = tmp_path / "dotfiles-clone"
    store = clone / session.VAULT_SOURCE
    store.parent.mkdir(parents=True)
    store.write_text('[secrets]\nOTHER= { provider = "age", value = "X" }\n')
    git(clone, "init", "-q")
    git(clone, "add", ".")
    git(clone, "commit", "-q", "-m", "init")
    return clone


def make_dotfiles(tmp_path: Path, name: str = "dotfiles-worktree") -> Path:
    """A linked worktree of that clone, the only folder a refresh may write."""
    clone = make_clone(tmp_path)
    root = tmp_path / name
    git(clone, "worktree", "add", "-q", "--no-checkout", "-b", "refresh", str(root))
    store = root / session.VAULT_SOURCE
    store.parent.mkdir(parents=True)
    shutil.copyfile(clone / session.VAULT_SOURCE, store)
    return root


@pytest.mark.parametrize("accepted", [True, False])
def test_refresh_verifies_then_writes_only_the_vault_never_a_plaintext_file(
    tmp_path, monkeypatch, accepted
) -> None:
    root = make_dotfiles(tmp_path)
    store = root / session.VAULT_SOURCE
    before = store.read_text()
    fnox = use_vault(monkeypatch, FakeFnox(stored=None))
    export_paths = []

    def export(path):
        export_paths.append(path)
        write_cookies(path)

    def verify(path, **_kwargs):
        assert VALUE in path.read_text()
        assert fnox.calls == []  # verified before any vault write
        if not accepted:
            raise session.SessionError("Sign in again")

    monkeypatch.setattr(session, "_export_helium", export)
    monkeypatch.setattr(session, "check_session", verify)

    if not accepted:
        with pytest.raises(session.SessionError):
            session.refresh_session(root)
        assert fnox.calls == [] and store.read_text() == before
        return
    changes, steps = session.refresh_session(root)

    assert changes == [["update", f"{LABEL} in {store}"]]
    set_call = next(call for call in fnox.calls if "set" in call)
    assert set_call[set_call.index("set") :] == [
        "set",
        session.VAULT_KEY,
        "--provider",
        "age",
        "--from-file",
        "/dev/stdin",
    ]
    assert set_call[set_call.index("-c") + 1] == str(store)
    assert fnox.stdin[fnox.calls.index(set_call)] == fnox.stored
    assert VALUE in fnox.stored and VALUE not in json.dumps(fnox.calls)
    # fnox set dropped as_file; refresh restores it on the entry's line
    assert (
        'YOUTUBE_COOKIES_TXT= { provider = "age", value = "CIPHERTEXT", as_file = true }'
        in store.read_text()
    )
    assert "OTHER=" in store.read_text()
    # The export lived in a temporary directory that is gone, and no cookie file remains
    assert export_paths and not export_paths[0].exists()
    files = sorted(
        path.name
        for path in tmp_path.rglob("*")
        if path.is_file() and ".git" not in path.parts and path.name != ".git"
    )
    # the clone's tracked store and the worktree's checkout of it, nothing else
    assert files == ["private_config.toml"] * 2
    assert "just merge" in " ".join(steps) and VALUE not in " ".join(steps)


def test_refresh_steps_start_in_the_quoted_dotfiles_worktree(
    tmp_path, monkeypatch
) -> None:
    root = make_dotfiles(tmp_path, "dotfiles worktree")
    use_vault(monkeypatch, FakeFnox(stored=None))
    monkeypatch.setattr(session, "_export_helium", lambda path: write_cookies(path))
    monkeypatch.setattr(session, "check_session", lambda *_a, **_k: None)

    _, steps = session.refresh_session(root)

    in_root = f"cd {shlex.quote(str(root))} && "
    handoff = steps[:-1]  # the last step re-checks the session from anywhere
    assert len(handoff) == 5 and all(step.startswith(in_root) for step in handoff)
    assert "auth check" in steps[-1]
    assert next(step for step in steps if "gh pr create" in step) == (
        in_root + "git push -u origin HEAD && gh pr create --fill"
    )


def test_refresh_refuses_a_folder_that_is_not_a_dotfiles_worktree(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(session, "_export_helium", lambda *_a: pytest.fail("export"))
    with pytest.raises(session.SessionError, match="not a dotfiles worktree"):
        session.refresh_session(tmp_path)


def test_refresh_refuses_the_ordinary_clone_and_a_subfolder(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(session, "_export_helium", lambda *_a: pytest.fail("export"))
    worktree = make_dotfiles(tmp_path)
    clone = tmp_path / "dotfiles-clone"
    nested = worktree / "dot_config" / "private_fnox"
    (nested / session.VAULT_SOURCE).parent.mkdir(parents=True)
    (nested / session.VAULT_SOURCE).touch()

    for refused in (clone, nested):
        with pytest.raises(session.SessionError, match="linked git worktree"):
            session.refresh_session(refused)
    assert session.vault_source(worktree) == worktree / session.VAULT_SOURCE


def test_refresh_dry_run_names_the_vault_without_opening_keychain_or_writing(
    tmp_path, monkeypatch, capsys
) -> None:
    root = make_dotfiles(tmp_path)
    monkeypatch.setattr(
        session, "refresh_session", lambda *_a, **_k: pytest.fail("mutation")
    )
    code = transcript.main(
        ["auth", "refresh", "--dry-run", "--dotfiles-worktree", str(root)]
    )
    answer = json.loads(capsys.readouterr().out)
    assert code == 0
    assert answer["changes"] == [
        ["update", f"{LABEL} in {root / session.VAULT_SOURCE}"]
    ]


def test_refresh_leaves_no_ssh_or_target_file_options() -> None:
    help_text = transcript.build_parser().format_help()
    for retired in ("--to", "youtube-targets"):
        assert retired not in help_text
    assert not hasattr(session, "targets_file") and not hasattr(session, "session_file")


@pytest.mark.parametrize(
    "config_text,expected",
    [
        (None, "YouTube session configuration is missing"),
        ("profile_name = [", "could not be read as TOML"),
        ('browser_data_dir = "/synthetic/browser"\n', "Set profile_name"),
    ],
)
def test_refresh_reports_unusable_config_before_browser_access(
    tmp_path, monkeypatch, capsys, config_text, expected
) -> None:
    root = make_dotfiles(tmp_path)
    path = tmp_path / "config/transcript/youtube-session.toml"
    if config_text is not None:
        path.parent.mkdir(parents=True)
        path.write_text(config_text, encoding="utf-8")
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(
        session, "helium_profile", lambda *_a: pytest.fail("profile read")
    )
    fnox = use_vault(monkeypatch, FakeFnox(stored=None))

    code = transcript.main(["auth", "refresh", "--dotfiles-worktree", str(root)])

    output = capsys.readouterr()
    assert code == 1 and output.out == "" and fnox.calls == []
    answer = json.loads(output.err.splitlines()[-1])
    assert answer["ok"] is False
    assert expected in answer["errors"][0] and str(path) in answer["errors"][0]


def write_helium(
    root: Path, profiles: dict[str, str], database: str = "Cookies"
) -> None:
    """A synthetic Helium data directory with folder and display names."""
    root.mkdir(parents=True, exist_ok=True)
    for folder in profiles:
        path = root / folder / database
        path.parent.mkdir(parents=True)
        path.write_bytes(b"sqlite")
    info_cache = {folder: {"name": name} for folder, name in profiles.items()}
    (root / "Local State").write_text(
        json.dumps({"profile": {"info_cache": info_cache}}), encoding="utf-8"
    )


@pytest.mark.parametrize(
    "profiles",
    [
        None,
        {"Default": "Other profile"},
        {"Profile 1": "Automation fixture", "Profile 2": "Automation fixture"},
    ],
)
def test_missing_or_ambiguous_helium_profile_names_the_settings(
    tmp_path, profiles
) -> None:
    root = tmp_path / "browser"
    if profiles is not None:
        write_helium(root, profiles)
    config = session.HeliumConfig(root, "Automation fixture", "service", "account")

    with pytest.raises(session.SessionError, match="browser_data_dir and profile_name"):
        session.helium_profile(config)


def test_refused_keychain_access_names_the_desktop_fix(tmp_path, monkeypatch) -> None:
    config = session.HeliumConfig(tmp_path, "Automation fixture", "service", "account")
    monkeypatch.setattr(
        session.subprocess,
        "run",
        lambda command, **_k: subprocess.CompletedProcess(command, 51, b"", b"denied"),
    )

    with pytest.raises(session.SessionError, match="Always Allow"):
        session._helium_cookie_key(config)


@pytest.mark.parametrize("database", ["Cookies", "Network/Cookies"])
def test_refresh_with_local_settings_exports_only_youtube_and_restores_ytdlp(
    tmp_path, monkeypatch, capsys, database
) -> None:
    from http.cookiejar import Cookie

    from yt_dlp import cookies

    root = make_dotfiles(tmp_path)
    browser_root = tmp_path / "browser data"
    write_helium(
        browser_root,
        {"Default": "Other profile", "Profile 3": "Automation fixture"},
        database,
    )
    config = tmp_path / "config/transcript/youtube-session.toml"
    config.parent.mkdir(parents=True)
    config.write_text(
        f"browser_data_dir = {json.dumps(str(browser_root))}\n"
        'profile_name = "Automation fixture"\n'
        'keychain_service = "Fixture Safe Storage"\n'
        'keychain_account = "fixture-account"\n'
        'user_agent = "SyntheticBrowser/1.0"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "platform", "darwin")
    original = cookies._get_mac_keyring_password
    fnox = use_vault(monkeypatch, FakeFnox(stored=None))

    def security(command, **_kwargs):
        assert command == [
            "security",
            "find-generic-password",
            "-w",
            "-s",
            "Fixture Safe Storage",
            "-a",
            "fixture-account",
        ]
        return subprocess.CompletedProcess(command, 0, b"fixture-key\n", b"")

    monkeypatch.setattr(session.subprocess, "run", security)

    def cookie(domain: str, name: str) -> Cookie:
        return Cookie(
            0,
            name,
            VALUE,
            None,
            False,
            domain,
            True,
            True,
            "/",
            True,
            True,
            4102444800,
            False,
            None,
            None,
            {},
        )

    def extract(browser, *, profile):
        assert browser == "chrome" and profile == str(browser_root / "Profile 3")
        assert cookies._get_mac_keyring_password("Chrome", None) == b"fixture-key"
        jar = cookies.YoutubeDLCookieJar()
        for domain, name in [
            (".youtube.com", "SID"),
            ("music.youtube.com", "PREF"),
            (".google.com", "SID"),
            ("notyoutube.com", "SID"),
        ]:
            jar.set_cookie(cookie(domain, name))
        return jar

    monkeypatch.setattr(cookies, "extract_cookies_from_browser", extract)
    client = httpx.Client

    def respond(request):
        assert request.headers["User-Agent"] == "SyntheticBrowser/1.0"
        assert request.headers["Cookie"] == f"SID={VALUE}"
        return httpx.Response(200, text='ytcfg.set({"LOGGED_IN": true});')

    monkeypatch.setattr(
        session.httpx,
        "Client",
        lambda **kwargs: client(**kwargs, transport=httpx.MockTransport(respond)),
    )

    code = transcript.main(["auth", "refresh", "--dotfiles-worktree", str(root)])

    output = capsys.readouterr()
    assert code == 0, output.err
    assert output.err == ""
    assert json.loads(output.out)["changes"] == [
        ["update", f"{LABEL} in {root / session.VAULT_SOURCE}"]
    ]
    assert VALUE not in output.out
    assert fnox.stored is not None
    domains = {
        line.removeprefix("#HttpOnly_").split("\t", 1)[0]
        for line in fnox.stored.splitlines()
        if "\t" in line
    }
    assert domains == {".youtube.com", "music.youtube.com"}
    assert cookies._get_mac_keyring_password is original
