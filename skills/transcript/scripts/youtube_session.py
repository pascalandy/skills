"""Verify a YouTube session and renew it in the fnox vault, never in a plaintext file."""

from __future__ import annotations

import contextlib
import io
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
import warnings
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path

import httpx

LOGIN_URL = "https://www.youtube.com/watch?v=EIEc43CxIvY"
# The only copy of the session: an age-encrypted fnox entry with `as_file = true`,
# so `fnox exec` hands a consumer the path of a temporary 0600 file it then removes
VAULT_KEY = "YOUTUBE_COOKIES_TXT"
VAULT_LABEL = f"fnox:{VAULT_KEY}"
# The fnox store inside a worktree of pascalandy/dotfiles
VAULT_SOURCE = "dot_config/private_fnox/private_config.toml"
FNOX_TIMEOUT = 15
# Exit code of the child shell when `as_file` did not hand it a file path
NOT_A_FILE = 97
HTTP_LOGGERS = ("httpcore", "httpx")
# Keep standard user-local fnox installs reachable when a desktop app has a short PATH.
FNOX_CANDIDATES = (
    "fnox",
    str(Path.home() / ".local/bin/fnox"),
    str(Path.home() / ".local/share/fnox/fnox"),
)
SUPPORTED_YTDLP_VERSION = "2026.07.04"
SESSION_CONFIG = Path("transcript/youtube-session.toml")
# The command run from the skills checkout; `transcript` is not on PATH
REFRESH_COMMAND = "just transcript-auth-refresh"
REFRESH_HINT = (
    "Follow references/youtube-auth-refresh.md to configure the source Mac, then run "
    f"'{REFRESH_COMMAND} --dotfiles-worktree <dotfiles worktree>' from the skills "
    "checkout in the unlocked desktop session. Land the dotfiles PR with 'just merge'. "
    "If YouTube signed the profile out, sign in again and close its window"
)


class SessionError(RuntimeError):
    """A safe session diagnostic, containing no cookie values or raw responses."""


class SessionNetworkError(SessionError):
    """A free session check failed temporarily, before any paid work."""


@dataclass(frozen=True)
class HeliumConfig:
    data_dir: Path
    profile_name: str
    keychain_service: str
    keychain_account: str


def _config_path() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", ""))
    if not config_home.is_absolute():
        config_home = Path.home() / ".config"
    return config_home / SESSION_CONFIG


def _read_config(path: Path, *, required: bool) -> dict[str, object]:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except FileNotFoundError:
        if not required:
            return {}
        raise SessionError(
            f"YouTube session configuration is missing. Create {path} "
            "as described in references/youtube-auth-refresh.md"
        ) from None
    except (OSError, ValueError):
        raise SessionError(
            f"YouTube session configuration could not be read as TOML. Fix {path}; "
            "see references/youtube-auth-refresh.md"
        ) from None


def _config_string(settings: dict[str, object], key: str, path: Path) -> str:
    value = settings.get(key)
    if not isinstance(value, str) or not value.strip() or "\0" in value:
        raise SessionError(f"Set {key} to a non-empty TOML string in {path}")
    return value


def _helium_config() -> HeliumConfig:
    path = _config_path()
    settings = _read_config(path, required=True)
    data_dir = _config_string(settings, "browser_data_dir", path)
    try:
        root = Path(data_dir).expanduser()
    except RuntimeError:
        raise SessionError(
            f"Set browser_data_dir to an absolute path in {path}"
        ) from None
    if not root.is_absolute():
        raise SessionError(f"Set browser_data_dir to an absolute path in {path}")
    return HeliumConfig(
        root,
        _config_string(settings, "profile_name", path),
        _config_string(settings, "keychain_service", path),
        _config_string(settings, "keychain_account", path),
    )


def _probe_user_agent() -> str:
    path = _config_path()
    settings = _read_config(path, required=False)
    if "user_agent" in settings:
        value = _config_string(settings, "user_agent", path).strip()
        if not value.isascii() or not value.isprintable():
            raise SessionError(f"Set user_agent to a printable ASCII string in {path}")
        return value

    from yt_dlp.utils.networking import std_headers

    return std_headers["User-Agent"]


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


