"""retro_triage.py as agents run it: a subprocess against a fake TypeSafe server."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / "retro_triage.py"
# Scores the fake server returns, keyed by the story text it receives
SCORES = {
    "clear": {"skill_causes": 0.91, "recurs": 0.85, "fix_is_minimal": 0.93},
    "close": {"skill_causes": 0.49, "recurs": 0.80, "fix_is_minimal": 0.89},
}


def story(name: str, repo: str = "o/public", **extra: str) -> str:
    fields = {"id": name, "repo": repo, "story": name, "evidence": "e", "fix": "f"}
    return json.dumps({**fields, **extra})


@pytest.fixture
def jev() -> Iterator[tuple[str, list[dict]]]:
    """A fake /v1/systemone that answers from SCORES and records each state."""
    seen: list[dict] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen.append(body["state"])
            scores = SCORES[body["state"]["story"]]
            answers = {name: {"type": "noul", "noul": p} for name, p in scores.items()}
            reply = json.dumps({"model": "jev-1.13.0", "answers": answers}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(reply)))
            self.end_headers()
            self.wfile.write(reply)

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}", seen
    server.shutdown()


def run(
    tmp_path: Path, lines: list[str], *args: str, visibility: str = "PUBLIC", **env: str
) -> subprocess.CompletedProcess[str]:
    """Run the script with a stub gh, an empty config home, and a keyring with no key."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name, body in (("gh", f"echo {visibility}"), ("chezmoi", "exit 1")):
        (bin_dir / name).write_text(f"#!/bin/sh\n{body}\n")
        (bin_dir / name).chmod(0o755)
    stories = tmp_path / "stories.jsonl"
    stories.write_text("\n".join(lines) + "\n")
    base = {k: v for k, v in os.environ.items() if not k.startswith("TYPESAFE_")}
    path = f"{bin_dir}{os.pathsep}/usr/bin{os.pathsep}/bin"
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(stories), *args],
        env={**base, "PATH": path, "XDG_CONFIG_HOME": str(tmp_path), **env},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def test_run_decides_each_story_and_flags_close_calls(tmp_path: Path, jev) -> None:
    url, seen = jev
    lines = [story("clear", reviewer="accept"), story("close", reviewer="accept")]
    done = run(tmp_path, lines, TYPESAFE_API_KEY="k", TYPESAFE_BASE_URL=url)

    assert (done.returncode, done.stderr) == (0, "")
    assert done.stdout.splitlines() == [
        "ID\tDECISION\tCONTESTED\tSKILL_CAUSES\tRECURS\tFIX_IS_MINIMAL\tREVIEWER",
        "clear\taccept\tno\t0.91\t0.85\t0.93\taccept",
        "close\trefuse\tyes\t0.49\t0.80\t0.89\taccept",
    ]
    # Jev never sees the reviewer's verdict
    assert {tuple(sorted(state)) for state in seen} == {
        ("evidence", "goal", "proposed_fix", "story")
    }


def test_json_prints_one_object(tmp_path: Path, jev) -> None:
    url, _ = jev
    done = run(
        tmp_path,
        [story("clear")],
        "--json",
        TYPESAFE_API_KEY="k",
        TYPESAFE_BASE_URL=url,
    )

    assert json.loads(done.stdout)["stories"][0]["decision"] == "accept"


def test_dry_run_shows_each_state_without_key_consent_or_network(
    tmp_path: Path,
) -> None:
    done = run(
        tmp_path, [story("clear", repo="o/private")], "--dry-run", visibility="PRIVATE"
    )

    assert done.returncode == 0
    assert json.loads(done.stdout)["state"]["story"] == "clear"


def test_a_private_repository_needs_recorded_consent(tmp_path: Path, jev) -> None:
    url, seen = jev
    done = run(
        tmp_path,
        [story("clear", repo="o/private")],
        visibility="PRIVATE",
        TYPESAFE_API_KEY="k",
        TYPESAFE_BASE_URL=url,
    )

    assert (done.returncode, done.stdout, seen) == (1, "", [])
    assert 'jevlabel consent add o/private --by "<their name>"' in done.stderr


def test_recorded_consent_lets_a_private_story_through(tmp_path: Path, jev) -> None:
    url, _ = jev
    consent = tmp_path / "label-for-issues-jev/consent.toml"
    consent.parent.mkdir()
    consent.write_text('["o/private"]\nterms = "typesafe-2026-09-26"\n')
    done = run(
        tmp_path,
        [story("clear", repo="o/private")],
        visibility="PRIVATE",
        TYPESAFE_API_KEY="k",
        TYPESAFE_BASE_URL=url,
    )

    assert done.returncode == 0


def test_an_unreachable_api_exits_75(tmp_path: Path) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    done = run(
        tmp_path,
        [story("clear")],
        TYPESAFE_API_KEY="k",
        TYPESAFE_BASE_URL=f"http://127.0.0.1:{port}",
    )

    assert (done.returncode, done.stdout) == (75, "")


@pytest.mark.parametrize(
    ("lines", "message"),
    [
        (["not json"], "stories.jsonl:1 is not JSON"),
        (["[]"], "stories.jsonl:1 is not a JSON object"),
        ([json.dumps({"id": "a"})], "stories.jsonl:1 lacks repo, story, evidence, fix"),
        ([story("clear"), story("clear")], "stories.jsonl:2 repeats id 'clear'"),
    ],
)
def test_bad_input_exits_1_naming_the_line(
    tmp_path: Path, lines: list[str], message: str
) -> None:
    done = run(tmp_path, lines, "--dry-run")

    assert (done.returncode, done.stdout) == (1, "")
    assert message in done.stderr


def test_no_key_exits_1_with_the_fix(tmp_path: Path) -> None:
    done = run(tmp_path, [story("clear")])

    assert done.returncode == 1
    assert "export TYPESAFE_API_KEY" in done.stderr


def test_help_wins_and_lists_examples_and_exit_codes(tmp_path: Path) -> None:
    done = run(tmp_path, [story("clear")], "--bogus", "--help")

    assert (done.returncode, done.stderr) == (0, "")
    assert "examples:" in done.stdout and "75   TypeSafe" in done.stdout
