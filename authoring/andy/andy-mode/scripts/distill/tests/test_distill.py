from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

import pytest

SCRIPT_PATH = Path(__file__).parent.parent / "distill.py"
PROMPTS_DIR = SCRIPT_PATH.parent.parent.parent / "references" / "distill-prompt"
E2E_INPUT_DIR = Path.home() / "Documents" / "_my_docs" / "62_distill_exports"
E2E_INPUT_PATH = E2E_INPUT_DIR / "raw_transcript.txt"


def make_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def make_fake_claude(bin_dir: Path) -> None:
    make_executable(
        bin_dir / "claude",
        """#!/usr/bin/env -S uv run --no-project python
import json
print(json.dumps({
    \"result\": \"## Distilled output\",
    \"usage\": {\"input_tokens\": 12, \"output_tokens\": 7}
}))
""",
    )


def make_asserting_fake_claude(bin_dir: Path, expected_snippet: str) -> None:
    make_executable(
        bin_dir / "claude",
        f"""#!/usr/bin/env -S uv run --no-project python
import json
import sys

args = sys.argv[1:]

def require(flag: str) -> str:
    try:
        index = args.index(flag)
    except ValueError:
        print(f"missing flag: {{flag}}", file=sys.stderr)
        raise SystemExit(2)
    try:
        return args[index + 1]
    except IndexError:
        print(f"missing value for: {{flag}}", file=sys.stderr)
        raise SystemExit(2)

system_prompt = require("--system-prompt")
user_message = args[-1] if args else ""

if "Quick high-level summary" not in system_prompt:
    print("short-summary prompt was not passed to claude", file=sys.stderr)
    raise SystemExit(3)

if {expected_snippet!r} not in user_message:
    print("input transcript content was not passed to claude", file=sys.stderr)
    raise SystemExit(4)

print(json.dumps({{
    \"result\": \"## VaultWarden Summary\\n\\n### Overview\\n\\nA quick integration summary.\",
    \"usage\": {{\"input_tokens\": 42, \"output_tokens\": 9}}
}}))
""",
    )


def make_fake_opencode(bin_dir: Path) -> None:
    make_executable(
        bin_dir / "opencode",
        """#!/usr/bin/env -S uv run --no-project python
import json
import sys

args = sys.argv[1:]

if args[:1] == ["run"]:
    payload = sys.stdin.read()
    if "hello from opencode" not in payload:
        print("stdin payload was not passed to opencode", file=sys.stderr)
        raise SystemExit(4)

    if "--agent" not in args:
        print("missing --agent", file=sys.stderr)
        raise SystemExit(2)

    if "--format" not in args:
        print("missing --format", file=sys.stderr)
        raise SystemExit(2)

    print("OK: 0 plugin file(s)")
    print(json.dumps({"type": "step_start"}))
    print(json.dumps({"type": "text", "part": {"text": "## OpenCode output"}}))
    print(json.dumps({"type": "step_finish"}))
    raise SystemExit(0)

print("unsupported command", file=sys.stderr)
raise SystemExit(9)
""",
    )


def make_asserting_fake_opencode(bin_dir: Path, expected_snippet: str) -> None:
    make_executable(
        bin_dir / "opencode",
        f"""#!/usr/bin/env -S uv run --no-project python
import json
import sys

args = sys.argv[1:]

if args[:1] != ["run"]:
    print("unsupported command", file=sys.stderr)
    raise SystemExit(9)

if "--agent" not in args:
    print("missing --agent", file=sys.stderr)
    raise SystemExit(2)

if "--format" not in args:
    print("missing --format", file=sys.stderr)
    raise SystemExit(2)

payload = sys.stdin.read()
if "Quick high-level summary" not in payload:
    print("short-summary prompt was not passed to opencode", file=sys.stderr)
    raise SystemExit(3)

if {expected_snippet!r} not in payload:
    print("input transcript content was not passed to opencode", file=sys.stderr)
    raise SystemExit(4)

print("OK: 0 plugin file(s)")
print(json.dumps({{"type": "step_start"}}))
print(json.dumps({{"type": "text", "part": {{"text": "## VaultWarden OpenCode Summary\\n\\n### Overview\\n\\nA quick integration summary."}}}}))
print(json.dumps({{"type": "step_finish", "part": {{"tokens": {{"total": 51}}}}}}))
""",
    )


