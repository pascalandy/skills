"""Run records, the exact cache, replay, explain, and failures that must not publish a verdict."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jevtest import Project, add_sub


def test_exact_request_cache(project: Project) -> None:
    project.set_pr(
        3, "Add sub to the calculator", "- Adds a sub function with a test\n"
    )
    add_sub(project)
    fake = project.fake
    first = project.run_merge()
    assert first.code == 0, first
    sent = len(fake.requests)
    assert first.json["usage"]["requests"] == sent == 2
    assert (
        first.json["usage"]["cached"] == 0 and first.json["usage"]["input_tokens"] > 0
    )

    project.git("checkout", "-q", "main")
    project.commit("Tidy the readme", {"README.md": "# Calc\n"})
    project.git("checkout", "-q", "feature")
    second = project.run_merge("--base", "main")
    assert second.code == 0, second
    assert second.json["judged"]["base"] != first.json["judged"]["base"]
    assert len(fake.requests) == sent
    usage = second.json["usage"]
    assert (
        usage["cached"] == 2 and usage["input_tokens"] == 0 and usage["cost_usd"] == 0
    )
    assert usage["cached_input_tokens"] == first.json["usage"]["input_tokens"]

    fresh = project.run_merge("--no-cache")
    assert len(fake.requests) == 2 * sent and fresh.json["usage"]["cached"] == 0
    other_model = project.run_merge("--model", "jev-1.14.0")
    assert len(fake.requests) == 3 * sent
    assert other_model.json["model"] == {
        "requested": "jev-1.14.0",
        "answered": "jev-1.14.0",
    }
    assert {body["model"] for body in fake.requests[-sent:]} == {"jev-1.14.0"}

    project.edit(
        ".jev/packs/merge.toml",
        "make an existing test less able to catch a regression?",
        "make an existing test less able to catch a regression in this module?",
    )
    changed = project.run_merge()
    assert changed.code == 0, changed
    assert (
        changed.json["usage"]["cached"] == 1 and changed.json["usage"]["requests"] == 2
    )
    assert [body["state"].get("group", "pr") for body in fake.requests[3 * sent :]] == [
        "src"
    ]


def test_replay_uses_saved_policy(tmp_path: Path, project: Project) -> None:
    add_sub(project)
    project.fake.answer("test_weakened", 0.5)
    original = project.run_merge()
    assert original.code == 10, original
    run_id = original.json["run_id"]
    record = project.root / original.json["record"]
    saved = record.read_bytes()
    sent = len(project.fake.requests)

    (project.jev_dir / "packs" / "merge.toml").unlink()
    (project.jev_dir / "gates" / "merge.toml").write_text("this is not toml = [\n")
    replayed = project.jev("replay", run_id, "--json", key=False)
    assert replayed.code == 10, replayed
    assert replayed.json["replay"] == {
        "of": run_id,
        "original_verdict": "escalate",
        "policy": None,
        "matches": True,
        "source": f".jev/runs/{run_id}.json",
    }
    assert replayed.json["answers"] == original.json["answers"]
    assert replayed.json["reasons"] == original.json["reasons"]

    policy = tmp_path / "bands.toml"
    policy.write_text("[bands.test_weakened]\nfavorable = 0.6\nadverse = 0.9\n")
    relaxed = project.jev(
        "replay", run_id, "--policy", str(policy), "--json", key=False
    )
    assert relaxed.code == 0, relaxed
    assert (
        relaxed.json["replay"]["matches"] is False and relaxed.json["verdict"] == "pass"
    )
    assert record.read_bytes() == saved

    refused = {
        "[questions]\nid = 'extra'\n": "may only override bands",
        'model = "jev-2.0.0"\n': "may only override bands",
        '[bands.test_weakened]\ndirection = "yes_is_good"\n': "cannot change the direction",
        "[bands.no_such_question]\nadverse = 0.5\n": "no question 'no_such_question'",
        "[bands.test_weakened]\nfavorable = 0.9\nadverse = 0.1\n": "yes_is_bad needs favorable <= adverse",
    }
    for text, expected in refused.items():
        policy.write_text(text)
        result = project.jev("replay", run_id, "--policy", str(policy), key=False)
        assert result.code == 1, (text, result)
        assert expected in result.stderr, (text, result.stderr)
    assert record.read_bytes() == saved
    assert len(project.fake.requests) == sent

    human = project.jev("replay", run_id, key=False)
    assert human.stdout.startswith(f"replay of {run_id} (recorded verdict escalate)")


def test_explain_exposes_inputs(project: Project) -> None:
    add_sub(project)
    project.commit("Pin dependencies", {"uv.lock": "version = 1\n"})
    result = project.run_merge()
    run_id = result.json["run_id"]
    explained = project.jev("explain", run_id, "--json", key=False)
    assert explained.code == 0, explained
    detail = json.loads((project.root / explained.json["file"]).read_text())
    assert set(detail["state"]) == {"pr", "group:src"}
    assert (
        detail["state"]["group:src"]["files"][0]["hunks"][0]["id"] == "src/calc.py@@1"
    )
    assert detail["answers"]["group:src"]["answers"]["behavior_tested"]["noul"] == 0.93
    assert explained.json["summary"]["omitted"] == [
        {"path": "uv.lock", "old_path": None, "why": "lock file"}
    ]
    assert explained.json["summary"]["reasons"] == result.json["reasons"]
    human = project.jev("explain", "last", key=False)
    assert f"run {run_id}  gate merge  verdict escalate (advisory)" in human.stdout
    assert "omitted: uv.lock (lock file)" in human.stdout
    assert (
        f"full state, requests, and answers: .jev/runs/explain/{run_id}.json"
        in human.stdout
    )


def test_record_failure(project: Project) -> None:
    add_sub(project)
    fake = project.fake
    runs = project.jev_dir / "runs"
    runs.write_text("not a directory\n")
    blocked = project.run_merge()
    assert blocked.code == 1, blocked
    assert blocked.json["error"]["kind"] == "internal"
    assert "verdict" not in blocked.json and blocked.stdout.count("\n") == 1
    runs.unlink()

    def drop_one(
        body: dict[str, Any], response: dict[str, Any]
    ) -> tuple[int, Any, dict[str, str]]:
        answers = dict(list(response["answers"].items())[:-1])
        return 200, {**response, "answers": answers}, {}

    def bad_probability(
        body: dict[str, Any], response: dict[str, Any]
    ) -> tuple[int, Any, dict[str, str]]:
        key = next(
            key
            for key, answer in response["answers"].items()
            if answer["type"] == "noul"
        )
        response["answers"][key]["noul"] = 1.7
        return 200, response, {}

    for hook, expected in (
        (drop_one, "answer IDs do not match"),
        (bad_probability, "noul is not a probability"),
    ):
        fake.hooks[:] = [hook]
        result = project.run_merge("--no-cache")
        assert result.code == 1, result
        assert (
            result.json["error"]["kind"] == "service"
            and expected in result.json["error"]["message"]
        )
        assert "verdict" not in result.json
        record = json.loads((project.root / result.json["error"]["record"]).read_text())
        assert record["verdict"] is None and record["error"]["kind"] == "service"
    fake.hooks.clear()

    fake.answered_model = "jev-1.14.0"
    mismatch = project.run_merge("--no-cache")
    assert (
        mismatch.code == 1
        and "answered by 'jev-1.14.0', requested 'jev-1.13.0'"
        in mismatch.json["error"]["message"]
    )
    fake.answered_model = None

    calls = {"count": 0}

    def second_fails(
        body: dict[str, Any], response: dict[str, Any]
    ) -> tuple[int, Any, dict[str, str]] | None:
        calls["count"] += 1
        return (500, {"error": "boom"}, {}) if calls["count"] == 2 else None

    fake.hooks[:] = [second_fails]
    partial = project.run_merge("--no-cache")
    assert partial.code == 1, partial
    assert partial.json["error"]["kind"] == "service"
    record = json.loads((project.root / partial.json["error"]["record"]).read_text())
    assert record["verdict"] is None and list(record["responses"]) == ["pr"]
    assert record["usage"]["requests"] == 1
    fake.hooks.clear()
    resumed = project.run_merge()
    assert resumed.code == 0, resumed
    assert resumed.json["usage"]["cached"] == 1
