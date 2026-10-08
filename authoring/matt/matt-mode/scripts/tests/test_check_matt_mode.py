from __future__ import annotations

import json
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "check_matt_mode.py"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    # uv, because the script needs PyYAML, which the test environment lacks
    return subprocess.run(
        ["uv", "run", "--quiet", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_repository_bucket_answers_ok_on_stdout() -> None:
    result = run()
    assert (result.returncode, result.stdout, result.stderr) == (0, '{"ok":true}\n', "")


def test_a_missing_bucket_fails_on_the_last_line_of_stderr(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = run(str(missing))
    assert (result.returncode, result.stdout) == (1, "")
    assert json.loads(result.stderr.splitlines()[-1]) == {
        "ok": False,
        "errors": [f"expected a non-symlink Matt skill bucket: {missing}"],
    }


def test_a_usage_error_answers_with_the_help_command() -> None:
    result = run("--typo")
    assert (result.returncode, result.stdout) == (2, "")
    assert json.loads(result.stderr.splitlines()[-1]) == {
        "ok": False,
        "errors": ["unrecognized arguments: --typo"],
        "help": "check_matt_mode.py --help",
    }
