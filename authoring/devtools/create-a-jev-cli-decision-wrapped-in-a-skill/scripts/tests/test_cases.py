"""Labels, admission, and portable cases.

Planted secrets are assembled at runtime so no token-shaped literal is committed.
"""

from __future__ import annotations

import json
import random
import shutil
import string
from pathlib import Path

from jevtest import Project, Result, add_sub

TOKEN = "ghp_" + "".join(
    random.Random(3).choices(string.ascii_letters + string.digits, k=36)
)


def label(
    project: Project,
    run: str,
    scope: str,
    outcome: str,
    by: str,
    evidence: str,
    *extra: str,
) -> Result:
    return project.jev(
        "label",
        run,
        "--scope",
        scope,
        "--outcome",
        outcome,
        "--by",
        by,
        "--evidence",
        evidence,
        "--json",
        *extra,
        key=False,
    )


def test_portable_case_replay(tmp_path: Path, project: Project) -> None:
    project.privacy(commit_cases=True)
    add_sub(project)
    project.fake.answer("risk_deploy_config", 0.97, group="src")
    run = project.run_merge()
    assert run.code == 10, run
    run_id = run.json["run_id"]
    admitted = label(
        project,
        run_id,
        "gate",
        "unknown",
        "reproduced",
        "setup proof; semantic outcome not reviewed",
        "--admit",
    )
    assert admitted.code == 0, admitted
    assert admitted.json["admitted"] == f".jev/cases/{run_id}"
    case = project.jev_dir / "cases" / run_id
    assert (case / "record.json").read_bytes() == (
        project.root / run.json["record"]
    ).read_bytes()
    project.commit("Admit the setup case")
    assert project.git("ls-files", f".jev/cases/{run_id}").splitlines() == [
        f".jev/cases/{run_id}/labels.toml",
        f".jev/cases/{run_id}/record.json",
    ]

    fresh = project.clone(tmp_path / "fresh")
    assert (
        not (fresh.jev_dir / "runs").exists() and not (fresh.jev_dir / "cache").exists()
    )
    sent = len(project.fake.requests)
    replay = fresh.jev("replay", run_id, "--json", key=False)
    assert replay.code == 10, replay
    assert replay.json["replay"]["matches"] is True
    assert replay.json["replay"]["source"] == f".jev/cases/{run_id}/record.json"
    assert (
        replay.json["answers"] == run.json["answers"]
        and replay.json["reasons"] == run.json["reasons"]
    )
    assert [
        (item["scope"], item["outcome"], item["by"]) for item in replay.json["labels"]
    ] == [("gate", "unknown", "reproduced")]
    assert len(project.fake.requests) == sent and project.fake.model_requests == 0
    assert (
        not (fresh.jev_dir / "runs").exists()
        and fresh.git("status", "--porcelain") == ""
    )


