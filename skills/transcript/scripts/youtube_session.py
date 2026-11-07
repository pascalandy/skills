"""Store, verify and renew a YouTube session without publishing its secrets."""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import warnings
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path

import httpx

LOGIN_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
REFRESH_HINT = (
    "Sign in to YouTube in Arc on the source Mac, then run "
    "'transcript auth refresh' in its unlocked desktop terminal"
)


class SessionError(RuntimeError):
    """A safe session diagnostic, containing no cookie values or raw responses."""


class SessionNetworkError(SessionError):
    """A free session check failed temporarily, before any paid work."""


def session_directory() -> Path:
    return Path.home() / ".local/share/transcript"


def session_file() -> Path:
    return session_directory() / "youtube.cookies.txt"


def targets_file() -> Path:
    return session_directory() / "youtube-targets.txt"


def load_cookie_jar(path: Path) -> MozillaCookieJar:
    """Load a jar, suppressing parser warnings and secret-bearing exceptions."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            jar = MozillaCookieJar(str(path))
            jar.load(ignore_discard=True, ignore_expires=True)
            if not any(jar):
                raise LoadError
            for cookie in jar:
                if cookie.expires == 0:
                    cookie.expires = None  # Netscape/yt-dlp use 0 for session cookies.
        return jar
    except (OSError, ValueError):
        raise SessionError(
            "Cookies file is unreadable, empty, or not Netscape format. "
            "Replace it with a fresh YouTube cookies export."
        ) from None


def logged_in_flag(body: str) -> bool | None:
    """Read the server's configuration, never infer login from a public video."""
    flags = []
    decoder = json.JSONDecoder()
    for match in re.finditer(r"ytcfg\.set\(\s*", body):
        try:
            value, _ = decoder.raw_decode(body[match.end() :])
        except ValueError:
            continue
        if isinstance(value, dict) and isinstance(value.get("LOGGED_IN"), bool):
            flags.append(value["LOGGED_IN"])
    return flags[0] if flags and len(set(flags)) == 1 else None


def check_session(path: Path, *, timeout: float = 25) -> None:
    """Require a positive YouTube login response without saving changed cookies."""
    jar = load_cookie_jar(path)
    try:
        with httpx.Client(
            cookies=jar,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/146.0.0.0 Safari/537.36"
                )
            },
            follow_redirects=True,
            timeout=timeout,
        ) as client:
            response = client.get(LOGIN_URL)
    except httpx.HTTPError:
        raise SessionNetworkError(
            "YouTube session could not be checked because of a network failure. "
            "Retry 'transcript auth check'"
        ) from None
    if response.status_code == 429 or response.status_code >= 500:
        raise SessionNetworkError(
            f"YouTube session check returned HTTP {response.status_code}. "
            "Retry 'transcript auth check' later"
        )
    flag = logged_in_flag(response.text) if response.status_code == 200 else None
    if flag is False:
        raise SessionError(f"YouTube session is expired or signed out. {REFRESH_HINT}")
    if flag is not True or response.url.host not in {"www.youtube.com", "youtube.com"}:
        raise SessionError(
            "YouTube did not confirm a signed-in session. "
            f"Run 'transcript auth check' or renew it. {REFRESH_HINT}"
        )


def refresh_targets(explicit: list[str] | None) -> list[str]:
    """Read non-secret SSH destinations; explicit targets override the file."""
    if explicit is None:
        path = targets_file()
        try:
            explicit = (
                path.read_text(encoding="utf-8").splitlines() if path.exists() else []
            )
        except (OSError, UnicodeError):
            raise SessionError(
                f"Cannot read SSH targets. Fix {path}, then run 'transcript auth refresh'"
            ) from None
    targets = list(dict.fromkeys(line.strip() for line in explicit if line.strip()))
    if any(
        re.fullmatch(r"(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9][A-Za-z0-9.-]*", host) is None
        for host in targets
    ):
        raise SessionError(
            "SSH targets must be host aliases or user@host, one per line. "
            f"Fix {targets_file()} or the --to arguments"
        )
    return targets


