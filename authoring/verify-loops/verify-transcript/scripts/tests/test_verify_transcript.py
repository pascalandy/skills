import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "verify_transcript.py"
SPEC = importlib.util.spec_from_file_location("verify_transcript", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verify_transcript = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify_transcript
SPEC.loader.exec_module(verify_transcript)


def test_public_identity_matches_skill_name():
    skill_name = SCRIPT.parents[1].name
    help_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    version_result = subprocess.run(
        [sys.executable, str(SCRIPT), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert help_result.returncode == 0
    assert help_result.stdout.startswith(f"usage: {skill_name} ")
    assert version_result.returncode == 0
    assert version_result.stdout.startswith(f"{skill_name} ")


def test_default_evidence_root_preserves_existing_namespace(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    assert verify_transcript.default_evidence_root() == (
        tmp_path / "eval-transcript" / "runs"
    )


def make_transcript_skill(path: Path) -> None:
    (path / "scripts").mkdir(parents=True)
    (path / "SKILL.md").write_text("---\nname: transcript\n---\n")
    (path / "scripts" / "transcript.py").write_text("print('transcript')\n")


def make_context(tmp_path: Path, *, allow_paid: bool = False):
    transcript_dir = tmp_path / "transcript"
    make_transcript_skill(transcript_dir)
    scratch = verify_transcript.create_scratch("test-run")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    located = verify_transcript.LocatedSkill(
        transcript_dir,
        transcript_dir / "scripts" / "transcript.py",
        "applied",
    )
    return verify_transcript.RunContext(
        run_id="test-run",
        located=located,
        scratch_dir=scratch,
        evidence_dir=evidence,
        allow_paid=allow_paid,
        youtube_url=verify_transcript.CANONICAL_YOUTUBE_URL,
    )


def test_locates_categorized_source_layout(tmp_path: Path):
    verify_dir = tmp_path / "skills" / "verify-loops" / "verify-transcript"
    transcript_dir = tmp_path / "skills" / "andy" / "transcript"
    verify_dir.mkdir(parents=True)
    make_transcript_skill(transcript_dir)

    located = verify_transcript.locate_transcript_skill(verify_dir)

    assert located.layout == "source"
    assert located.directory == transcript_dir


def test_locates_flat_applied_layout(tmp_path: Path, monkeypatch):
    skills_dir = tmp_path / "skills"
    verify_dir = skills_dir / "verify-transcript"
    transcript_dir = skills_dir / "transcript"
    verify_dir.mkdir(parents=True)
    make_transcript_skill(transcript_dir)
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)

    located = verify_transcript.locate_transcript_skill(verify_dir)

    assert located.layout == "applied"
    assert located.directory == transcript_dir


def test_missing_layout_error_lists_both_candidates(tmp_path: Path):
    verify_dir = tmp_path / "skills" / "verify-loops" / "verify-transcript"
    verify_dir.mkdir(parents=True)

    with pytest.raises(verify_transcript.VerificationError) as caught:
        verify_transcript.locate_transcript_skill(verify_dir)

    assert caught.value.code == "transcript_skill_not_found"
    assert "andy/transcript" in caught.value.hint
    assert "skills/verify-loops/transcript" in caught.value.hint


def test_paid_selection_requires_feature_and_gate():
    defaults = verify_transcript.select_features((), False, True)
    assert all(not feature.paid for feature in defaults)

    with pytest.raises(verify_transcript.VerificationError) as caught:
        verify_transcript.select_features(("youtube.real-summary",), False, False)
    assert caught.value.code == "paid_intent_required"
    assert caught.value.exit_code == 2

    selected = verify_transcript.select_features(
        ("youtube.real-summary",), False, True
    )
    assert [feature.id for feature in selected] == ["youtube.real-summary"]


def test_every_feature_is_mapped_to_its_pages():
    feature_dir = SCRIPT.parents[1] / "features"
    expected_headings = [
        "## Sub-features",
        "## How to get to it (user POV)",
        "## Driving it with verify-transcript",
        "## Gotchas",
    ]
    for area in verify_transcript.FEATURE_AREAS:
        page = feature_dir / f"{area}.md"
        text = page.read_text()
        assert [
            line for line in text.splitlines() if line.startswith("## ")
        ] == expected_headings
    for feature in verify_transcript.FEATURES:
        for area in feature.areas:
            assert f"`{feature.id}`" in (feature_dir / f"{area}.md").read_text()


def test_every_public_surface_is_in_the_interface_inventory():
    interface = (SCRIPT.parents[1] / "features" / "interface.md").read_text()

    for surface in verify_transcript.PUBLIC_SURFACES:
        assert f"`{surface.id}`" in interface
        for owner in surface.owners:
            assert f"`{owner}`" in interface
        if surface.exclusion_reason:
            assert surface.exclusion_reason in interface


def test_feature_map_searches_body_text():
    documents = verify_transcript.feature_documents(SCRIPT.parents[1], "deepgram")
    assert {document["id"] for document in documents} >= {
        "diagnostics",
        "youtube",
        "zoom",
    }


def test_feature_entries_return_exact_selectable_ids():
    entries = verify_transcript.feature_entries(SCRIPT.parents[1], None)

    assert {entry["id"] for entry in entries} == {
        feature.id for feature in verify_transcript.FEATURES
    }
    assert all(
        verify_transcript.select_features((entry["id"],), False, entry["paid"])[0].id
        == entry["id"]
        for entry in entries
    )
    assert all(entry["verify_command"].endswith(" --json") for entry in entries)

    interface = verify_transcript.feature_entries(SCRIPT.parents[1], "interface")
    assert {entry["id"] for entry in interface} == {
        "interface.help-version",
        "interface.structured-recovery",
    }

    deepgram = verify_transcript.feature_entries(SCRIPT.parents[1], "deepgram")
    assert deepgram
    assert "diagnostics.youtube" in {entry["id"] for entry in deepgram}
    assert "interface.help-version" not in {entry["id"] for entry in deepgram}
    assert all(
        entry["id"] in {feature.id for feature in verify_transcript.FEATURES}
        for entry in deepgram
    )


def test_features_command_exposes_selectable_ids(monkeypatch):
    reports = []
    monkeypatch.setattr(
        verify_transcript,
        "_print_json",
        lambda payload, **_kwargs: reports.append(payload),
    )

    code = verify_transcript.main(["features", "--json"])

    payload = reports[0]
    assert code == 0
    assert {entry["id"] for entry in payload["features"]} == {
        feature.id for feature in verify_transcript.FEATURES
    }
    assert {document["id"] for document in payload["documents"]} == set(
        verify_transcript.FEATURE_AREAS
    )


def test_default_features_cover_the_agent_boundary():
    defaults = {
        feature.id for feature in verify_transcript.select_features((), False, False)
    }

    assert {
        "interface.help-version",
        "interface.structured-recovery",
        "dry-runs.transcript-only",
    } <= defaults


def test_public_surfaces_have_one_owner_or_exclusion():
    feature_ids = {feature.id for feature in verify_transcript.FEATURES}
    surface_ids = [surface.id for surface in verify_transcript.PUBLIC_SURFACES]

    assert len(surface_ids) == len(set(surface_ids))
    for surface in verify_transcript.PUBLIC_SURFACES:
        assert bool(surface.owners) != bool(surface.exclusion_reason)
        assert set(surface.owners) <= feature_ids


def test_public_surface_inventory_matches_help_contracts():
    expected_commands = set().union(
        *(contract.choices for contract in verify_transcript.HELP_CONTRACTS)
    )
    expected_options = set().union(
        *(contract.options for contract in verify_transcript.HELP_CONTRACTS)
    )

    assert {
        surface.token
        for surface in verify_transcript.PUBLIC_SURFACES
        if surface.kind == "command"
    } == expected_commands
    assert {
        surface.token
        for surface in verify_transcript.PUBLIC_SURFACES
        if surface.kind == "option"
    } == expected_options


def test_response_contract_enforces_json_streams():
    success = verify_transcript.CapturedProcess(
        (), 0, '{"ok":true}\n', "", 0.1, False
    )
    failure = verify_transcript.CapturedProcess(
        (), 2, "", '{"ok":false}\n', 0.1, False
    )

    assert verify_transcript.parse_expected_output(
        success, verify_transcript.OutputExpectation("stdout-json", (0,))
    ) == {"ok": True}
    assert verify_transcript.parse_expected_output(
        failure, verify_transcript.OutputExpectation("stderr-json", (2,))
    ) == {"ok": False}
    with pytest.raises(AssertionError, match="stderr"):
        verify_transcript.parse_expected_output(
            failure, verify_transcript.OutputExpectation("stdout-json", (2,))
        )


def test_a_doctor_report_is_read_from_the_stream_its_exit_code_names():
    by_exit = verify_transcript.OutputExpectation("json-by-exit", (0, 1))
    ready = verify_transcript.CapturedProcess((), 0, '{"ok":true}\n', "", 0.1, False)
    unready = verify_transcript.CapturedProcess(
        (), 1, "", '{"ok":false}\n', 0.1, False
    )

    assert verify_transcript.parse_expected_output(ready, by_exit) == {"ok": True}
    assert verify_transcript.parse_expected_output(unready, by_exit) == {"ok": False}


def test_new_free_commands_remain_safe_and_confined(tmp_path: Path):
    context = make_context(tmp_path)
    feature_ids = {
        "interface.help-version",
        "interface.structured-recovery",
        "dry-runs.transcript-only",
    }
    try:
        for feature in verify_transcript.FEATURES:
            if feature.id not in feature_ids:
                continue
            plans = verify_transcript.build_commands(feature, context)
            assert plans
            for plan in plans:
                verify_transcript.assert_safe_command(feature, plan, context)
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


def test_command_guard_confines_output_and_paid_calls(tmp_path: Path):
    context = make_context(tmp_path)
    try:
        dry_feature = next(
            feature
            for feature in verify_transcript.FEATURES
            if feature.id == "youtube.dry-run-summary"
        )
        dry_plan = verify_transcript.build_commands(dry_feature, context)[0]
        verify_transcript.assert_safe_command(dry_feature, dry_plan, context)

        escaped = verify_transcript.CommandPlan(
            dry_plan.id,
            tuple(
                "/tmp/escaped" if value == str(dry_plan.output_dir) else value
                for value in dry_plan.args
            ),
            Path("/tmp/escaped"),
        )
        with pytest.raises(verify_transcript.VerificationError) as caught:
            verify_transcript.assert_safe_command(dry_feature, escaped, context)
        assert caught.value.code == "unsafe_output"

        paid_feature = next(
            feature
            for feature in verify_transcript.FEATURES
            if feature.id == "youtube.real-summary"
        )
        paid_plan = verify_transcript.build_commands(paid_feature, context)[0]
        with pytest.raises(verify_transcript.VerificationError) as caught:
            verify_transcript.assert_safe_command(paid_feature, paid_plan, context)
        assert caught.value.code == "paid_intent_required"
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


def test_process_helper_captures_streams_and_exit(tmp_path: Path):
    helper = tmp_path / "helper.py"
    helper.write_text(
        "import sys\nprint('public output')\nprint('useful error', file=sys.stderr)\nraise SystemExit(3)\n"
    )

    captured = verify_transcript.run_process(
        (sys.executable, str(helper)), tmp_path, timeout_seconds=10
    )

    assert captured.exit_code == 3
    assert captured.stdout == "public output\n"
    assert captured.stderr == "useful error\n"
    assert captured.timed_out is False


def test_doctor_validator_rejects_crossed_source():
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "diagnostics.youtube"
    )
    process = verify_transcript.CapturedProcess((), 0, "", "", 0.1, False)
    payload = {
        "ok": True,
        "command": "doctor",
        "source": "zoom",
        "summary": False,
        "checks": [
            {"name": "deepgram_credential", "status": "pass"},
            {"name": "zoom_recordings", "status": "pass"},
        ],
        "counts": {"pass": 2, "warn": 0, "fail": 0},
    }

    with pytest.raises(AssertionError, match="doctor source is invalid"):
        verify_transcript._validate_doctor(feature, process, payload)


def test_safe_cleanup_requires_current_marker(tmp_path: Path):
    scratch = verify_transcript.create_scratch("cleanup-test")
    (scratch / verify_transcript.RUN_MARKER).write_text("another-run\n")
    try:
        with pytest.raises(verify_transcript.VerificationError) as caught:
            verify_transcript.safe_cleanup(scratch, "cleanup-test")
        assert caught.value.code == "unsafe_cleanup"
        assert scratch.exists()
    finally:
        shutil.rmtree(scratch)

    removable = verify_transcript.create_scratch("cleanup-test")
    verify_transcript.safe_cleanup(removable, "cleanup-test")
    assert not removable.exists()


@pytest.mark.parametrize(
    "upload_line",
    [
        "Audio upload: complete (1024 bytes)",
        "",
        "Audio upload: complete (0 bytes)",
        "Audio upload: incomplete (512/1024 bytes)",
    ],
)
def test_e2e_validator_records_verified_upload_without_transcript_content(
    tmp_path: Path, upload_line: str
):
    context = make_context(tmp_path, allow_paid=True)
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "youtube.real-summary"
    )
    plan = verify_transcript.build_commands(feature, context)[0]
    assert plan.output_dir is not None
    published = plan.output_dir / "2026_09_01_fixture"
    published.mkdir(parents=True)
    artifact_paths = {
        "transcript": published / "raw_transcript.txt",
        "sentences": published / "raw_sentences.txt",
        "json": published / "raw_transcript.json",
        "metadata": published / "meta.txt",
        "summary": published / "short_summary.md",
    }
    artifact_paths["transcript"].write_text("Hello world\n")
    artifact_paths["sentences"].write_text("[00:00] Hello world\n")
    artifact_paths["json"].write_text(json.dumps([{"text": "Hello world"}]))
    artifact_paths["metadata"].write_text(f"Summary status: succeeded\n{upload_line}\n")
    artifact_paths["summary"].write_text("# Summary\n\nHello world\n")
    payload = {
        "ok": True,
        "source": "youtube",
        "output_dir": str(published),
        "summary": {"status": "succeeded"},
        "artifacts": {key: str(path) for key, path in artifact_paths.items()},
    }
    process = verify_transcript.CapturedProcess((), 0, "", "", 1.0, False)
    try:
        if upload_line != "Audio upload: complete (1024 bytes)":
            with pytest.raises(AssertionError, match="upload"):
                verify_transcript._validate_e2e(
                    feature, plan, process, payload, context
                )
            return
        observations = verify_transcript._validate_e2e(
            feature, plan, process, payload, context
        )

        manifest_path = Path(observations["artifact_manifest"])
        manifest_text = manifest_path.read_text()
        assert observations["artifact_count"] == 5
        assert "Hello world" not in manifest_text
        assert "sha256" in manifest_text
        assert observations["audio_upload"] == {"status": "complete", "bytes": 1024}
        assert json.loads(manifest_text)["audio_upload"] == observations["audio_upload"]
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


def test_dry_run_validator_requires_no_output(tmp_path: Path):
    context = make_context(tmp_path)
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "zoom.dry-run"
    )
    plan = verify_transcript.build_commands(feature, context)[0]
    assert plan.output_dir is not None
    meeting = Path(plan.args[plan.args.index("--path") + 1])
    payload = {
        "ok": True,
        "command": "run",
        "dry_run": True,
        "source": {
            "kind": "zoom",
            "path": str(meeting),
            "audio": str(meeting / "audio_only.m4a"),
        },
        "summary": {
            "enabled": True,
            "profile": "opus",
            "provider": "claude",
            "model": "claude-opus-5-5",
            "effort": "high",
            "prompt": "synthese-rencontre",
        },
        "output_dir": str(plan.output_dir),
        "timeout_seconds": 570.0,
        "side_effects": [],
    }
    process = verify_transcript.CapturedProcess((), 0, "", "", 0.1, False)
    try:
        observations = verify_transcript._validate_dry_run(
            feature, plan, process, payload
        )
        assert observations["side_effects"] == []
        assert not plan.output_dir.exists()
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)