def test_case_admission(tmp_path: Path, project: Project) -> None:
    project.privacy(commit_cases=True)
    add_sub(project)
    project.commit("Plan notes", {"notes/plan.md": "# Plan\n\nShip sub.\n"})
    run = project.run_merge()
    assert run.code == 0, run
    run_id = run.json["run_id"]
    cases = project.jev_dir / "cases"

    project.edit_config("deny_globs = []", 'deny_globs = ["notes/**"]')
    denied = label(project, run_id, "gate", "good", "human", "reviewed", "--admit")
    assert denied.code == 1 and denied.json["error"]["kind"] == "permission", denied
    assert (
        "group:notes holds notes/plan.md, which deny glob notes/** now covers"
        in denied.json["error"]["problems"]
    )
    assert not cases.exists()
    assert (
        len(
            json.loads(
                label(project, run_id, "gate", "good", "human", "reviewed again").stdout
            )["labels"]
        )
        == 2
    )

    project.edit_config('deny_globs = ["notes/**"]', "deny_globs = []")
    project.edit(".gitignore", "local/\n", "local/\nnotes/\n")
    ignored = label(project, run_id, "gate", "good", "human", "reviewed", "--admit")
    assert ignored.code == 1 and "which git now ignores" in ignored.stderr
    project.edit(".gitignore", "local/\nnotes/\n", "local/\n")

    secret_label = label(
        project, run_id, "gate", "good", "human", f"token was {TOKEN}", "--admit"
    )
    assert secret_label.code == 1 and secret_label.json["error"]["kind"] == "permission"
    assert TOKEN not in secret_label.stdout + secret_label.stderr
    labels_file = project.jev_dir / "runs" / f"{run_id}.labels.toml"
    assert TOKEN not in labels_file.read_text()
    original_labels = labels_file.read_text()
    labels_file.write_text(
        original_labels.replace(
            'evidence = "reviewed again"', f'evidence = "reviewed again {TOKEN}"'
        )
    )
    tampered_label = label(
        project, run_id, "gate", "good", "human", "reviewed", "--admit"
    )
    assert (
        tampered_label.code == 1
        and "evidence" in tampered_label.json["error"]["problems"][0]
    )
    labels_file.write_text(original_labels)

    record_path = project.root / run.json["record"]
    original = record_path.read_bytes()
    record = json.loads(original)
    record["plan"]["requests"][0]["body"]["state"]["claims"]["c1"] += f" {TOKEN}"
    record_path.write_text(json.dumps(record))
    tampered_payload = label(
        project, run_id, "gate", "good", "human", "reviewed", "--admit"
    )
    assert tampered_payload.code == 1 and "possible secret" in tampered_payload.stderr
    assert TOKEN not in tampered_payload.stdout + tampered_payload.stderr
    del record["responses"]["group:src"]
    record["plan"]["requests"][0]["body"]["state"]["claims"]["c1"] = (
        "Add sub to the calculator"
    )
    record_path.write_text(json.dumps(record))
    missing = label(project, run_id, "gate", "good", "human", "reviewed", "--admit")
    assert missing.code == 1 and missing.json["error"]["kind"] == "config"
    assert "no stored answers for group:src" in missing.stderr
    record_path.write_bytes(original)
    assert not cases.exists()

    first = label(
        project, run_id, "gate", "bad", "human", "first admitted review", "--admit"
    )
    assert first.code == 0, first
    case_record = cases / run_id / "record.json"
    stored = case_record.read_bytes()
    assert stored == original
    second = label(
        project, run_id, "gate", "good", "human", "second admitted review", "--admit"
    )
    assert second.code == 0, second
    assert case_record.read_bytes() == stored
    history = second.json["labels"]
    assert [item["evidence"] for item in history] == [
        "reviewed",
        "reviewed again",
        "reviewed",
        "reviewed",
        "reviewed",
        "first admitted review",
        "second admitted review",
    ]
    assert all(
        item["supersedes"] == previous["id"]
        for previous, item in zip(history, history[1:])
    )
    case_labels = (cases / run_id / "labels.toml").read_text()
    assert (
        "first admitted review" in case_labels
        and "second admitted review" in case_labels
    )
    case_record.write_bytes(stored.replace(b'"advisory": true', b'"advisory": false'))
    changed = label(project, run_id, "gate", "good", "human", "third", "--admit")
    assert changed.code == 1 and "admitted cases never change" in changed.stderr
    case_record.write_bytes(stored)
    project.commit("Commit the admitted case")

    project.fake.hooks.append(lambda body, response: (500, {"error": "boom"}, {}))
    failed = project.run_merge("--no-cache")
    assert failed.code == 1
    error_run = (
        failed.json["error"]["record"].removeprefix(".jev/runs/").removesuffix(".json")
    )
    no_verdict = label(
        project, error_run, "gate", "bad", "human", "service failed", "--admit"
    )
    assert no_verdict.code == 1 and "has no verdict to label" in no_verdict.stderr
    project.fake.hooks.clear()

    project.commit("Read the token", {"src/settings.py": f'TOKEN = "{TOKEN}"\n'})
    blocked = project.run_merge()
    assert blocked.code == 11
    redacted = label(
        project,
        blocked.json["run_id"],
        "gate",
        "bad",
        "human",
        "secret found",
        "--admit",
    )
    assert redacted.code == 1 and "redacted after a secret hit" in redacted.stderr


def test_local_cases(tmp_path: Path, project: Project) -> None:
    project.privacy(commit_cases=False)
    add_sub(project)
    run = project.run_merge()
    run_id = run.json["run_id"]
    unguarded = label(
        project, run_id, "gate", "unknown", "reproduced", "local proof", "--admit"
    )
    assert unguarded.code == 1 and "does not ignore .jev/cases/" in unguarded.stderr
    assert not (project.jev_dir / "cases").exists()

    project.edit(".jev/.gitignore", "cache/\n", "cache/\ncases/\n")
    admitted = label(
        project, run_id, "gate", "unknown", "reproduced", "local proof", "--admit"
    )
    assert admitted.code == 0, admitted
    record = f".jev/cases/{run_id}/record.json"
    assert project.git("check-ignore", record) == record
    assert project.git("status", "--porcelain") == ""
    shutil.rmtree(project.jev_dir / "runs")
    shutil.rmtree(project.jev_dir / "cache")
    replay = project.jev("replay", run_id, "--json", key=False)
    assert replay.code == 0 and replay.json["replay"]["source"] == record
    fresh = project.clone(tmp_path / "elsewhere")
    assert not (fresh.jev_dir / "cases").exists()
    assert fresh.jev("replay", run_id, key=False).code == 1


