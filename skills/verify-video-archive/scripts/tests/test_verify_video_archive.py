from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, cast

SCRIPT = Path(__file__).parents[1] / "verify_video_archive.py"


def load_driver() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "verify_video_archive", SCRIPT
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


driver = load_driver()


class RunFixture(unittest.TestCase):
    """A launched run on a fixture checkout, cleaned up after each test."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.evidence_parent = Path(self.temporary.name) / "evidence"
        selected = os.environ.get("VIDEO_ARCHIVE_CHECKOUT")
        self.checkout = (
            Path(selected) if selected else Path(self.temporary.name) / "checkout"
        )
        if not selected:
            self.checkout.mkdir()
            (self.checkout / "justfile").write_text(
                "convert-video:\n    @true\n", encoding="utf-8"
            )
            wrapper = self.checkout / "dot_local/bin/executable_video-archive"
            wrapper.parent.mkdir(parents=True)
            wrapper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            wrapper.chmod(0o755)
            subprocess.run(["git", "init", "-q", str(self.checkout)], check=True)
            subprocess.run(["git", "-C", str(self.checkout), "add", "."], check=True)
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(self.checkout),
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.com",
                    "commit",
                    "-qm",
                    "fixture",
                ],
                check=True,
            )
        self.checkout = self.checkout.resolve()
        self.manifest_path = driver.launch(self.checkout, self.evidence_parent)
        self.manifest = driver.load_manifest(self.manifest_path)

    def tearDown(self) -> None:
        if self.manifest_path.exists():
            try:
                driver.cleanup(self.manifest_path)
            except (OSError, TypeError, ValueError):
                pass
        self.temporary.cleanup()


class RunIsolationTests(RunFixture):
    def test_each_scenario_has_distinct_owned_paths_and_checkout_bridge(self) -> None:
        seen: set[str] = set()
        for feature in driver.FEATURES:
            paths = driver.manifest_paths(self.manifest, feature, self.manifest_path)
            current = {
                str(paths.home),
                *(str(item) for item in paths.inputs),
                str(paths.archive),
                str(paths.state),
                str(paths.journal),
                str(paths.scratch),
                str(paths.evidence),
            }
            self.assertTrue(seen.isdisjoint(current))
            seen.update(current)
            self.assertEqual(
                paths.bridge.resolve(),
                self.checkout / "dot_local/bin/executable_video-archive",
            )
            self.assertEqual(
                (paths.state / "video-archive.log").resolve(), paths.journal_file
            )

    def test_verifier_and_application_have_separate_identities(self) -> None:
        verifier = self.manifest["verifier"]
        self.assertEqual(verifier["package"], str(SCRIPT.parent.parent))
        self.assertIn(
            "scripts/verify_video_archive.py",
            {item["path"] for item in verifier["files"]},
        )
        self.assertEqual(self.manifest["checkout"], str(self.checkout))
        self.assertEqual(
            self.manifest["git"]["revision"],
            subprocess.run(
                ["git", "-C", str(self.checkout), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip(),
        )
        self.assertTrue(
            all(
                not item["path"].startswith("authoring/")
                for item in self.manifest["tested_files"]
            )
        )

    def test_evidence_references_survive_bundle_relocation(self) -> None:
        paths = driver.manifest_paths(self.manifest, "conversion", self.manifest_path)
        transcript = paths.evidence / "commands" / "stdout.txt"
        transcript.parent.mkdir(parents=True)
        transcript.write_text("real command output\n", encoding="utf-8")
        self.manifest["invocations"] = [
            {
                "stdout": driver.evidence_reference(self.manifest_path, transcript),
                "stderr": driver.evidence_reference(self.manifest_path, transcript),
            }
        ]
        driver.save_manifest(self.manifest_path, self.manifest)
        self.assertEqual(driver.evidence(self.manifest_path)["evidence_missing"], [])
        driver.cleanup(self.manifest_path)
        relocated = Path(self.temporary.name) / "relocated"
        shutil.copytree(self.manifest_path.parent, relocated)
        relocated_manifest = relocated / "manifest.json"

        summary = driver.evidence(relocated_manifest)
        relocated_document = driver.load_manifest(relocated_manifest)

        self.assertEqual(summary["verdict"], "passed")
        self.assertEqual(summary["evidence_missing"], [])
        self.assertEqual(relocated_document["phase"], "cleaned")
        files = cast(list[dict[str, object]], relocated_document["evidence_files"])
        for item in files:
            reference = item["path"]
            assert isinstance(reference, str)
            self.assertTrue((relocated / reference).is_file())

    def test_tampered_evidence_fails_every_validation_without_rebaselining(
        self,
    ) -> None:
        paths = driver.manifest_paths(self.manifest, "conversion", self.manifest_path)
        artifact = paths.evidence / "artifact.txt"
        artifact.write_text("trusted\n", encoding="utf-8")
        self.assertEqual(driver.evidence(self.manifest_path)["evidence_missing"], [])
        trusted_manifest = driver.load_manifest(self.manifest_path)
        trusted_inventory = trusted_manifest["evidence_files"]
        artifact.write_text("tampered\n", encoding="utf-8")

        first = driver.evidence(self.manifest_path)
        second = driver.evidence(self.manifest_path)
        observed = driver.load_manifest(self.manifest_path)

        reference = driver.evidence_reference(self.manifest_path, artifact)
        self.assertEqual(first["verdict"], "failed")
        self.assertIn(reference, first["evidence_missing"])
        self.assertEqual(second["verdict"], "failed")
        self.assertIn(reference, second["evidence_missing"])
        self.assertEqual(observed["evidence_files"], trusted_inventory)

    def test_cleanup_removes_only_run_root_and_preserves_evidence(self) -> None:
        run_root = Path(self.manifest["paths"]["run_root"])

        result = driver.cleanup(self.manifest_path)

        self.assertEqual(result["status"], "removed")
        self.assertFalse(run_root.exists())
        self.assertTrue(self.manifest_path.is_file())
        self.assertEqual(
            driver.cleanup(self.manifest_path)["status"], "already-removed"
        )

    def test_cleanup_refuses_a_mismatched_owner_marker(self) -> None:
        run_root = Path(self.manifest["paths"]["run_root"])
        owner_path = run_root / "owner.json"
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        owner["token"] = "not-the-run-token"
        owner_path.write_text(json.dumps(owner), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "does not match"):
            driver.cleanup(self.manifest_path)

        self.assertTrue(run_root.is_dir())
        owner["token"] = self.manifest["owner_token"]
        owner_path.write_text(json.dumps(owner), encoding="utf-8")

    def test_pty_driver_reaches_eof_and_retains_the_terminal_transcript(self) -> None:
        if not os.environ.get("VIDEO_ARCHIVE_CHECKOUT"):
            self.skipTest(
                "set VIDEO_ARCHIVE_CHECKOUT to run the A application integration"
            )
        paths = driver.manifest_paths(self.manifest, "conversion", self.manifest_path)

        record = driver.run_just_pty(
            self.manifest,
            self.manifest_path,
            paths,
            "pty-no-work",
            width=48,
            no_color=True,
            timeout=10,
        )
        transcript = driver.invocation_text(self.manifest_path, record)

        self.assertEqual(record["exit_status"], 0)
        self.assertEqual(record["terminal_width"], 48)
        self.assertIn("No work: 0 videos found.", transcript)


class AnswerTests(RunFixture):
    """Each command answers in one JSON line; no case here touches real media."""

    def setUp(self) -> None:
        super().setUp()
        # Only git, and sysctl where the run reads the CPU name, on PATH: doctor
        # finds no media tools, so drive starts no scenario
        self.bin = Path(self.temporary.name) / "bin"
        self.bin.mkdir()
        git = shutil.which("git")
        assert git is not None
        (self.bin / "git").symlink_to(git)
        if sysctl := shutil.which("sysctl"):
            (self.bin / "sysctl").symlink_to(sysctl)

    def answer(self, *args: str) -> tuple[int, str, dict[str, Any]]:
        """The exit code, stdout, and the JSON line that ends the output."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            env={**os.environ, "PATH": str(self.bin)},
            capture_output=True,
            text=True,
            check=False,
        )
        stream = result.stderr if result.returncode else result.stdout
        if not result.returncode:
            self.assertEqual(result.stderr, "")
        return (
            result.returncode,
            result.stdout,
            json.loads(stream.splitlines()[-1]),
        )

    def test_launch_answers_the_manifest_it_writes(self) -> None:
        code, stdout, answer = self.answer(
            "launch",
            "--checkout",
            str(self.checkout),
            "--evidence-root",
            str(self.evidence_parent),
        )
        manifest = Path(answer["file"])
        driver.cleanup(manifest)

        self.assertEqual(code, 0)
        self.assertEqual(stdout.count("\n"), 1)
        self.assertEqual(answer, {"ok": True, "file": str(manifest)})
        self.assertTrue(manifest.is_absolute())
        self.assertTrue(manifest.is_file())

    def test_unmet_checks_fail_with_one_error_each(self) -> None:
        manifest = str(self.manifest_path)

        doctor = self.answer("doctor", "--manifest", manifest)
        drive = self.answer("drive", "--manifest", manifest, "--feature", "conversion")

        self.assertEqual(doctor[:2], (1, ""))
        self.assertIs(doctor[2]["ok"], False)
        self.assertIn(
            'doctor.ffmpeg unmet: FFmpeg is available; expected "resolved '
            + 'executable", observed null',
            doctor[2]["errors"],
        )
        self.assertEqual(drive[:2], (1, ""))
        self.assertEqual(
            drive[2]["errors"],
            [
                *doctor[2]["errors"],
                (
                    "conversion.platform skipped: The real-media scenario was not "
                    "run because doctor found an unmet requirement"
                    + '; expected "all doctor checks passed", observed "scenario not started"'
                ),
            ],
        )

    def test_run_names_the_manifest_beside_its_errors(self) -> None:
        code, stdout, answer = self.answer(
            "run",
            "--checkout",
            str(self.checkout),
            "--evidence-root",
            str(self.evidence_parent),
            "--feature",
            "conversion",
        )
        manifest = Path(answer["file"])

        self.assertEqual((code, stdout), (1, ""))
        self.assertIn("conversion.platform skipped", str(answer["errors"]))
        self.assertEqual(driver.load_manifest(manifest)["phase"], "cleaned")

    def test_cleanup_answers_the_root_it_removes(self) -> None:
        run_root = self.manifest["paths"]["run_root"]

        first = self.answer("cleanup", "--manifest", str(self.manifest_path))
        second = self.answer("cleanup", "--manifest", str(self.manifest_path))

        self.assertEqual(
            first, (0, first[1], {"ok": True, "changes": [["remove", run_root]]})
        )
        self.assertEqual(second, (0, '{"ok":true}\n', {"ok": True}))

    def test_a_verifier_error_answers_what_to_run_first(self) -> None:
        answer = self.answer("drive", "--manifest", str(self.manifest_path))

        self.assertEqual(
            answer, (1, "", {"ok": False, "errors": ["run doctor before drive"]})
        )

    def test_a_usage_error_answers_the_help_command(self) -> None:
        answer = self.answer("drive", "--feature", "conversion")

        self.assertEqual(
            answer,
            (
                2,
                "",
                {
                    "ok": False,
                    "errors": ["the following arguments are required: --manifest"],
                    "help": "verify-video-archive --help",
                },
            ),
        )


class VerdictTests(unittest.TestCase):
    def test_skipped_and_unmet_checks_cannot_produce_a_pass(self) -> None:
        manifest = {
            "doctor": [{"status": "unmet"}],
            "scenarios": {"conversion": {"checks": [{"status": "skipped"}]}},
        }

        driver.recompute_summary(manifest)

        self.assertEqual(manifest["summary"]["verdict"], "unmet")
        self.assertEqual(manifest["summary"]["passed"], 0)


if __name__ == "__main__":
    unittest.main()
