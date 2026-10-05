"""Agent-facing CLI contract for transcript.py.

These tests cover the public command tree and structured output. They avoid
network calls and paid services.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from cli_support import run_script


class TestCommandTree:
    def test_no_args_is_a_usage_error_that_points_to_help(self) -> None:
        stdout, stderr, code = run_script()

        assert code == 2
        assert stdout == ""
        assert stderr.startswith("usage: transcript ")
        assert "the following arguments are required: COMMAND" in stderr
        assert stderr.splitlines()[-1] == "run 'transcript --help'"

    @pytest.mark.parametrize(
        "argv,expected",
        [
            (("run", "--help"), "youtube"),
            (("run", "youtube", "--help"), "--url URL"),
            (("run", "zoom", "--help"), "--latest"),
            (("list", "--help"), "prompts"),
            (("list", "prompts", "--help"), "--json"),
            (("list", "models", "--help"), "--provider"),
            (("doctor", "--help"), "--source"),
        ],
    )
    def test_every_command_has_focused_help(
        self, argv: tuple[str, ...], expected: str
    ) -> None:
        stdout, stderr, code = run_script(*argv)

        assert code == 0
        assert stderr == ""
        assert expected in stdout
        assert "examples:" in stdout

    def test_old_flat_syntax_fails_with_migration_hint(self) -> None:
        _stdout, stderr, code = run_script("https://youtu.be/abc")

        assert code == 2
        assert "transcript run youtube --url" in stderr


class TestParsing:
    def test_youtube_command_normalizes_for_pipeline(self) -> None:
        import transcript

        args = transcript.parse_args(
            [
                "run",
                "youtube",
                "--url",
                "https://youtu.be/abc",
                "--output-dir",
                "/tmp/transcripts",
                "--no-summary",
                "--dry-run",
                "--json",
            ]
        )

        assert args.command == "run"
        assert args.source == "youtube"
        assert args.url == "https://youtu.be/abc"
        assert args.output_dir == Path("/tmp/transcripts")
        assert args.zoom is False
        assert args.zoom_custom_path is None
        assert args.no_prompt is True
        assert args.dry_run is True
        assert args.json is True

    @pytest.mark.parametrize(
        "selector,zoom,custom_path",
        [
            (("--latest",), True, None),
            (("--path", "meeting"), False, "meeting"),
        ],
    )
    def test_zoom_selectors_normalize_for_pipeline(
        self,
        selector: tuple[str, ...],
        zoom: bool,
        custom_path: str | None,
    ) -> None:
        import transcript

        args = transcript.parse_args(["run", "zoom", *selector, "--no-summary"])

        assert args.source == "zoom"
        assert args.url is None
        assert args.zoom is zoom
        assert args.zoom_custom_path == custom_path
        assert args.no_prompt is True

    def test_json_and_preview_are_rejected_before_execution(self) -> None:
        _stdout, stderr, code = run_script(
            "run",
            "youtube",
            "--url",
            "https://youtu.be/abc",
            "--json",
            "--preview",
        )

        assert code == 2
        payload = json.loads(stderr)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "invalid_usage"
        assert "--preview" in payload["error"]["message"]
        assert "--help" in payload["error"]["hint"]

    def test_json_source_error_is_one_document(self) -> None:
        stdout, stderr, code = run_script(
            "run",
            "youtube",
            "--url",
            "https://example.com/video",
            "--no-summary",
            "--json",
        )

        assert code == 2
        assert stdout == ""
        payload = json.loads(stderr)
        assert payload["ok"] is False
        assert payload["error"]["code"] == "invalid_source"
        assert payload["error"]["hint"] == (
            "transcript run youtube --no-summary --json "
            "--url 'https://www.youtube.com/watch?v=VIDEO_ID'"
        )

    def test_invalid_model_names_the_current_discovery_command(self) -> None:
        stdout, stderr, code = run_script(
            "run",
            "youtube",
            "--url",
            "https://youtu.be/abc",
            "--provider",
            "codex",
            "--model",
            "",
            "--effort",
            "low",
            "--dry-run",
            "--json",
        )

        assert code == 2
        assert stdout == ""
        payload = json.loads(stderr)
        assert payload["error"]["code"] == "invalid_configuration"
        assert "transcript list models --provider codex" in payload["error"]["message"]
        assert "--list-models" not in payload["error"]["message"]


class TestDiscovery:
    def test_list_prompts_json_is_one_document(self) -> None:
        stdout, stderr, code = run_script("list", "prompts", "--json")

        assert code == 0
        assert stderr == ""
        payload = json.loads(stdout)
        assert payload["ok"] is True
        assert payload["command"] == "list prompts"
        assert "follow_along_note" in [item["name"] for item in payload["prompts"]]

    def test_list_models_json_names_provider_and_default(self) -> None:
        stdout, stderr, code = run_script(
            "list", "models", "--provider", "openrouter", "--json"
        )

        assert code == 0
        assert stderr == ""
        payload = json.loads(stdout)
        assert payload == {
            "ok": True,
            "command": "list models",
            "provider": "openrouter",
            "default": "z-ai/glm-5.3-flash",
            "models": ["z-ai/glm-5.3-flash"],
        }


class TestDryRun:
    def test_json_dry_run_resolves_plan_without_preflight(
        self, monkeypatch, capsys
    ) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_preflight",
            lambda *_args: pytest.fail("dry-run reached execution preflight"),
        )
        monkeypatch.setattr(
            transcript,
            "_acquire_source",
            lambda *_args: pytest.fail("dry-run started media work"),
        )

        code = transcript.main(
            [
                "run",
                "youtube",
                "--url",
                "https://youtu.be/abc",
                "--no-summary",
                "--dry-run",
                "--json",
            ]
        )

        assert code == 0
        payload = json.loads(capsys.readouterr().out)
        assert payload["ok"] is True
        assert payload["command"] == "run"
        assert payload["dry_run"] is True
        assert payload["source"] == {
            "kind": "youtube",
            "url": "https://youtu.be/abc",
        }
        assert payload["summary"]["enabled"] is False
        assert payload["side_effects"] == []


class TestDoctor:
    def test_doctor_report_never_exposes_deepgram_key(
        self, monkeypatch, tmp_path
    ) -> None:
        import transcript

        zoom_root = tmp_path / "Zoom"
        zoom_root.mkdir()
        arc_profile = tmp_path / "Arc" / "Default"
        arc_profile.mkdir(parents=True)
        monkeypatch.setattr(transcript, "ZOOM_ROOT", zoom_root)
        monkeypatch.setattr(transcript, "ARC_BROWSER_PROFILE", arc_profile)
        monkeypatch.setattr(
            transcript,
            "validate_env",
            lambda *_args: "deepgram-secret-value",
        )
        monkeypatch.setattr(transcript.shutil, "which", lambda _name: "/bin/tool")
        monkeypatch.setattr(
            transcript,
            "_installed_ytdlp_version",
            lambda: "2026.7.4",
        )

        report = transcript._doctor_report(source="all", summarize=True)

        serialized = json.dumps(report)
        assert report["ok"] is True
        assert "deepgram-secret-value" not in serialized
        assert {check["name"] for check in report["checks"]} >= {
            "deepgram_credential",
            "claude",
            "pi",
            "ffmpeg",
            "ffprobe",
            "yt_dlp",
            "youtube_browser",
            "zoom_recordings",
        }

    @pytest.mark.parametrize(
        "missing,expected",
        [
            (
                "claude",
                {
                    "name": "claude",
                    "status": "fail",
                    "message": "claude was not found on PATH",
                    "hint": "Install claude, or skip summary checks: "
                    "transcript doctor --no-summary",
                },
            ),
            (
                "pi",
                {
                    "name": "pi",
                    "status": "warn",
                    "message": "pi was not found on PATH; "
                    "only the astra, sol, glm profiles need it",
                    "hint": "Install pi to use --profile astra",
                },
            ),
        ],
    )
    def test_only_the_default_summary_runner_is_required(
        self, monkeypatch, tmp_path, missing, expected
    ) -> None:
        import transcript

        monkeypatch.setattr(transcript, "ZOOM_ROOT", tmp_path)
        monkeypatch.setattr(transcript, "validate_env", lambda *_args: "secret")
        monkeypatch.setattr(
            transcript.shutil,
            "which",
            lambda name: None if name == missing else f"/bin/{name}",
        )

        report = transcript._doctor_report(source="zoom", summarize=True)

        runner_check = next(
            check for check in report["checks"] if check["name"] == missing
        )
        assert runner_check == expected
        assert report["ok"] is (expected["status"] != "fail")

    def test_doctor_failure_is_actionable_json(self, monkeypatch, capsys) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_doctor_report",
            lambda **_kwargs: {
                "ok": False,
                "command": "doctor",
                "source": "youtube",
                "summary": True,
                "checks": [
                    {
                        "name": "pi",
                        "status": "fail",
                        "message": "pi was not found on PATH",
                        "hint": "Install pi or rerun with --no-summary",
                    }
                ],
                "counts": {"pass": 0, "warn": 0, "fail": 1},
            },
        )

        code = transcript.main(["doctor", "--source", "youtube", "--json"])

        captured = capsys.readouterr()
        assert code == 1
        # A failed report is the error: stdout stays empty
        assert captured.out == ""
        payload = json.loads(captured.err)
        assert payload["ok"] is False
        assert payload["checks"][0]["hint"] == "Install pi or rerun with --no-summary"
        assert payload["error"] == {
            "code": "doctor_failed",
            "message": "1 required check failed: pi",
            "hint": "Install pi or rerun with --no-summary",
        }


class TestStructuredRunResult:
    def test_payload_names_every_saved_artifact(self, tmp_path) -> None:
        from datetime import UTC, datetime

        import transcript

        result_dir = tmp_path / "result"
        result_dir.mkdir()
        raw = result_dir / "raw_transcript.txt"
        sentences = result_dir / "raw_sentences.txt"
        raw_json = result_dir / "raw_transcript.json"
        summary = result_dir / "short_summary.md"
        meta = result_dir / "meta.txt"
        for path in (raw, sentences, raw_json, summary, meta):
            path.write_text("content", encoding="utf-8")

        payload = transcript._run_result_payload(
            plan=transcript.RunPlan(
                source_kind="youtube",
                provider="codex",
                model="gpt-5.6-sol",
                effort="medium",
                summarize=True,
            ),
            folder=transcript.ResultFolder(
                path=result_dir,
                asset=transcript.SourceAsset(
                    "youtube", "A video", "https://youtu.be/abc", raw, "abc"
                ),
                prompt=None,
                started=datetime.now(UTC),
            ),
            saved_files={
                "transcript": raw,
                "sentences": sentences,
                "json": raw_json,
            },
            outcome=transcript.SummaryOutcome(status="succeeded", path=summary),
        )

        assert payload["ok"] is True
        assert payload["output_dir"] == str(result_dir)
        assert payload["summary"]["status"] == "succeeded"
        assert payload["artifacts"] == {
            "transcript": str(raw),
            "sentences": str(sentences),
            "json": str(raw_json),
            "metadata": str(meta),
            "summary": str(summary),
        }

    def test_json_run_suppresses_human_progress(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        import transcript

        monkeypatch.setattr(transcript, "validate_env", lambda *_args: "secret")

        def fake_download(_url, output_dir, *_args, **_kwargs):
            audio = output_dir / "audio.webm"
            audio.write_bytes(b"audio")
            return transcript.DownloadedAudio(audio, "anonymous", "A video", "abc")

        monkeypatch.setattr(transcript, "download_audio", fake_download)
        monkeypatch.setattr(
            transcript,
            "transcribe_audio",
            lambda *_args: {
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "Hello world",
                                    "paragraphs": {
                                        "paragraphs": [
                                            {
                                                "sentences": [
                                                    {
                                                        "start": 1.0,
                                                        "end": 2.0,
                                                        "text": "Hello world",
                                                    }
                                                ]
                                            }
                                        ]
                                    },
                                }
                            ]
                        }
                    ]
                }
            },
        )

        code = transcript.main(
            [
                "run",
                "youtube",
                "--url",
                "https://youtu.be/abc",
                "--no-summary",
                "--output-dir",
                str(tmp_path),
                "--json",
            ]
        )

        captured = capsys.readouterr()
        assert code == 0
        assert captured.err == ""
        payload = json.loads(captured.out)
        assert payload["ok"] is True
        assert payload["summary"]["status"] == "skipped"


class TestProcessBoundary:
    def test_ctrl_c_exits_130_without_traceback(self, monkeypatch, capsys) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_dispatch",
            lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()),
        )

        assert transcript.main(["run", "youtube", "--url", "https://youtu.be/a"]) == 130
        assert capsys.readouterr() == ("", "interrupted\n")

    def test_unexpected_error_names_the_debug_rerun(self, monkeypatch, capsys) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_dispatch",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        code = transcript.main(["run", "youtube", "--url", "https://youtu.be/a"])

        assert code == 1
        assert capsys.readouterr() == (
            "",
            (
                "error: RuntimeError: boom\n"
                "rerun: transcript run youtube --url https://youtu.be/a --debug\n"
            ),
        )

    def test_debug_prints_the_traceback_and_keeps_the_exit_code(
        self, monkeypatch, capsys
    ) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_dispatch",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        code = transcript.main(
            ["run", "youtube", "--url", "https://youtu.be/a", "--debug"]
        )

        err = capsys.readouterr().err
        assert code == 1
        assert "Traceback (most recent call last)" in err
        assert err.splitlines()[-2:] == [
            "error: RuntimeError: boom",
            "report: report the traceback above as a bug",
        ]
