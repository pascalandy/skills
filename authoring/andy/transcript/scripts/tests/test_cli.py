"""Agent-facing CLI contract for transcript.py.

These tests cover the public command tree and the one-line JSON answer. They avoid
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
        assert json.loads(stderr) == {
            "ok": False,
            "errors": ["the following arguments are required: COMMAND"],
            "help": "transcript --help",
        }

    @pytest.mark.parametrize(
        "argv,expected",
        [
            (("run", "--help"), "youtube"),
            (("run", "youtube", "--help"), "--url URL"),
            (("run", "zoom", "--help"), "--latest"),
            (("list", "--help"), "prompts"),
            (("list", "prompts", "--help"), "--no-color"),
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

    def test_a_source_error_is_one_json_line_with_its_fix_and_help(self) -> None:
        stdout, stderr, code = run_script(
            "run",
            "youtube",
            "--url",
            "https://example.com/video",
            "--no-summary",
        )

        assert code == 2
        assert stdout == ""
        assert json.loads(stderr) == {
            "ok": False,
            "errors": [
                (
                    "Invalid YouTube URL: https://example.com/video; fix: "
                    "transcript run youtube --no-summary "
                    "--url 'https://www.youtube.com/watch?v=VIDEO_ID'"
                )
            ],
            "help": "transcript run youtube --help",
        }

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
        )

        assert code == 2
        assert stdout == ""
        (error,) = json.loads(stderr)["errors"]
        assert "transcript list models --provider codex" in error
        assert "--list-models" not in error


class TestDiscovery:
    def test_list_prompts_is_one_json_line(self) -> None:
        stdout, stderr, code = run_script("list", "prompts")

        assert code == 0
        assert stderr == ""
        payload = json.loads(stdout)
        assert payload["ok"] is True
        assert "follow_along_note" in [item["name"] for item in payload["prompts"]]

    def test_list_models_names_provider_and_default(self) -> None:
        stdout, stderr, code = run_script("list", "models", "--provider", "openrouter")

        assert code == 0
        assert stderr == ""
        payload = json.loads(stdout)
        assert payload == {
            "ok": True,
            "provider": "openrouter",
            "default": "z-ai/glm-5.3-flash",
            "models": ["z-ai/glm-5.3-flash"],
        }


class TestDryRun:
    def test_a_dry_run_answers_its_plan_without_preflight(
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
            ]
        )

        assert code == 0
        assert json.loads(capsys.readouterr().out) == {
            "ok": True,
            "source": {"kind": "youtube", "url": "https://youtu.be/abc"},
            "summary": {
                "enabled": False,
                "profile": None,
                "provider": None,
                "model": None,
                "effort": None,
                "prompt": None,
            },
            "output_dir": str(transcript.OUTPUT_DIR),
            "timeout_seconds": 570.0,
        }


class TestDoctor:
    def test_doctor_checks_never_expose_deepgram_key(
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

        checks = transcript._doctor_checks(source="all", summarize=True)

        assert all(check["status"] == "pass" for check in checks)
        assert "deepgram-secret-value" not in json.dumps(checks)
        assert {check["name"] for check in checks} >= {
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

        checks = transcript._doctor_checks(source="zoom", summarize=True)

        runner_check = next(check for check in checks if check["name"] == missing)
        assert runner_check == expected

    def test_a_warning_is_verbose_detail_and_keeps_doctor_passing(
        self, monkeypatch, capsys
    ) -> None:
        import transcript

        warning = {
            "name": "pi",
            "status": "warn",
            "message": "pi was not found on PATH",
            "hint": "Install pi to use --profile astra",
        }
        monkeypatch.setattr(transcript, "_doctor_checks", lambda **_kwargs: [warning])

        assert transcript.main(["doctor"]) == 0
        assert capsys.readouterr() == ('{"ok":true}\n', "")
        assert transcript.main(["doctor", "-v"]) == 0
        assert capsys.readouterr() == (
            '{"ok":true}\n',
            (
                "[WARN] pi: pi was not found on PATH\n"
                "  fix: Install pi to use --profile astra\n"
            ),
        )

    def test_each_failed_check_is_one_error_with_its_fix(
        self, monkeypatch, capsys
    ) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_doctor_checks",
            lambda **_kwargs: [
                {
                    "name": "pi",
                    "status": "fail",
                    "message": "pi was not found on PATH",
                    "hint": "Install pi or rerun with --no-summary",
                },
                {"name": "ffmpeg", "status": "pass", "message": "ffmpeg is here"},
                {
                    "name": "ffprobe",
                    "status": "fail",
                    "message": "ffprobe was not found on PATH",
                    "hint": "brew install ffmpeg",
                },
            ],
        )

        code = transcript.main(["doctor", "--source", "youtube"])

        captured = capsys.readouterr()
        assert code == 1
        # A failed check is the error: stdout stays empty
        assert captured.out == ""
        assert json.loads(captured.err) == {
            "ok": False,
            "errors": [
                (
                    "pi: pi was not found on PATH; "
                    "fix: Install pi or rerun with --no-summary"
                ),
                "ffprobe: ffprobe was not found on PATH; fix: brew install ffmpeg",
            ],
        }


class TestStructuredRunResult:
    def test_the_answer_lists_every_saved_file_in_the_order_it_appears(
        self, tmp_path
    ) -> None:
        from datetime import UTC, datetime

        import transcript

        result_dir = tmp_path / "result"
        result_dir.mkdir()
        meta = result_dir / "meta.txt"
        raw = result_dir / "raw_transcript.txt"
        sentences = result_dir / "raw_sentences.txt"
        raw_json = result_dir / "raw_transcript.json"
        summary = result_dir / "short_summary.md"
        folder = transcript.ResultFolder(
            path=result_dir,
            asset=transcript.SourceAsset(
                "youtube", "A video", "https://youtu.be/abc", raw, "abc"
            ),
            prompt=transcript.PromptSpec("short_summary", summary.name, summary),
            started=datetime.now(UTC),
        )
        for path in (meta, raw):
            path.write_text("content", encoding="utf-8")

        assert folder.files() == [str(meta), str(raw)]

        for path in (sentences, raw_json, summary):
            path.write_text("content", encoding="utf-8")

        assert folder.files() == [
            str(meta),
            str(raw),
            str(sentences),
            str(raw_json),
            str(summary),
        ]

    def test_a_run_answers_its_files_and_streams_its_folder(
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
            ]
        )

        captured = capsys.readouterr()
        (folder,) = tmp_path.iterdir()
        assert code == 0
        assert captured.err == f"{folder}\n"
        assert json.loads(captured.out) == {
            "ok": True,
            "files": [
                str(folder / name)
                for name in (
                    "meta.txt",
                    "raw_transcript.txt",
                    "raw_sentences.txt",
                    "raw_transcript.json",
                )
            ],
        }


class TestProcessBoundary:
    def test_ctrl_c_exits_130_without_traceback(self, monkeypatch, capsys) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_dispatch",
            lambda *_args: (_ for _ in ()).throw(KeyboardInterrupt()),
        )

        assert transcript.main(["run", "youtube", "--url", "https://youtu.be/a"]) == 130
        assert capsys.readouterr() == ("", '{"ok":false,"errors":["interrupted"]}\n')

    def test_unexpected_error_names_the_debug_rerun(self, monkeypatch, capsys) -> None:
        import transcript

        monkeypatch.setattr(
            transcript,
            "_dispatch",
            lambda *_args: (_ for _ in ()).throw(RuntimeError("boom")),
        )

        code = transcript.main(["run", "youtube", "--url", "https://youtu.be/a"])

        out, err = capsys.readouterr()
        assert (code, out) == (1, "")
        assert json.loads(err) == {
            "ok": False,
            "errors": ["RuntimeError: boom"],
            "rerun": "transcript run youtube --url https://youtu.be/a --debug",
        }

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
        assert json.loads(err.splitlines()[-1]) == {
            "ok": False,
            "errors": ["RuntimeError: boom"],
        }