def test_label_history(tmp_path: Path, project: Project) -> None:
    project.privacy(commit_cases=True)
    add_sub(project)
    project.fake.answer("test_weakened", 0.5)
    run = project.run_merge()
    assert run.code == 10, run
    run_id = run.json["run_id"]
    review = tmp_path / "review.md"
    review.write_text(
        "Reran the suite on the captured commit; the weakened assertion still catches the bug.\n"
    )

    first = label(
        project,
        "last",
        "gate",
        "bad",
        "human",
        "missing edge case for negative numbers",
    )
    assert first.code == 0, first
    second = label(project, run_id, "gate", "good", "human", str(review))
    assert second.json["label"]["supersedes"] == first.json["label"]["id"]
    assert (
        second.json["label"]["evidence_file"] == "review.md"
        and second.json["label"]["evidence"] == review.read_text()
    )
    third = label(
        project,
        run_id,
        "question:test_weakened@src",
        "good",
        "reproduced",
        "old test still fails on the bug",
    )
    assert third.json["label"]["supersedes"] is None
    assert (
        "not whether Jev agreed" in third.json["label"]["assesses"]
        and "not whether Jev agreed" in first.json["label"]["assesses"]
    )
    fourth = label(
        project,
        run_id,
        "question:claim_supported@c1",
        "unknown",
        "model",
        "no later fix; outcome not known",
    )
    assert fourth.code == 0, fourth

    for scope in (
        "question:nope",
        "question:test_weakened@docs",
        "stage",
        "question:claim_supported@c9",
    ):
        assert label(project, run_id, scope, "good", "human", "x").code == 2, scope
    assert (
        project.jev(
            "label",
            run_id,
            "--scope",
            "gate",
            "--outcome",
            "correct",
            "--by",
            "human",
            "--evidence",
            "x",
        ).code
        == 2
    )

    final = label(
        project,
        run_id,
        "gate",
        "good",
        "human",
        "final review after the fix landed",
        "--admit",
    )
    assert final.code == 0, final
    assert final.json["label"]["supersedes"] == second.json["label"]["id"]
    expected = [
        ("gate", "bad", "human", None),
        ("gate", "good", "human", first.json["label"]["id"]),
        ("question:test_weakened@src", "good", "reproduced", None),
        ("question:claim_supported@c1", "unknown", "model", None),
        ("gate", "good", "human", second.json["label"]["id"]),
    ]
    shape = [
        (item["scope"], item["outcome"], item["by"], item.get("supersedes"))
        for item in final.json["labels"]
    ]
    assert shape == expected

    project.commit("Admit the reviewed case")
    fresh = project.clone(tmp_path / "fresh")
    replay = fresh.jev("replay", run_id, "--json", key=False)
    assert replay.code == 10, replay
    assert [
        (item["scope"], item["outcome"], item["by"], item.get("supersedes"))
        for item in replay.json["labels"]
    ] == expected
    assert replay.json["labels"][1]["evidence"] == review.read_text()
    explained = fresh.jev("explain", run_id, key=False)
    assert (
        "label "
        + second.json["label"]["id"]
        + ": gate good by human, supersedes "
        + first.json["label"]["id"]
        in explained.stdout
    )


def test_records_read_by_schema_version(project: Project) -> None:
    add_sub(project)
    run = project.run_merge()
    run_id = run.json["run_id"]
    assert (
        label(project, run_id, "gate", "unknown", "reproduced", "schema probe").code
        == 0
    )
    record_path = project.root / run.json["record"]
    record = json.loads(record_path.read_text())
    assert record["schema"] == "jevgate.run/v1"
    record_path.write_text(json.dumps({**record, "schema": "jevgate.run/v9"}))
    future = project.jev("replay", run_id, key=False)
    assert future.code == 1
    assert (
        "uses schema 'jevgate.run/v9', which this engine cannot read" in future.stderr
    )
    record_path.write_text(json.dumps(record))
    labels = project.jev_dir / "runs" / f"{run_id}.labels.toml"
    assert labels.read_text().startswith('schema = "jevgate.labels/v1"')
    labels.write_text(
        labels.read_text().replace("jevgate.labels/v1", "jevgate.labels/v9")
    )
    assert (
        "which this engine cannot read"
        in project.jev("replay", run_id, key=False).stderr
    )