@contextlib.contextmanager
def _quiet_http_transport() -> Iterator[None]:
    """Silence httpx and httpcore for the session check.

    Their debug records print request and response headers, Set-Cookie included,
    and --debug would copy them to stderr. The check's own diagnostics stay."""
    prefixes = tuple(HTTP_LOGGERS) + tuple(f"{each}." for each in HTTP_LOGGERS)

    def keep(record: logging.LogRecord) -> bool:
        return not (record.name in HTTP_LOGGERS or record.name.startswith(prefixes))

    # A filter on the root handlers also drops records from child loggers
    # created during the check or set to DEBUG explicitly.
    handlers = list(logging.getLogger().handlers)
    for each in handlers:
        each.addFilter(keep)
    try:
        yield
    finally:
        for each in handlers:
            each.removeFilter(keep)


def check_session(path: Path, *, timeout: float = 25) -> None:
    """Require a positive YouTube login response without saving changed cookies."""
    jar = load_cookie_jar(path)
    user_agent = _probe_user_agent()
    try:
        with (
            _quiet_http_transport(),
            httpx.Client(
                cookies=jar,
                headers={"User-Agent": user_agent},
                follow_redirects=True,
                timeout=timeout,
            ) as client,
        ):
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
        raise SessionError(
            f"YouTube refused the stored session: it expired or was signed out. {REFRESH_HINT}"
        )
    if flag is not True or response.url.host not in {"www.youtube.com", "youtube.com"}:
        raise SessionError(
            "YouTube did not confirm a signed-in session. "
            f"Run 'transcript auth check' or renew it. {REFRESH_HINT}"
        )


def helium_profile(config: HeliumConfig) -> Path:
    """Find the configured profile by its display name in Chromium's Local State."""
    setup = (
        "Check browser_data_dir and profile_name in references/youtube-auth-refresh.md. "
        "Sign in to YouTube in that Helium profile and close its window before retrying"
    )
    try:
        state = json.loads(
            (config.data_dir / "Local State").read_text(encoding="utf-8")
        )
        profiles = state["profile"]["info_cache"]
        if not isinstance(profiles, dict):
            raise TypeError
    except (OSError, ValueError, KeyError, TypeError):
        raise SessionError(
            f"Helium profile metadata could not be read. {setup}"
        ) from None
    folders = [
        config.data_dir / folder
        for folder, info in profiles.items()
        if isinstance(info, dict) and info.get("name") == config.profile_name
    ]
    if len(folders) != 1 or not any(
        (folders[0] / relative).is_file() for relative in ("Cookies", "Network/Cookies")
    ):
        raise SessionError(
            f"Helium has no single configured profile with a cookies database. {setup}"
        )
    return folders[0]


def _helium_cookie_key(config: HeliumConfig) -> bytes:
    """Read Helium's cookie key; macOS asks once, then 'Always Allow' remembers."""
    try:
        result = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-w",
                "-s",
                config.keychain_service,
                "-a",
                config.keychain_account,
            ],
            capture_output=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is None or result.returncode or not result.stdout.strip():
        raise SessionError(
            f"Keychain did not release Helium's cookie key. Run '{REFRESH_COMMAND}' "
            "in the source Mac's unlocked desktop terminal and choose 'Always Allow'"
        )
    return result.stdout.rstrip(b"\n")


def _export_helium(path: Path) -> None:
    """Export only YouTube domains; retain all browser diagnostics in memory."""
    if sys.platform != "darwin":
        raise SessionError(f"Helium session renewal requires macOS. {REFRESH_HINT}")
    config = _helium_config()
    profile = helium_profile(config)
    key = _helium_cookie_key(config)
    from yt_dlp import cookies, version

    original = getattr(cookies, "_get_mac_keyring_password", None)
    if version.__version__ != SUPPORTED_YTDLP_VERSION or not callable(original):
        raise SessionError(
            f"The Helium export supports yt-dlp {SUPPORTED_YTDLP_VERSION} only; "
            f"found {version.__version__}"
        )
    try:
        # yt-dlp reads Chromium cookies but looks up '<name> Safe Storage'; Helium
        # stores its key under another name, so hand yt-dlp the key directly
        cookies._get_mac_keyring_password = lambda *_args: key
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
            warnings.catch_warnings(),
        ):
            warnings.simplefilter("ignore")
            jar = cookies.extract_cookies_from_browser("chrome", profile=str(profile))
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
            f"Helium YouTube cookies could not be exported. {REFRESH_HINT}"
        ) from None
    finally:
        cookies._get_mac_keyring_password = original


