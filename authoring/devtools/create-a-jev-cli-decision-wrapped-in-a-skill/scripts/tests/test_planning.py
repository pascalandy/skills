"""Pack validation and request planning: budgets, citation capacity, and the request cap."""

from __future__ import annotations

from pathlib import Path

from jevtest import FakeTypeSafe, Project, add_sub, make_project

EXTRA = """
[[questions]]
id = "extra"
primitive = "{primitive}"
scope = "group"
role = "{role}"
applies_when = "{predicate}"
instruction = "{instruction}"
band = {{ direction = "{direction}", favorable = {favorable}, adverse = {adverse} }}
{more}
"""


def with_extra(project: Project, original: str, **fields: str) -> None:
    values = {
        "primitive": "noul",
        "role": "check",
        "predicate": "always",
        "instruction": "Is `files` tidy?",
        "direction": "yes_is_good",
        "favorable": "0.80",
        "adverse": "0.20",
        "more": "",
    }
    values.update(fields)
    pack = project.jev_dir / "packs" / "merge.toml"
    pack.write_text(original + EXTRA.format(**values))


def test_pack_validation(project: Project) -> None:
    shipped = project.jev("gates", "--check", key=False)
    assert shipped.code == 0, shipped
    assert shipped.stdout.strip().endswith("gates --check: ok, 1 gate, 14 questions")
    original = (project.jev_dir / "packs" / "merge.toml").read_text()

    structural = {
        "unknown predicate": (
            {"predicate": "group_is_large"},
            "unknown applies_when predicate 'group_is_large'",
        ),
        "unknown role": ({"role": "verdict"}, "unknown role 'verdict'"),
        "declared citation": ({"role": "citation"}, "citation questions are generated"),
        "incompatible primitive and role": (
            {
                "role": "risk",
                "more": 'area = "other"',
                "direction": "yes_is_bad",
                "favorable": "0.5",
                "adverse": "0.5",
                "primitive": "score",
            },
            "role risk cannot use primitive score",
        ),
        "unknown direction": (
            {"direction": "up"},
            "band direction must be yes_is_good or yes_is_bad",
        ),
        "threshold out of range": (
            {"favorable": "1.5"},
            "band favorable must be a threshold between 0 and 1",
        ),
        "thresholds reversed": (
            {"favorable": "0.20", "adverse": "0.80"},
            "yes_is_good needs favorable >= adverse",
        ),
    }
    for name, (fields, expected) in structural.items():
        with_extra(project, original, **fields)
        checked = project.jev("gates", "--check", key=False)
        assert checked.code == 1, (name, checked)
        assert expected in checked.stderr, (name, checked.stderr)
        listed = project.jev("gates", key=False)
        assert listed.code == 1, name
        run = project.jev("run", "merge", "--dry-run", key=False)
        assert run.code == 1 and "is invalid" in run.stderr, (name, run)

    checklist = {
        "unknown state path": (
            {"instruction": "Is `diff_text` tidy?"},
            "`diff_text` names no group state field",
        ),
        "unknown nested field": (
            {"instruction": "Is `files[0].lines` tidy?"},
            "`files[0].lines` has no field 'lines'",
        ),
        "author path in a group question": (
            {"instruction": "Is `author_text.body` polite?"},
            "`author_text.body` names no group state field",
        ),
        "choice without a no-match option": (
            {
                "primitive": "choice",
                "more": 'options = { tidy = "tidy", messy = "messy" }\nyes_options = ["tidy"]',
            },
            "a Choice needs a no-match option",
        ),
        "score with one level": (
            {"primitive": "score", "more": 'levels = ["only"]'},
            "a Score needs 2 to 10 levels, found 1",
        ),
        "score with eleven levels": (
            {
                "primitive": "score",
                "more": "levels = ["
                + ", ".join(f'"level {n}"' for n in range(11))
                + "]",
            },
            "a Score needs 2 to 10 levels, found 11",
        ),
    }
    for name, (fields, expected) in checklist.items():
        with_extra(project, original, **fields)
        checked = project.jev("gates", "--check", key=False)
        assert checked.code == 1, (name, checked)
        assert expected in checked.stderr, (name, checked.stderr)
        assert project.jev("gates", key=False).code == 0, (
            f"{name} is a checklist finding, not a load error"
        )

    with_extra(
        project,
        original,
        primitive="choice",
        more='options = { tidy = "tidy", none = "neither" }\nyes_options = ["tidy"]',
    )
    assert project.jev("gates", "--check", key=False).code == 0


