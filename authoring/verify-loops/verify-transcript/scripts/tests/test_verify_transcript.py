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

    selected = verify_transcript.select_features(("youtube.real-summary",), False, True)
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
    assert all(
        entry["verify_command"].startswith("verify-transcript verify --feature ")
        for entry in entries
    )

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


def test_features_command_exposes_selectable_ids(capsys):
    code = verify_transcript.main(["features"])

    out, err = capsys.readouterr()
    payload = json.loads(out)
    assert (code, err, out.count("\n")) == (0, "", 1)
    assert payload["ok"] is True
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


ANSWER = verify_transcript.OutputExpectation("answer", (0,))


def captured(code: int, stdout: str = "", stderr: str = ""):
    return verify_transcript.CapturedProcess((), code, stdout, stderr, 0.1, False)


def test_an_answer_is_one_json_line_on_the_stream_its_exit_code_names():
    by_exit = verify_transcript.OutputExpectation("answer", (0, 1))
    failure = '{"ok":false,"errors":["boom; fix: run this"]}\n'

    assert verify_transcript.parse_expected_output(
        captured(0, '{"ok":true}\n'), by_exit
    ) == {"ok": True}
    assert verify_transcript.parse_expected_output(
        captured(1, stderr=f"/tmp/result\n{failure}"), by_exit
    ) == {"ok": False, "errors": ["boom; fix: run this"]}


@pytest.mark.parametrize(
    ("process", "expectation", "verdict"),
    [
        (captured(0, '{"ok":true}\n', "note\n"), ANSWER, "wrote to stderr"),
        (
            captured(0, '{"ok":true}\n{"ok":true}\n'),
            ANSWER,
            "stdout is not one JSON line",
        ),
        (captured(0, '{"ok":false}\n'), ANSWER, "ok disagrees with the exit code"),
        (
            captured(1, '{"ok":true}\n', '{"ok":false}\n'),
            verify_transcript.OutputExpectation("answer", (1,)),
            "a failed command wrote to stdout",
        ),
        (captured(0, "help text\n"), ANSWER, "invalid JSON on stdout"),
    ],
    ids=["stderr-on-success", "two-lines", "ok-disagrees", "stdout-on-failure", "text"],
)
def test_an_answer_that_breaks_the_rule_fails(process, expectation, verdict):
    with pytest.raises(AssertionError, match=verdict):
        verify_transcript.parse_expected_output(process, expectation)


def test_a_real_run_may_stream_its_folder_on_stderr_before_it_answers():
    events = verify_transcript.OutputExpectation("answer", (0,), events=True)

    assert verify_transcript.parse_expected_output(
        captured(0, '{"ok":true,"files":[]}\n', "/tmp/result\n"), events
    ) == {"ok": True, "files": []}


@pytest.mark.parametrize(
    ("stderr", "verdict"),
    [
        (
            (
                "/tmp/result\n"
                '{"ok":false,"errors":["yt-dlp failed: HTTP Error 403: Forbidden; '
                'fix: transcript doctor --source youtube"]}\n'
            ),
            (
                "transcript exited 1; expected (0,): yt-dlp failed: HTTP Error 403: "
                "Forbidden; fix: transcript doctor --source youtube"
            ),
        ),
        ("Traceback (most recent call last):\n", "transcript exited 1; expected (0,)"),
        ("", "transcript exited 1; expected (0,)"),
        ('{"ok":false,"errors":[3]}\n', "transcript exited 1; expected (0,)"),
    ],
)
def test_a_wrong_exit_code_names_the_error_transcript_reported(stderr, verdict):
    with pytest.raises(AssertionError) as raised:
        verify_transcript.parse_expected_output(captured(1, stderr=stderr), ANSWER)

    assert str(raised.value) == verdict


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


def test_profile_discovery_accepts_new_profiles_but_rejects_duplicate_names(tmp_path):
    context = make_context(tmp_path)
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "configuration.profiles"
    )
    payload = {
        "default": "opus",
        "profiles": [
            {"name": name, "provider": "claude", "model": "a-model", "effort": "medium"}
            for name in ("opus", "sonnet", "new-profile")
        ],
    }
    process = verify_transcript.CapturedProcess((), 0, "", "", 0.1, False)
    try:
        assert verify_transcript.validate_feature(
            feature, (), ((process, payload),), context
        ) == {"default": "opus", "profiles": ["opus", "sonnet", "new-profile"]}

        payload["profiles"].append(payload["profiles"][-1])
        with pytest.raises(AssertionError, match="duplicate profile names"):
            verify_transcript.validate_feature(
                feature, (), ((process, payload),), context
            )
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


def test_doctor_validator_rejects_crossed_source():
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "diagnostics.youtube"
    )
    unready = captured(1)
    payload = {
        "ok": False,
        "errors": [
            "deepgram_credential: Missing Deepgram API key; fix: chezmoi secret",
            "zoom_recordings: no Zoom folder; fix: record a meeting",
        ],
    }

    with pytest.raises(AssertionError, match="doctor source is invalid"):
        verify_transcript._validate_doctor(feature, unready, payload)