def _export_arc(path: Path) -> None:
    """Export only YouTube domains; retain all browser diagnostics in memory."""
    if sys.platform != "darwin":
        raise SessionError(f"Arc session renewal requires macOS. {REFRESH_HINT}")
    from yt_dlp import cookies, version
    from ytdlp_arc import install_arc_cookie_adapter

    original = cookies._get_chromium_based_browser_settings
    try:
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore")
            install_arc_cookie_adapter(cookies, runtime_version=version.__version__)
            jar = cookies.extract_cookies_from_browser(
                "chrome",
                profile=str(
                    Path.home() / "Library/Application Support/Arc/User Data/Default"
                ),
            )
            exported = cookies.YoutubeDLCookieJar(str(path))
            for cookie in jar:
                domain = cookie.domain.lstrip(".")
                if (
                    domain == "youtube.com" or domain.endswith(".youtube.com")
                ) and not cookie.is_expired():
                    exported.set_cookie(cookie)
            exported.save(ignore_discard=True, ignore_expires=True)
    except Exception:  # noqa: BLE001 - browser exceptions can contain secret cookie records
        raise SessionError(
            f"Arc YouTube cookies could not be exported. {REFRESH_HINT}"
        ) from None
    finally:
        cookies._get_chromium_based_browser_settings = original


def _install_local(candidate: Path, destination: Path) -> None:
    """Publish an already verified candidate with one atomic replacement."""
    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination.parent.chmod(0o700)
    descriptor, name = tempfile.mkstemp(prefix=".youtube-", dir=destination.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(candidate.read_bytes())
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


# The remote owns only its private store. Secrets travel on stdin, never argv.
# uv is already required by Transcript; no remote skill installation is needed.
REMOTE_INSTALL = """import os, sys, tempfile, warnings
from pathlib import Path
from http.cookiejar import MozillaCookieJar
directory = Path.home() / ".local/share/transcript"
directory.mkdir(mode=0o700, parents=True, exist_ok=True)
directory.chmod(0o700)
fd, name = tempfile.mkstemp(prefix=".youtube-", dir=directory)
temporary = Path(name)
try:
    data = sys.stdin.buffer.read(1048577)
    if not data or len(data) > 1048576:
        raise ValueError()
    with os.fdopen(fd, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        jar = MozillaCookieJar(str(temporary))
        jar.load(ignore_discard=True, ignore_expires=True)
    if not any(jar):
        raise ValueError()
    check_session(temporary)
    os.replace(temporary, directory / "youtube.cookies.txt")
except Exception:
    sys.stderr.write("Session installation failed\\n")
    sys.exit(1)
finally:
    temporary.unlink(missing_ok=True)
"""


def remote_install_code() -> str:
    """Send this verifier with its receiver, without installing remote skills."""
    return Path(__file__).read_text(encoding="utf-8") + "\n" + REMOTE_INSTALL


def _install_remote(candidate: Path, host: str, *, timeout: float) -> None:
    remote = (
        'PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin" '
        "uv run --quiet --no-project --with httpx python -c "
        + shlex.quote(remote_install_code())
    )
    try:
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "StrictHostKeyChecking=yes",
                "-o",
                "ConnectTimeout=8",
                "-o",
                "ForwardAgent=no",
                "--",
                host,
                remote,
            ],
            input=candidate.read_bytes(),
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        raise SessionError(
            f"Could not update {host}. Retry 'transcript auth refresh'"
        ) from None
    if result.returncode:
        raise SessionError(f"Could not update {host}. Retry 'transcript auth refresh'")


def refresh_session(
    targets: list[str], *, timeout: float = 60
) -> tuple[list[list[str]], list[str]]:
    """Verify before replacing the old session; report partial fleet updates."""
    changes: list[list[str]] = []
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="transcript-renew-") as directory:
        candidate = Path(directory) / "cookies.txt"
        candidate.touch(mode=0o600)
        _export_arc(candidate)
        check_session(candidate, timeout=min(timeout, 25))
        _install_local(candidate, session_file())
        changes.append(["update", str(session_file())])
        for host in targets:
            try:
                _install_remote(candidate, host, timeout=timeout)
            except SessionError as error:
                errors.append(str(error))
            else:
                changes.append(
                    ["update", f"{host}:.local/share/transcript/youtube.cookies.txt"]
                )
    return changes, errors