def test_request_limits_and_coverage(tmp_path: Path, fake: FakeTypeSafe) -> None:
    capped = make_project(tmp_path / "cap", fake)
    add_sub(capped)
    capped.commit(
        "Document sub",
        {"docs/guide.md": "# Guide\n\nThe calculator adds and subtracts.\n"},
    )
    result = capped.run_merge("--max-requests", "1")
    assert result.code == 10, result
    assert [body["state"].get("group", "pr") for body in fake.requests] == ["pr"]
    assert {
        reason["message"]
        for reason in result.json["reasons"]
        if reason["kind"] == "unjudged"
    } == {
        "group:docs unjudged: request cap 1 reached",
        "group:src unjudged: request cap 1 reached",
    }
    assert {
        reason["item"]
        for reason in result.json["reasons"]
        if reason["kind"] == "claim_unsupported"
    } == {"c1", "c2"}

    fake.requests.clear()
    state = make_project(tmp_path / "state", fake)
    add_sub(state)
    state.commit(
        "Write the long guide",
        {"docs/guide.md": "# Guide\n\n" + "The calculator adds numbers. " * 900 + "\n"},
    )
    state.edit_config("max_state_tokens = 30000", "max_state_tokens = 5000")
    result = state.run_merge()
    assert result.code == 10, result
    unjudged = {
        reason["scope"]: reason["message"]
        for reason in result.json["reasons"]
        if reason["kind"] == "unjudged"
    }
    assert list(unjudged) == ["group:docs"]
    assert "above the 5000 budget" in unjudged["group:docs"]
    assert sorted(body["state"].get("group", "pr") for body in fake.requests) == [
        "pr",
        "src",
    ]

    fake.requests.clear()
    total = make_project(tmp_path / "total", fake)
    add_sub(total)
    rules = "".join(
        f'\n[[rules]]\nid = "rule-{n}"\ntext = "Rule {n} keeps module {n} documented."\n'
        for n in range(400)
    )
    total.edit(
        ".jev/packs/rules.toml",
        'source = "AGENTS.md"\n',
        'source = "AGENTS.md"\n' + rules,
    )
    result = total.run_merge()
    assert result.code == 10, result
    unjudged = [
        reason for reason in result.json["reasons"] if reason["kind"] == "unjudged"
    ]
    assert [reason["scope"] for reason in unjudged] == ["group:src"]
    assert "a request must stay below 64000" in unjudged[0]["message"]

    fake.requests.clear()
    wide = make_project(tmp_path / "wide", fake)
    lines = [f"value {n}" for n in range(300 * 8)]
    wide.git("checkout", "-q", "main")
    wide.commit("Add the table", {"data/table.txt": "\n".join(lines) + "\n"})
    wide.git("checkout", "-q", "feature")
    wide.git("reset", "-q", "--hard", "main")
    changed = [f"changed {n}" if n % 8 == 0 else line for n, line in enumerate(lines)]
    wide.commit(
        "Update every eighth value", {"data/table.txt": "\n".join(changed) + "\n"}
    )
    result = wide.run_merge()
    assert result.code == 10, result
    reason = next(item for item in result.json["reasons"] if item["kind"] == "unjudged")
    assert reason["scope"] == "group:data"
    assert (
        "300 hunks exceed the citation capacity of 254 hunk IDs plus none"
        in reason["message"]
    )
    assert "data" not in fake.groups_asked()


def test_gate_declarations(project: Project) -> None:
    add_sub(project)
    project.edit(
        ".jev/gates/merge.toml",
        'preconditions = ["check_green", "no_conflict", "no_conflict_markers"]\ncollectors = ["files", "groups", "claims", "facts", "existing_tests"]',
        'preconditions = ["no_conflict"]\ncollectors = ["files", "groups", "claims"]',
    )
    result = project.jev("run", "merge", "--json")
    assert result.code == 0, result
    assert result.json["check"]["status"] == "not required"
    src = next(
        body for body in project.fake.requests if body["state"].get("group") == "src"
    )
    assert src["state"]["facts"] == {} and src["state"]["existing_tests"] == []
    project.edit(
        ".jev/gates/merge.toml",
        'collectors = ["files", "groups", "claims"]',
        'collectors = ["claims"]',
    )
    broken = project.jev("gates", "--check", key=False)
    assert (
        broken.code == 1 and "collectors must include files and groups" in broken.stderr
    )