def test_doctor_validator_reads_readiness_from_the_answer():
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "diagnostics.zoom"
    )
    failure = {
        "ok": False,
        "errors": ["zoom_recordings: no Zoom folder; fix: record a meeting"],
    }

    assert verify_transcript._validate_doctor(feature, captured(0), {"ok": True}) == {
        "readiness_ok": True,
        "failed_checks": [],
    }
    assert verify_transcript._validate_doctor(feature, captured(1), failure) == {
        "readiness_ok": False,
        "failed_checks": ["zoom_recordings"],
    }
    with pytest.raises(AssertionError, match="names no fix"):
        verify_transcript._validate_doctor(
            feature, captured(1), {"ok": False, "errors": ["zoom_recordings: x"]}
        )


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


def published_run(
    plan, metadata: str
) -> tuple[dict, verify_transcript.CapturedProcess]:
    """A real run's saved files under `plan`'s output, its answer, and the
    process that streamed its folder."""
    published = plan.output_dir / "2026_09_01_fixture"
    published.mkdir(parents=True)
    files = {
        "meta.txt": metadata,
        "raw_transcript.txt": "Hello world\n",
        "raw_sentences.txt": "[00:00] Hello world\n",
        "raw_transcript.json": json.dumps([{"text": "Hello world"}]),
        "short_summary.md": "# Summary\n\nHello world\n",
    }
    for name, content in files.items():
        (published / name).write_text(content)
    payload = {"ok": True, "files": [str(published / name) for name in files]}
    return payload, captured(0, stderr=f"{published}\n")


def real_summary(context):
    feature = next(
        feature
        for feature in verify_transcript.FEATURES
        if feature.id == "youtube.real-summary"
    )
    return feature, verify_transcript.build_commands(feature, context)[0]


def metadata(*, upload: str, model: str = "claude-sonnet-5-5") -> str:
    url = verify_transcript.CANONICAL_YOUTUBE_URL
    return (
        f"Source: {url}\nSummary status: succeeded\n"
        f"Claude: {model} (reasoning: medium)\n{upload}\n"
    )


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
    feature, plan = real_summary(context)
    payload, process = published_run(plan, metadata(upload=upload_line))
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


def test_the_paid_run_summarizes_with_the_sonnet_profile(tmp_path: Path):
    context = make_context(tmp_path, allow_paid=True)
    feature, plan = real_summary(context)
    upload = "Audio upload: complete (1024 bytes)"
    payload, process = published_run(
        plan, metadata(upload=upload, model="claude-opus-5-5")
    )

    try:
        assert plan.args[plan.args.index("--profile") + 1] == "sonnet"
        with pytest.raises(AssertionError, match="sonnet test profile"):
            verify_transcript._validate_e2e(feature, plan, process, payload, context)
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


@pytest.mark.parametrize(
    ("change", "verdict"),
    [
        ("drop-summary", "file set is incomplete"),
        ("no-stream", "did not stream its result folder"),
    ],
)
def test_the_paid_run_answers_every_file_and_streams_its_folder(
    tmp_path: Path, change: str, verdict: str
):
    context = make_context(tmp_path, allow_paid=True)
    feature, plan = real_summary(context)
    upload = "Audio upload: complete (1024 bytes)"
    payload, process = published_run(plan, metadata(upload=upload))
    if change == "drop-summary":
        payload["files"].pop()
    else:
        process = captured(0)

    try:
        with pytest.raises(AssertionError, match=verdict):
            verify_transcript._validate_e2e(feature, plan, process, payload, context)
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
    }
    process = verify_transcript.CapturedProcess((), 0, "", "", 0.1, False)
    try:
        observations = verify_transcript._validate_dry_run(
            feature, plan, process, payload
        )
        assert observations == {
            "source": payload["source"],
            "summary": payload["summary"],
        }
        assert not plan.output_dir.exists()
    finally:
        verify_transcript.safe_cleanup(context.scratch_dir, context.run_id)


@pytest.mark.parametrize(
    ("argv", "code", "answer"),
    [
        (["doctor"], 0, {"ok": True}),
        (
            ["features", "no page says this"],
            1,
            {
                "ok": False,
                "errors": [
                    (
                        "no feature or Feature Map page matches 'no page says this'; "
                        "run 'verify-transcript features' to list them all"
                    )
                ],
            },
        ),
        (
            ["verify", "--feature", "bogus"],
            2,
            {
                "ok": False,
                "errors": [
                    (
                        "Unknown feature ID: bogus; run 'verify-transcript features' "
                        "and use one of features[].id"
                    )
                ],
                "help": "verify-transcript --help",
            },
        ),
        (
            ["verify", "--json"],
            2,
            {
                "ok": False,
                "errors": ["unrecognized arguments: --json"],
                "help": "verify-transcript verify --help",
            },
        ),
    ],
    ids=["doctor", "no-match", "unknown-feature", "json-is-the-default"],
)
def test_each_command_answers_in_one_json_line(argv, code, answer, capsys):
    assert verify_transcript.main(argv) == code

    out, err = capsys.readouterr()
    assert json.loads(out if code == 0 else err) == answer
    assert (out if code else err) == ""


def test_a_command_prints_its_own_help(capsys):
    assert verify_transcript.main(["verify", "--help"]) == 0

    assert capsys.readouterr().out.startswith("usage: verify-transcript verify ")