def run_script(*args: str, env: dict[str, str] | None = None) -> tuple[str, str, int]:
    result = subprocess.run(
        ["uv", "run", str(SCRIPT_PATH), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
        env=env,
    )
    return result.stdout, result.stderr, result.returncode


def answer(stdout: str, stderr: str, code: int) -> dict[str, Any]:
    """The one JSON line distill answers with: all of stdout on success, or the
    last line of stderr, with stdout empty, on failure."""
    if code == 0:
        assert stdout.count("\n") == 1, stdout
        return json.loads(stdout)
    assert stdout == ""
    return json.loads(stderr.splitlines()[-1])


def env_with_fake_claude(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    make_fake_claude(bin_dir)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return env


def env_with_fake_opencode(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    make_fake_opencode(bin_dir)

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return env


class TestPromptDiscovery:
    def test_help_prints_prompt_driven_interface(self) -> None:
        stdout, _stderr, code = run_script("--help")

        assert code == 0
        assert "--list-prompts" in stdout
        assert "--prompt STEM" in stdout

    def test_list_prompts_lists_library_names(self) -> None:
        result = run_script("--list-prompts")

        assert answer(*result) == {
            "ok": True,
            "prompts": [
                "extract_wisdom",
                "follow_along_note",
                "short_summary",
                "summary_with_quotes",
                "synthese_rencontre",
            ],
        }

    def test_list_models_puts_each_default_first(self) -> None:
        result = run_script("--list-models", "--provider", "opencode")

        assert answer(*result) == {
            "ok": True,
            "models": {"opencode": ["1-glm", "2-luna", "3-sol", "4-astra", "5-qwen"]},
        }


class TestPromptDrivenCli:
    def test_dry_run_uses_default_prompt(self, tmp_path: Path) -> None:
        env = env_with_fake_claude(tmp_path)
        input_file = tmp_path / "article.md"
        input_file.write_text("hello world\n", encoding="utf-8")

        result = run_script(str(input_file), "--dry-run", env=env)

        plan = answer(*result)
        assert plan["ok"] is True
        assert plan["prompt"] == "follow_along_note"
        assert plan["prompt_file"].endswith("follow-along-note/prompt.md")
        assert plan["file"].endswith("_follow_along_note/article_follow_along_note.md")
        # A dry run writes nothing
        assert sorted(path.name for path in tmp_path.iterdir()) == ["article.md", "bin"]

    def test_prompt_flag_accepts_underscore_stem(self, tmp_path: Path) -> None:
        env = env_with_fake_claude(tmp_path)
        input_file = tmp_path / "notes.txt"
        input_file.write_text("hello world\n", encoding="utf-8")

        result = run_script(
            "--prompt",
            "short_summary",
            str(input_file),
            "--dry-run",
            env=env,
        )

        plan = answer(*result)
        assert plan["prompt"] == "short_summary"
        assert plan["prompt_file"].endswith("short-summary/prompt.md")

    def test_real_run_writes_planned_artifacts(self, tmp_path: Path) -> None:
        env = env_with_fake_claude(tmp_path)
        input_file = tmp_path / "article.md"
        input_file.write_text("hello world\n", encoding="utf-8")

        stdout, stderr, code = run_script(
            "--prompt",
            "short_summary",
            str(input_file),
            "--no-open",
            env=env,
        )

        assert code == 0, stderr
        run_dirs = [
            path
            for path in tmp_path.iterdir()
            if path.is_dir() and path.name.startswith("article_")
        ]
        assert len(run_dirs) == 1

        run_dir = run_dirs[0]
        slug = input_file.stem
        raw_copy = run_dir / f"{slug}_raw{input_file.suffix}"
        output_file = run_dir / f"{slug}_short_summary.md"
        assert answer(stdout, stderr, code) == {"ok": True, "file": str(output_file)}
        assert output_file.read_text(encoding="utf-8") == "## Distilled output\n"
        assert (run_dir / f"{slug}_meta.yml").exists()
        assert raw_copy.exists()
        assert raw_copy.read_text(encoding="utf-8") == input_file.read_text(
            encoding="utf-8"
        )


class TestOpenCodeProvider:
    def test_opencode_real_run_writes_text_events(self, tmp_path: Path) -> None:
        env = env_with_fake_opencode(tmp_path)
        input_file = tmp_path / "article.md"
        input_file.write_text("hello from opencode\n", encoding="utf-8")

        _stdout, stderr, code = run_script(
            "--provider",
            "opencode",
            str(input_file),
            "--no-open",
            env=env,
        )

        assert code == 0, stderr
        run_dirs = [
            path
            for path in tmp_path.iterdir()
            if path.is_dir() and path.name.startswith("article_")
        ]
        assert len(run_dirs) == 1
        slug = input_file.stem
        assert (run_dirs[0] / f"{slug}_follow_along_note.md").read_text(
            encoding="utf-8"
        ) == ("## OpenCode output\n")

    def test_opencode_rejects_effort_flag(self, tmp_path: Path) -> None:
        env = env_with_fake_opencode(tmp_path)
        input_file = tmp_path / "article.md"
        input_file.write_text("hello from opencode\n", encoding="utf-8")

        result = run_script(
            "--provider",
            "opencode",
            "--effort",
            "high",
            str(input_file),
            "--dry-run",
            env=env,
        )

        assert result[2] == 2
        assert answer(*result) == {
            "ok": False,
            "errors": ["--effort is not supported with --provider opencode"],
            "help": "distill.py --help",
        }


class TestFailures:
    def test_missing_input_is_a_usage_error(self) -> None:
        result = run_script()

        assert result[2] == 2
        assert answer(*result)["help"] == "distill.py --help"

    def test_unknown_prompt_exits_four(self, tmp_path: Path) -> None:
        input_file = tmp_path / "article.md"
        input_file.write_text("hello world\n", encoding="utf-8")

        result = run_script(str(input_file), "--prompt", "nope", "--dry-run")

        assert result[2] == 4
        assert answer(*result) == {
            "ok": False,
            "errors": [
                "Unknown prompt stem: nope. Run with --list-prompts to see the list."
            ],
        }


@pytest.mark.skipif(not E2E_INPUT_PATH.exists(), reason="E2E input file is unavailable")
class TestEndToEndWithRealTranscript:
    def test_short_summary_prompt_flows_from_library_into_provider(
        self, tmp_path: Path
    ) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        make_asserting_fake_claude(
            bin_dir,
            expected_snippet="Most people now think password managers are just another subscription",
        )

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"

        _stdout, stderr, code = run_script(
            "--prompt",
            "short_summary",
            str(E2E_INPUT_PATH),
            "--output-dir",
            str(tmp_path),
            "--no-open",
            env=env,
        )

        assert code == 0, stderr

        run_dirs = [
            path
            for path in tmp_path.iterdir()
            if path.is_dir() and path.name.startswith("raw_transcript_")
        ]
        assert len(run_dirs) == 1

        run_dir = run_dirs[0]
        slug = E2E_INPUT_PATH.stem
        output_file = run_dir / f"{slug}_short_summary.md"
        assert output_file.exists()
        assert "VaultWarden Summary" in output_file.read_text(encoding="utf-8")
        copied_input = run_dir / f"{slug}_raw{E2E_INPUT_PATH.suffix}"
        assert copied_input.exists()

    def test_short_summary_prompt_flows_from_library_into_opencode(
        self, tmp_path: Path
    ) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        make_asserting_fake_opencode(
            bin_dir,
            expected_snippet="Most people now think password managers are just another subscription",
        )

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}:{env['PATH']}"

        _stdout, stderr, code = run_script(
            "--provider",
            "opencode",
            "--prompt",
            "short_summary",
            str(E2E_INPUT_PATH),
            "--output-dir",
            str(tmp_path),
            "--no-open",
            env=env,
        )

        assert code == 0, stderr

        run_dirs = [
            path
            for path in tmp_path.iterdir()
            if path.is_dir() and path.name.startswith("raw_transcript_")
        ]
        assert len(run_dirs) == 1

        run_dir = run_dirs[0]
        slug = E2E_INPUT_PATH.stem
        output_file = run_dir / f"{slug}_short_summary.md"
        assert output_file.exists()
        assert "VaultWarden OpenCode Summary" in output_file.read_text(encoding="utf-8")
        copied_input = run_dir / f"{slug}_raw{E2E_INPUT_PATH.suffix}"
        assert copied_input.exists()
