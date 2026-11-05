"""Run opensrc_sync.py against a fake opensrc and a fake ssh in a temporary home."""

import json
import os
import socket
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "opensrc_sync.py"

# A fake opensrc that keeps a registry like the real one: fetch adds a version
# folder holding a fresh source file, remove deletes the entry and its folder.
# Every call is logged with the cache it used. A name in FAIL_FETCH fails.
FAKE_OPENSRC = """\
#!{python}
import json, os, shutil, sys
from pathlib import Path

cache = Path(os.environ.get("OPENSRC_HOME") or Path.home() / ".opensrc")
with open(os.environ["CALLS"], "a") as log:
    log.write(json.dumps({{"argv": sys.argv[1:], "cache": str(cache)}}) + "\\n")
registry = cache / "sources.json"
data = json.loads(registry.read_text()) if registry.exists() else {{"repos": []}}
command, *args = sys.argv[1:]
specs = [arg for arg in args if not arg.startswith("-")]
for spec in specs:
    name, _, version = spec.partition("@")
    if not name.startswith("github.com/"):
        name = "github.com/" + name
    if command == "fetch":
        if name in os.environ.get("FAIL_FETCH", "").split(","):
            print(f"Repository {{name}} not found", file=sys.stderr)
            sys.exit(1)
        version = version or "main"
        path = f"repos/{{name}}/{{version}}"
        (cache / path).mkdir(parents=True, exist_ok=True)
        (cache / path / "README.md").write_text("fresh")
        data["repos"] = [r for r in data["repos"] if r["name"] != name]
        data["repos"].append({{"name": name, "version": version, "path": path, "fetchedAt": "2999-01-01T00:00:00+00:00"}})
    elif command == "remove":
        for repo in data["repos"]:
            if repo["name"] == name:
                shutil.rmtree(cache / repo["path"])
        data["repos"] = [r for r in data["repos"] if r["name"] != name]
cache.mkdir(parents=True, exist_ok=True)
registry.write_text(json.dumps(data))
"""

# A fake ssh that logs its host, then runs the remote command in a local shell,
# or fails like an unreachable host when SSH_DOWN is set.
FAKE_SSH = """\
#!/bin/sh
for last; do :; done
host=""
while [ $# -gt 1 ]; do
	case "$1" in
	-o) shift 2 ;;
	*) host="$1"; shift ;;
	esac
done
echo "$host" >>"$SSH_LOG"
[ -z "${SSH_DOWN:-}" ] || { echo "ssh: connect to host $host: timed out" >&2; exit 255; }
exec sh -c "$last"
"""


class OpensrcSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.home = self.root / "home"
        self.home.mkdir()
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        fake = bin_dir / "opensrc"
        fake.write_text(FAKE_OPENSRC.format(python=sys.executable))
        ssh = bin_dir / "ssh"
        ssh.write_text(FAKE_SSH)
        for tool in (fake, ssh):
            tool.chmod(0o755)
        self.calls = self.root / "calls.jsonl"
        self.ssh_log = self.root / "ssh.log"
        self.env = {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
            "HOME": str(self.home),
            "CALLS": str(self.calls),
            "SSH_LOG": str(self.ssh_log),
        }

    def run_sync(self, *args: str, code: int = 0, **env: str) -> dict:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env={**self.env, **env},
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, code, result.stderr)
        if code:
            self.assertEqual(result.stdout, "")
            return json.loads(result.stderr.strip().splitlines()[-1])
        return json.loads(result.stdout)

    def seed(self, cache: Path, name: str, version: str, fetched: str) -> Path:
        path = f"repos/{name}/{version}"
        (cache / path).mkdir(parents=True)
        (cache / path / "STALE").write_text("old")
        registry = cache / "sources.json"
        data = json.loads(registry.read_text()) if registry.exists() else {"repos": []}
        data["repos"].append(
            {"name": name, "version": version, "path": path, "fetchedAt": fetched}
        )
        registry.write_text(json.dumps(data))
        return cache / path

    def fleet(self, machine: str, key: str = ".cache-src", extra: str = "") -> Path:
        path = self.root / "fleet.toml"
        path.write_text(
            textwrap.dedent(f"""\
                [machines.{machine}]
                ssh = "me@{machine}.example.net"
                opensrc = "{key}"
                {extra}
                [machines.other]
                ssh = "me@other.example.net"
                """)
        )
        return path

    def calls_made(self) -> list[dict]:
        if not self.calls.exists():
            return []
        return [json.loads(line) for line in self.calls.read_text().splitlines()]

    def test_fetches_a_missing_repository_and_reports_its_path(self) -> None:
        answer = self.run_sync("acme/widgets.git")
        cache = self.home / ".opensrc"
        path = cache / "repos/github.com/acme/widgets/main"
        self.assertEqual(
            answer,
            {
                "ok": True,
                "changes": [["fetch", "github.com/acme/widgets"]],
                "repos": [{"name": "github.com/acme/widgets", "path": str(path)}],
            },
        )
        self.assertEqual((path / "README.md").read_text(), "fresh")

    def test_refresh_replaces_the_cached_copy_and_keeps_its_version(self) -> None:
        old = self.seed(
            self.home / ".opensrc",
            "github.com/acme/widgets",
            "v2.1.0",
            "2020-01-01T00:00:00+00:00",
        )
        answer = self.run_sync("acme/widgets")
        self.assertEqual(answer["changes"], [["refresh", "github.com/acme/widgets"]])
        self.assertEqual(answer["repos"][0]["path"], str(old))
        self.assertFalse((old / "STALE").exists())
        self.assertEqual(
            [call["argv"] for call in self.calls_made()],
            [
                ["remove", "github.com/acme/widgets"],
                ["fetch", "--quiet", "github.com/acme/widgets@v2.1.0"],
            ],
        )

    def test_max_age_keeps_a_recent_copy(self) -> None:
        self.seed(
            self.home / ".opensrc",
            "github.com/acme/widgets",
            "main",
            "2999-01-01T00:00:00+00:00",
        )
        answer = self.run_sync("--max-age", "24h", "acme/widgets")
        self.assertNotIn("changes", answer)
        self.assertEqual(self.calls_made(), [])

    def test_without_a_repository_refreshes_every_cached_one(self) -> None:
        cache = self.home / ".opensrc"
        for name in ("github.com/acme/a", "github.com/acme/b"):
            self.seed(cache, name, "main", "2020-01-01T00:00:00+00:00")
        answer = self.run_sync()
        self.assertEqual(
            answer,
            {
                "ok": True,
                "changes": [
                    ["refresh", "github.com/acme/a"],
                    ["refresh", "github.com/acme/b"],
                ],
            },
        )

    def test_dry_run_lists_the_plan_and_runs_nothing(self) -> None:
        answer = self.run_sync("--dry-run", "acme/widgets")
        self.assertEqual(
            answer, {"ok": True, "changes": [["fetch", "github.com/acme/widgets"]]}
        )
        self.assertEqual(self.calls_made(), [])

    def test_fleet_runs_opensrc_on_the_cache_machine_through_ssh(self) -> None:
        answer = self.run_sync("--fleet", str(self.fleet("vault-host")), "acme/widgets")
        cache = self.home / ".cache-src"
        self.assertEqual(answer["machine"], "vault-host")
        self.assertEqual(
            answer["repos"][0]["path"],
            str(cache / "repos/github.com/acme/widgets/main"),
        )
        self.assertEqual(
            set(self.ssh_log.read_text().split()), {"me@vault-host.example.net"}
        )
        self.assertEqual({call["cache"] for call in self.calls_made()}, {str(cache)})

    def test_fleet_on_the_cache_machine_runs_locally(self) -> None:
        here = socket.gethostname().split(".")[0].lower()
        answer = self.run_sync("--fleet", str(self.fleet(here)), "acme/widgets")
        self.assertEqual(answer["machine"], here)
        self.assertFalse(self.ssh_log.exists())

    def test_fleet_with_two_caches_fails(self) -> None:
        fleet = self.root / "fleet.toml"
        fleet.write_text(
            '[machines.a]\nssh = "me@a"\nopensrc = ".x"\n[machines.b]\nssh = "me@b"\nopensrc = ".y"\n'
        )
        answer = self.run_sync("--fleet", str(fleet), "acme/widgets", code=1)
        self.assertIn("opensrc key to 2 machines", answer["errors"][0])

    def test_unreachable_cache_machine_is_temporary(self) -> None:
        answer = self.run_sync(
            "--fleet",
            str(self.fleet("vault-host")),
            "acme/widgets",
            code=75,
            SSH_DOWN="1",
        )
        self.assertIn("retry", answer)

    def test_a_failed_fetch_fails_the_run_and_keeps_the_others(self) -> None:
        answer = self.run_sync(
            "acme/missing", "acme/widgets", code=1, FAIL_FETCH="github.com/acme/missing"
        )
        self.assertIn(
            "opensrc fetch github.com/acme/missing failed", answer["errors"][0]
        )
        self.assertEqual(answer["changes"], [["fetch", "github.com/acme/widgets"]])

    def test_a_bad_reference_is_a_usage_error(self) -> None:
        answer = self.run_sync("not a repo", code=2)
        self.assertEqual(answer["help"], "opensrc_sync.py --help")


if __name__ == "__main__":
    unittest.main()