def _run_process(
    command: Sequence[str], *, input: str | None = None, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        input=input,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


# transcript.py swaps in its own child runner, which stops a child gently on a
# signal or deadline; this default keeps the module usable on its own
run_process = _run_process


def _fnox_run(
    arguments: Sequence[str], *, stdin: str | None = None, timeout: float = FNOX_TIMEOUT
) -> subprocess.CompletedProcess[str] | None:
    """Run fnox from the first candidate that exists; None when none is installed.

    Only a missing executable moves on to the next candidate. Output stays captured
    and callers never print it, because it can hold cookie values."""
    for fnox in FNOX_CANDIDATES:
        try:
            return run_process([fnox, *arguments], input=stdin, timeout=timeout)
        except FileNotFoundError:
            continue
        except (OSError, subprocess.SubprocessError):
            raise SessionError(
                f"fnox could not run to reach {VAULT_LABEL}. Check 'fnox list'"
            ) from None
    return None


def _outer_vault_file() -> Path | None:
    """The temporary file an enclosing `fnox exec --only YOUTUBE_COOKIES_TXT` made."""
    value = os.environ.get(VAULT_KEY, "")
    try:
        return Path(value) if value and Path(value).is_file() else None
    except (OSError, ValueError):
        return None


def vault_available() -> bool:
    """True when the vault holds the session. Reads no secret: `fnox list` names keys.

    False only when fnox is not installed or a successful listing omits the key,
    the two cases where a run may go anonymous. A failed or timed-out listing
    raises, because it says nothing about whether the entry exists."""
    if _outer_vault_file() is not None:
        return True
    result = _fnox_run(["list"])
    if result is None:
        return False
    if result.returncode:
        raise SessionError(
            f"'fnox list' failed, so {VAULT_LABEL} could not be checked. "
            "Fix fnox, then retry"
        )
    return re.search(rf"(?m)^\s*{re.escape(VAULT_KEY)}\s", result.stdout) is not None


def _file_script(command: str) -> str:
    """A child shell script that runs `command` only when $YOUTUBE_COOKIES_TXT is a
    file. Without `as_file`, the variable holds the raw value, and the builtin
    `test` keeps it out of any external command's arguments."""
    return f'test -f "${VAULT_KEY}" || exit {NOT_A_FILE}; {command}'


def _require_as_file(result: subprocess.CompletedProcess[str]) -> None:
    if result.returncode == NOT_A_FILE:
        raise SessionError(
            f"{VAULT_LABEL} is not exposed as a file: its entry lacks as_file = true. "
            "Restore it in the dotfiles fnox store, then retry"
        )


def copy_vault_cookies(destination: Path) -> None:
    """Copy the vault session into `destination`, a file the caller made private.

    An enclosing `fnox exec` already provides the temporary file; otherwise one
    `fnox exec` provides it for the length of the copy and removes it."""
    outer = _outer_vault_file()
    if outer is not None:
        try:
            destination.write_bytes(outer.read_bytes())
        except OSError:
            raise SessionError(f"{VAULT_LABEL} could not be read") from None
        return
    result = _fnox_run(
        [
            "exec",
            "--only",
            VAULT_KEY,
            "--if-missing",
            "error",
            "--",
            "/bin/sh",
            "-c",
            _file_script(f'cp -- "${VAULT_KEY}" "$1"'),
            "sh",
            str(destination),
        ]
    )
    if result is None:
        raise SessionError(
            f"fnox was not found, so {VAULT_LABEL} cannot be read. "
            "Install fnox as docs/operations/secrets.md in pascalandy/dotfiles describes"
        )
    _require_as_file(result)
    if result.returncode:
        raise SessionError(
            f"{VAULT_LABEL} could not be read from fnox. Check that 'fnox list' "
            f"shows it with as_file = true. {REFRESH_HINT}"
        )


def _entry_has_as_file(source: Path) -> bool:
    try:
        entry = tomllib.loads(source.read_text(encoding="utf-8"))["secrets"][VAULT_KEY]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return isinstance(entry, dict) and entry.get("as_file") is True


def _ensure_as_file(source: Path) -> None:
    """`fnox set` can drop `as_file = true`; restore it on the entry's own line."""
    if _entry_has_as_file(source):
        return
    text = source.read_text(encoding="utf-8")
    pattern = re.compile(rf"(?m)^({re.escape(VAULT_KEY)}\s*=\s*\{{.*?)\s*\}}[ \t]*$")
    patched, count = pattern.subn(r"\1, as_file = true }", text, count=1)
    if count != 1:
        raise SessionError(f"{VAULT_KEY} has no inline entry in {source}")
    source.write_text(patched, encoding="utf-8")
    if not _entry_has_as_file(source):
        raise SessionError(f"Could not keep as_file = true on {VAULT_KEY}")


def vault_source(worktree: Path) -> Path:
    """The fnox store of a dotfiles worktree, which must contain it.

    The folder must be the root of a linked git worktree: the ordinary clone, which
    chezmoi applies from, is never written."""
    root = worktree.expanduser().resolve()
    source = root / VAULT_SOURCE
    hint = "Create one as docs/operations/secrets.md in pascalandy/dotfiles describes"
    if not source.is_file():
        raise SessionError(
            f"{root} is not a dotfiles worktree: {VAULT_SOURCE} is missing. {hint}"
        )
    try:
        git = run_process(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "--path-format=absolute",
                "--show-toplevel",
                "--git-dir",
                "--git-common-dir",
            ],
            timeout=FNOX_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        raise SessionError("git could not run to check the dotfiles worktree") from None
    paths = git.stdout.split("\n") if git.returncode == 0 else []
    if (
        len(paths) < 3
        or Path(paths[0]).resolve() != root
        or Path(paths[1]).resolve() == Path(paths[2]).resolve()
    ):
        raise SessionError(
            f"{root} is not the root of a linked git worktree of the dotfiles repo. {hint}"
        )
    return source


def write_vault(candidate: Path, source: Path) -> None:
    """Encrypt the verified candidate into the entry of `source`, then read it back."""
    store = ["-c", str(source)]
    result = _fnox_run(
        [
            "--no-daemon",
            "--non-interactive",
            *store,
            "set",
            VAULT_KEY,
            "--provider",
            "age",
            "--from-file",
            "/dev/stdin",
        ],
        stdin=candidate.read_text(encoding="utf-8"),
    )
    if result is None or result.returncode:
        raise SessionError(f"fnox could not write {VAULT_LABEL} into {source}")
    _ensure_as_file(source)
    check = _fnox_run(
        [
            "--no-daemon",
            "--non-interactive",
            *store,
            "exec",
            "--only",
            VAULT_KEY,
            "--if-missing",
            "error",
            "--",
            "/bin/sh",
            "-c",
            _file_script(f'cmp -s -- "${VAULT_KEY}" "$1"'),
            "sh",
            str(candidate),
        ]
    )
    if check is not None:
        _require_as_file(check)
    if check is None or check.returncode:
        raise SessionError(
            f"{VAULT_LABEL} in {source} does not read back as the verified export"
        )


def refresh_session(
    worktree: Path, *, timeout: float = 60
) -> tuple[list[list[str]], list[str]]:
    """Export, verify, then write the session into a dotfiles worktree's vault.

    The export lives in a private temporary directory for the length of the call.
    A failed export or verification leaves the worktree untouched. Returns the
    changes and the steps that still land them, since the vault changes only
    once the dotfiles PR merges."""
    source = vault_source(worktree)
    with tempfile.TemporaryDirectory(prefix="transcript-renew-") as directory:
        candidate = Path(directory) / "cookies.txt"
        candidate.touch(mode=0o600)
        _export_helium(candidate)
        check_session(candidate, timeout=min(timeout, 25))
        write_vault(candidate, source)
    root = source.parents[2]
    in_root = f"cd {shlex.quote(str(root))} &&"
    steps = [
        f"{in_root} git diff --stat   # only {VAULT_SOURCE} changes, one encrypted value",
        f"{in_root} git add {VAULT_SOURCE}",
        f"{in_root} git commit -m 'chore(secrets): refresh the YouTube cookies ciphertext'",
        f"{in_root} git push -u origin HEAD && gh pr create --fill",
        f"{in_root} just merge   # a values-only diff merges without review",
        "uv run <skills checkout>/authoring/andy/transcript/scripts/transcript.py auth check",
    ]
    return [["update", f"{VAULT_LABEL} in {source}"]], steps
